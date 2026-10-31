"""
app.py
Server REST API Flask untuk Web Laprak Generator.
Menyediakan endpoint ekstraksi PDF berbasis Gemini AI & Groq LPU serta pembuatan berkas Word (.docx).
Dilengkapi rate limiter kuota, auto-cleanup berkas temporer, dan konfigurasi produksi Railway/Render.
"""

import os
import sys
import uuid
import time
import hmac
from functools import wraps
from collections import defaultdict
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Muat variabel lingkungan dari .env
load_dotenv()

# Tambahkan direktori backend ke sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.pdf_service import extract_text_from_pdf
from services.gemini_service import extract_report_from_pdf_content
from services.groq_service import extract_report_with_groq
from services.cache_service import get_cached_report, save_cached_report, get_cache_stats, clear_all_cache
from services.docx_service import generate_docx_report, IMAGES_DIR, UPLOAD_DIR
from core.book_compiler import compile_master_book, parse_module_docx
from services.auth_service import (
    init_auth_db, authenticate_user, generate_auth_token, verify_auth_token,
    revoke_token, change_password, require_auth, extract_bearer_token,
    optimize_database
)
from core.form_sanitizer import (
    sanitize_text, sanitize_alphanumeric, sanitize_placeholder_id,
    sanitize_upload_filename, verify_and_sanitize_image,
    sanitize_images_map, sanitize_student_info, sanitize_book_metadata,
    verify_pdf_safety, verify_docx_safety, is_safe_file_path
)
from core.rate_limiter import RATE_LIMITER, rate_limit, get_real_ip

app = Flask(__name__)

# Mode Debug dinonaktifkan secara ketat (anti-RCE & pencegahan kebocoran Werkzeug PIN console)
app.debug = False
app.config["DEBUG"] = False
app.config["TESTING"] = False
app.config["ENV"] = "production"

# Mask banner server bawaan Werkzeug agar tidak membocorkan versi Python/OS
try:
    import werkzeug.serving
    werkzeug.serving.WSGIRequestHandler.server_version = "WebLaprak"
    werkzeug.serving.WSGIRequestHandler.sys_version = ""
except Exception:
    pass

# Inisialisasi basis data kredensial & tabel pengguna
init_auth_db()

# Batas maksimal ukuran payload (30 MB) untuk mencegah DoS / kehabisan RAM
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

# Konfigurasi CORS produksi untuk Vercel, Cloudflare, dan domain publik
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "*").strip()
if allowed_origins_raw == "*":
    cors_origins = "*"
else:
    cors_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Gemini-Key", "X-Admin-Key", "X-Auth-Token"],
        "expose_headers": ["RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset", "Retry-After", "Content-Disposition"],
        "max_age": 86400
    }
})

PDF_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "pdf")
os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

# Konfigurasi Kebijakan Rate Limiting (dapat diatur lewat variabel lingkungan .env)
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", 5))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", 600))  # 10 menit

# Alias backward-compatible
get_client_ip = get_real_ip

# Alias decorator untuk proteksi rute admin berbasis Token Bearer & role
require_admin = require_auth(role="admin")

@app.before_request
def global_dos_protection():
    """Perlindungan Global Anti-DoS: Maks 120 request per menit per IP untuk seluruh API."""
    if request.method == "OPTIONS":
        return None

    client_ip = get_real_ip()
    allowed, remaining, reset_sec = RATE_LIMITER.check("global_api", client_ip, max_requests=120, window_seconds=60)
    if not allowed:
        return jsonify({
            "error": f"Batas laju permintaan global terlampaui (120 req/menit). Silakan tunggu {reset_sec} detik.",
            "retry_after_seconds": reset_sec
        }), 429, {
            "Retry-After": str(reset_sec),
            "RateLimit-Limit": "120",
            "RateLimit-Remaining": "0",
            "RateLimit-Reset": str(reset_sec)
        }

def cleanup_temp_files(max_age_seconds: int = 3600):
    """Membersihkan berkas-berkas upload dan hasil unduh yang lebih tua dari 1 jam."""
    now = time.time()
    dirs_to_clean = [
        PDF_UPLOAD_DIR,
        IMAGES_DIR,
        os.path.join(UPLOAD_DIR, "generated_docs"),
        os.path.join(UPLOAD_DIR, "inspect_temp"),
    ]
    for d in dirs_to_clean:
        if not os.path.exists(d):
            continue
        try:
            for item in os.listdir(d):
                p = os.path.join(d, item)
                if os.path.isfile(p) and (now - os.path.getmtime(p) > max_age_seconds):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
        except Exception:
            pass

def sanitize_error(msg) -> str:
    """Membersihkan pesan error dari kemungkinan bocornya API key atau rahasia token."""
    import re
    cleaned = str(msg)
    cleaned = re.sub(r'(AIza[0-9A-Za-z-_]{30,}|AQ\.[0-9A-Za-z-_]{30,})', '[PROTECTED_KEY]', cleaned)
    cleaned = re.sub(r'gsk_[0-9A-Za-z]{20,}', '[PROTECTED_KEY]', cleaned)
    return cleaned

# ==========================================
# PENANGANAN ERROR JSON STANDAR (ANTI-LEAK)
# ==========================================

@app.errorhandler(400)
def handle_400(error):
    return jsonify({"error": "Permintaan tidak valid (Bad Request). Format payload tidak sesuai."}), 400

@app.errorhandler(404)
def handle_404(error):
    relevant_env = {
        k: str(v) for k, v in request.environ.items()
        if any(w in k.upper() for w in ['PATH', 'URI', 'URL', 'MATCH', 'VERCEL', 'ROUTE', 'ORIGINAL'])
    }
    return jsonify({
        "error": "Endpoint API tidak ditemukan (404 Not Found).",
        "path": request.path,
        "env_matches": relevant_env
    }), 404

@app.errorhandler(405)
def handle_405(error):
    return jsonify({"error": f"Metode HTTP '{request.method}' tidak diizinkan pada rute ini (405 Method Not Allowed)."}), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Ukuran berkas melebihi batas maksimal yang diizinkan (30 MB)."}), 413

@app.errorhandler(415)
def handle_415(error):
    return jsonify({"error": "Format media tidak didukung. Header Content-Type harus berupa application/json atau multipart/form-data."}), 415

@app.errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Terjadi kesalahan internal pada server (500 Internal Server Error)."}), 500

@app.after_request
def add_security_headers(response):
    """
    Menyematkan HTTP Security Headers standar industri (OWASP Secure Headers Project)
    untuk proteksi terhadap XSS, MIME-sniffing, clickjacking, pembatasan permissions,
    isolasi origin, anti-caching data kredensial, dan server fingerprinting.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
        "fullscreen=(self), display-capture=()"
    )
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["X-Download-Options"] = "noopen"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    response.headers["Origin-Agent-Cluster"] = "?1"

    # Anti-Caching pada respons API dinamis dan kredensial autentikasi
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

    # HSTS aktif jika berjalan di protokol HTTPS (produksi Vercel/Railway/Render)
    if request.is_secure or request.headers.get("X-Forwarded-Proto", "").lower() == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https: http://127.0.0.1:* http://localhost:*; "
        "frame-ancestors 'self' https://huggingface.co https://*.hf.space; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    # Hapus duplikasi header Server agar hanya memuat WebLaprak bersih
    response.headers.pop("Server", None)
    return response

@app.route("/", methods=["GET"])
def index():
    """Halaman pembuka API backend untuk pengecekan status awal di cloud."""
    return jsonify({
        "status": "online",
        "service": "Web Laprak Generator API",
        "engine": "Flask + Gunicorn + Multi-Model AI",
        "health": "/api/health"
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """Pengecekan status server backend sekaligus pembersihan berkas temporer kadaluarsa."""
    cleanup_temp_files()
    return jsonify({
        "status": "ok",
        "service": "Web Laprak Generator API",
        "has_env_key": bool(os.environ.get("GEMINI_API_KEY")),
        "has_groq_key": bool(os.environ.get("GROQ_API_KEY")),
        "cache_enabled": True
    })

# ==========================================
# ENDPOINT AUTENTIKASI (PROPER AUTHENTICATION)
# ==========================================

auth_failed_logins = defaultdict(list)

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """
    Endpoint login pengguna & admin.
    Menerima JSON { username, password } dan mengembalikan Token Bearer bertanda tangan kriptografis.
    Dilengkapi perlindungan anti brute-force IP (maks 5x gagal per 15 menit).
    """
    client_ip = get_client_ip()
    now = time.time()
    recent_fails = [t for t in auth_failed_logins[client_ip] if now - t < 900]
    auth_failed_logins[client_ip] = recent_fails
    if len(recent_fails) >= 5:
        return jsonify({
            "error": "Terlalu banyak percobaan login yang gagal (maks 5x). IP Anda diblokir sementara selama 15 menit."
        }), 429

    if not request.is_json:
        return jsonify({"error": "Content-Type permintaan harus berupa application/json."}), 415

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"error": "Username dan kata sandi wajib diisi."}), 400

    if len(password) > 128:
        return jsonify({"error": "Kata sandi melebihi batas panjang maksimal (128 karakter)."}), 400

    user = authenticate_user(username, password)
    if not user:
        auth_failed_logins[client_ip].append(now)
        return jsonify({"error": "Username atau kata sandi salah."}), 401

    # Reset counter gagal login jika berhasil
    auth_failed_logins.pop(client_ip, None)

    # Buat token bertanda tangan kriptografis (24 jam)
    token = generate_auth_token(user)

    return jsonify({
        "status": "success",
        "message": f"Selamat datang kembali, {user['username']}!",
        "token": token,
        "user": user
    })

@app.route("/api/auth/logout", methods=["POST"])
@require_auth()
def auth_logout():
    """Mencabut token sesi pengguna saat ini (instant blacklist)."""
    token = extract_bearer_token(request)
    if token:
        revoke_token(token)
    return jsonify({
        "status": "success",
        "message": "Anda telah berhasil logout."
    })

@app.route("/api/auth/me", methods=["GET"])
@require_auth()
def auth_me():
    """Mengembalikan profil dan status hak akses pengguna yang sedang aktif."""
    return jsonify({
        "status": "ok",
        "user": request.current_user
    })

@app.route("/api/auth/change-password", methods=["POST"])
@require_auth()
def auth_change_password():
    """Mengubah kata sandi pengguna yang sedang login."""
    data = request.get_json(silent=True) or {}
    old_password = str(data.get("old_password", ""))
    new_password = str(data.get("new_password", ""))

    if not old_password or not new_password:
        return jsonify({"error": "Kata sandi lama dan baru wajib diisi."}), 400

    user_id = request.current_user.get("user_id") or request.current_user.get("id")
    success, msg = change_password(user_id, old_password, new_password)
    if not success:
        return jsonify({"error": msg}), 400

    return jsonify({
        "status": "success",
        "message": msg
    })

@app.route("/api/extract", methods=["POST"])
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    bucket="extract_ai",
    exempt_func=lambda: bool(request.form.get("api_key") or request.headers.get("X-Gemini-Key"))
)
def extract_pdf():
    """
    Menerima berkas PDF modul asdos dan mengembalikan draf laporan terstruktur JSON via Gemini AI / Groq.
    """
    if "file" not in request.files:
        return jsonify({"error": "Berkas PDF modul asdos tidak ditemukan pada formulir upload."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Nama berkas PDF kosong."}), 400

    # Verifikasi keabsahan format PDF asli via magic bytes %PDF-
    is_valid_pdf, pdf_err = verify_pdf_safety(file)
    if not is_valid_pdf:
        return jsonify({"error": pdf_err}), 400

    # Simpan file PDF ke direktori upload sementara setelah sanitasi nama berkas
    safe_name, ext = sanitize_upload_filename(file.filename, allowed_ext=".pdf")
    if not safe_name or ext != ".pdf":
        return jsonify({"error": "Berkas yang diunggah harus berformat PDF (.pdf) dengan nama yang valid."}), 400

    temp_filename = f"{uuid.uuid4().hex[:10]}_{safe_name}"
    temp_pdf_path = os.path.join(PDF_UPLOAD_DIR, temp_filename)
    file.save(temp_pdf_path)

    try:
        # 1. Ambil data mahasiswa dan API key dari form (tersanitasi)
        raw_key = request.form.get("api_key") or request.headers.get("X-Gemini-Key")
        api_key = sanitize_text(raw_key, max_len=100) if raw_key else None

        student_info = sanitize_student_info(request.form)

        # 2. Ekstrak teks dari PDF (otomatis fallback OCR AI Gemini jika PDF berupa scan gambar)
        pdf_res = extract_text_from_pdf(temp_pdf_path, api_key=api_key)
        full_text = pdf_res.get("full_text", "")
        if not full_text.strip():
            return jsonify({
                "error": "Tidak ada teks yang berhasil dibaca dari berkas PDF ini bahkan setelah mencoba OCR AI. Pastikan berkas PDF dapat dibuka dan tidak rusak."
            }), 400

        # Cek Cache Terlebih Dahulu (Quick Win: Instan < 50ms)
        cached_data = get_cached_report(file_path=temp_pdf_path, student_info=student_info)
        if cached_data:
            return jsonify({
                "status": "success",
                "source": "cache",
                "message": "Draf laporan dimuat instan dari cache lokal (tanpa kuota AI).",
                "data": cached_data
            })

        # 3. Panggil Gemini AI (Primary) dengan Auto-Fallback ke Groq AI (Secondary)
        report_data = None
        source_engine = "gemini"
        try:
            report_data = extract_report_from_pdf_content(
                pdf_text=full_text,
                student_info=student_info,
                api_key=api_key
            )
        except Exception as gemini_err:
            app.logger.warning(f"[AI Failover] Gemini gagal ({gemini_err}), mencoba Groq LPU...")
            try:
                report_data = extract_report_with_groq(
                    pdf_text=full_text,
                    student_info=student_info
                )
                source_engine = "groq"
            except Exception as groq_err:
                raise RuntimeError(f"Semua provider AI sibuk / tidak merespons. Gemini: {gemini_err} | Groq: {groq_err}")

        # Simpan ke cache lokal untuk percepatan upload berikutnya
        if report_data:
            save_cached_report(report_data, file_path=temp_pdf_path)

        return jsonify({
            "status": "success",
            "source": source_engine,
            "message": f"Ekstraksi modul praktikum berhasil via {source_engine.upper()}.",
            "data": report_data
        })

    except Exception as e:
        app.logger.error(f"Error saat mengekstrak PDF: {sanitize_error(e)}")
        return jsonify({"error": sanitize_error(e)}), 500
    finally:
        # Hapus file PDF sementara jika perlu
        if os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception:
                pass

@app.route("/api/upload-image", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=300, bucket="upload_image")
def upload_image():
    """
    Menerima unggahan screenshot praktikum mahasiswa untuk disisipkan ke placeholder langkah kerja.
    """
    if "image" not in request.files:
        return jsonify({"error": "Berkas gambar tidak ditemukan."}), 400

    img = request.files["image"]
    
    # 1. Verifikasi integritas gambar menggunakan Pillow (anti file palsu / skrip)
    is_valid_img, img_format_or_err = verify_and_sanitize_image(img)
    if not is_valid_img:
        return jsonify({"error": img_format_or_err}), 400

    safe_name, ext = sanitize_upload_filename(img.filename)
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        return jsonify({"error": "Format gambar harus berupa PNG, JPG, JPEG, atau WebP."}), 400

    # 2. Sanitasi ID placeholder untuk mencegah path traversal
    safe_placeholder = sanitize_placeholder_id(request.form.get("placeholder_id"))
    saved_filename = f"{uuid.uuid4().hex[:10]}_{safe_placeholder}{ext}"
    saved_path = os.path.join(IMAGES_DIR, saved_filename)
    img.save(saved_path)

    return jsonify({
        "status": "success",
        "placeholder_id": safe_placeholder,
        "filename": saved_filename,
        "image_path": saved_path
    })

@app.route("/api/generate", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=300, bucket="generate_docx")
def generate_docx():
    """
    Menerima payload JSON laporan hasil penyuntingan pengguna dan mengembalikan file .docx siap unduh.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type permintaan harus berupa application/json."}), 415

    data = request.get_json(silent=True)
    if not data or "report_data" not in data:
        return jsonify({"error": "Data laporan ('report_data') tidak ditemukan pada permintaan."}), 400

    report_data = data["report_data"]
    if not isinstance(report_data, dict):
        return jsonify({"error": "Struktur 'report_data' harus berupa objek JSON yang valid."}), 400

    # Sanitasi images_map agar tidak bisa mengarah ke file di luar direktori upload
    raw_images_map = data.get("images_map", {})
    images_map = sanitize_images_map(raw_images_map, IMAGES_DIR)

    try:
        output_path = generate_docx_report(report_data, images_map=images_map)
        if not is_safe_file_path(output_path, UPLOAD_DIR):
            return jsonify({"error": "Akses berkas dokumen ditolak karena di luar direktori yang diizinkan."}), 403

        # Bersihkan nama download agar ramah pengguna (misal f5512520089_prak_gis_8.docx)
        mod_num = report_data.get("module_number", 1)
        nim = report_data.get("student_nim", "f5512520089").lower()
        clean_download_name = f"{nim}_prak_gis_{mod_num}.docx"

        return send_file(
            output_path,
            as_attachment=True,
            download_name=clean_download_name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        app.logger.error(f"Error saat membuat file .docx: {sanitize_error(e)}")
        return jsonify({"error": f"Gagal membuat dokumen Word: {sanitize_error(e)}"}), 500

@app.route("/api/inspect-module-docx", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=300, bucket="inspect_docx")
def inspect_module_docx():
    """
    Menganalisis berkas .docx modul yang diunggah dan mengembalikan ringkasan metadata
    seperti nomor modul, judul, dan jumlah paragraf per bab untuk pratinjau di UI pembukuan.
    """
    if "file" not in request.files:
        return jsonify({"error": "Berkas .docx tidak ditemukan."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Nama berkas .docx kosong."}), 400

    # Verifikasi OpenXML, anti Zip Slip, anti Zip Bomb
    is_valid_docx, docx_err = verify_docx_safety(file)
    if not is_valid_docx:
        return jsonify({"error": docx_err}), 400

    safe_name, ext = sanitize_upload_filename(file.filename, allowed_ext=".docx")
    if not safe_name or ext != ".docx":
        return jsonify({"error": "Berkas harus berformat Word (.docx) dengan nama yang valid."}), 400

    temp_id = uuid.uuid4().hex[:8]
    temp_dir = os.path.join(UPLOAD_DIR, "inspect_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{temp_id}_{safe_name}")
    file.save(temp_path)

    try:
        data = parse_module_docx(temp_path)
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "module_number": data.get("module_number"),
            "module_title": data.get("module_title"),
            "student_name": data.get("student_name"),
            "student_nim": data.get("student_nim"),
            "student_class": data.get("student_class"),
            "bab2_count": len(data.get("bab2_paragraphs", [])),
            "bab3_count": len(data.get("bab3_paragraphs", [])),
            "bab4_count": len(data.get("bab4_paragraphs", [])),
            "bab5_count": len(data.get("bab5_paragraphs", [])),
            "bib_count": len(data.get("daftar_pustaka_entries", []))
        })
    except Exception as e:
        app.logger.error(f"Error inspect docx: {sanitize_error(e)}")
        return jsonify({"error": f"Gagal membedah modul docx: {sanitize_error(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

@app.route("/api/compile-book", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=300, bucket="compile_book")
def compile_book():
    """
    Menerima beberapa berkas .docx modul praktikum dan menyatukannya menjadi
    1 dokumen pembukuan laporan terpadu Model 1 (sesuai format.md).
    """
    uploaded_files = request.files.getlist("files")
    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({"error": "Tidak ada berkas modul .docx yang diunggah untuk pembukuan."}), 400

    batch_id = uuid.uuid4().hex[:8]
    batch_dir = os.path.join(UPLOAD_DIR, f"compile_{batch_id}")
    os.makedirs(batch_dir, exist_ok=True)

    saved_paths = []
    try:
        for f in uploaded_files:
            if not f or f.filename == "":
                continue

            # Verifikasi keabsahan OpenXML dokumen Word dan anti Zip Bomb/Slip
            is_valid_docx, docx_err = verify_docx_safety(f)
            if not is_valid_docx:
                return jsonify({"error": f"Berkas '{f.filename}' tidak valid: {docx_err}"}), 400

            safe_name, ext = sanitize_upload_filename(f.filename, allowed_ext=".docx")
            if safe_name and ext == ".docx":
                p = os.path.join(batch_dir, f"{len(saved_paths)}_{safe_name}")
                f.save(p)
                saved_paths.append(p)

        if not saved_paths:
            return jsonify({"error": "Seluruh berkas yang diunggah harus berformat .docx dengan nama yang valid."}), 400

        metadata = sanitize_book_metadata(request.form)

        import json
        modules_meta_raw = request.form.get("modules_metadata")
        modules_metadata = []
        if modules_meta_raw:
            try:
                modules_metadata = json.loads(modules_meta_raw)
            except Exception as e:
                app.logger.warning(f"Error parsing modules_metadata: {e}")

        output_path = compile_master_book(saved_paths, metadata=metadata, modules_metadata=modules_metadata)
        if not is_safe_file_path(output_path, UPLOAD_DIR):
            return jsonify({"error": "Akses berkas pembukuan ditolak karena di luar direktori aman."}), 403

        nim = metadata.get("student_nim") or "laprak"
        course_clean = metadata.get("course_name", "prak").lower().replace(" ", "_")
        download_name = f"pembukuan_{nim}_{course_clean}.docx"

        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        app.logger.error(f"Error compiling book: {sanitize_error(e)}")
        return jsonify({"error": f"Gagal menyatukan pembukuan: {sanitize_error(e)}"}), 500
    finally:
        # Bersihkan folder batch sementara
        import shutil
        if os.path.exists(batch_dir):
            try:
                shutil.rmtree(batch_dir)
            except Exception:
                pass

# ==========================================
# RUTE ADMIN TERPROTEKSI (MEMERLUKAN KUNCI ADMIN)
# ==========================================

@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    """Mengambil metrik server, kuota AI, disk, dan statistik cache."""
    cache_stats = get_cache_stats()
    
    # Ringkasan IP aktif di seluruh kategori rate limiting
    active_summary = RATE_LIMITER.get_active_summary(window_seconds=RATE_LIMIT_WINDOW_SECONDS)

    # Hitung total file upload sementara
    total_uploads = 0
    uploads_bytes = 0
    for root, _, files in os.walk(UPLOAD_DIR):
        for f in files:
            p = os.path.join(root, f)
            try:
                total_uploads += 1
                uploads_bytes += os.path.getsize(p)
            except Exception:
                pass

    return jsonify({
        "status": "ok",
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "has_groq_key": bool(os.environ.get("GROQ_API_KEY")),
        "cache": cache_stats,
        "rate_limited_active_summary": active_summary,
        "uploads": {
            "file_count": total_uploads,
            "size_kb": round(uploads_bytes / 1024, 2)
        },
        "rate_limit_policy": {
            "max_requests": RATE_LIMIT_MAX_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "tiers": {
                "extract_ai": f"{RATE_LIMIT_MAX_REQUESTS} req / {RATE_LIMIT_WINDOW_SECONDS // 60} menit",
                "generate_docx": "20 req / 5 menit",
                "compile_book": "10 req / 5 menit",
                "upload_image": "30 req / 5 menit",
                "inspect_docx": "20 req / 5 menit",
                "global_dos": "120 req / 1 menit"
            }
        }
    })

@app.route("/api/admin/clear-cache", methods=["POST"])
@require_admin
def admin_clear_cache():
    """Menghapus semua berkas cache modul yang tersimpan di disk."""
    cleared = clear_all_cache()
    return jsonify({
        "status": "success",
        "message": f"Berhasil menghapus {cleared} berkas cache.",
        "cleared_count": cleared
    })

@app.route("/api/admin/reset-limits", methods=["POST"])
@require_admin
def admin_reset_limits():
    """Mereset riwayat rate limiting untuk semua IP klien."""
    total_reset = RATE_LIMITER.reset_all()
    auth_failed_logins.clear()
    return jsonify({
        "status": "success",
        "message": f"Berhasil mereset seluruh batasan laju permintaan ({total_reset} entri IP).",
        "reset_count": total_reset
    })

@app.route("/api/admin/cleanup-disk", methods=["POST"])
@require_admin
def admin_cleanup_disk():
    """Memaksa pembersihan instan seluruh berkas upload sementara dan optimasi basis data."""
    cleanup_temp_files(max_age_seconds=0)
    try:
        optimize_database()
    except Exception as e:
        app.logger.warning(f"Error saat optimasi DB: {e}")
    return jsonify({
        "status": "success",
        "message": "Seluruh berkas upload temporer berhasil dibersihkan dan basis data dioptimasi."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Web Laprak API Server on http://127.0.0.1:{port} (Debug: False, Production Mode)")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
