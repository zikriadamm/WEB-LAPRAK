"""
form_sanitizer.py
Modul sanitasi dan validasi komprehensif untuk formulir input teks,
berkas unggahan (PDF, DOCX, gambar), ID placeholder, dan pemetaan gambar.
Melindungi sistem dari Path Traversal, XSS, Script Injection, DoS Buffer, dan File Inclusion.
"""

import os
import re
import zipfile
import unicodedata
from werkzeug.utils import secure_filename
from PIL import Image

# Regex untuk membersihkan tag HTML dan karakter kontrol non-cetak
HTML_TAG_RE = re.compile(r'<[^>]*?>', re.IGNORECASE)
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
DANGEROUS_PATTERNS_RE = re.compile(
    r'(javascript:|vbscript:|data:text/html|onload=|onerror=|onclick=|onmouseover=|onfocus=|onblur=|autofocus|<script|<iframe|<object|<embed|<svg|<form|eval\(|expression\()',
    re.IGNORECASE
)

def sanitize_text(val, max_len: int = 150, allow_multiline: bool = False) -> str:
    """
    Membersihkan teks input dari karakter kontrol, tag HTML, dan pola XSS berbahaya,
    serta membatasi panjang karakter maksimal.
    """
    if val is None:
        return ""

    # Konversi ke string dan normalisasi unicode (NFKC)
    text = unicodedata.normalize("NFKC", str(val))

    # Hapus karakter kontrol (null byte, form-feed, escape)
    text = CONTROL_CHAR_RE.sub("", text)

    # Hapus pola dan event handler skrip XSS
    text = DANGEROUS_PATTERNS_RE.sub("", text)

    # Hapus tag HTML
    text = HTML_TAG_RE.sub("", text)

    # Hapus kurung siku/sudut sisa untuk membatalkan tag parsial
    text = text.replace("<", "").replace(">", "")

    # Atur penanganan baris baru
    if not allow_multiline:
        text = re.sub(r'[\r\n\t]+', ' ', text)
    else:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Batasi baris kosong beruntun maksimal 2
        text = re.sub(r'\n{3,}', '\n\n', text)

    # Pangkas whitespace berlebih dan batasi panjang
    text = text.strip()
    return text[:max_len]

def sanitize_alphanumeric(val, max_len: int = 50, allow_chars: str = "-_.") -> str:
    """
    Hanya mengizinkan karakter huruf, angka, dan karakter pembatas yang aman.
    Cocok untuk NIM, ID modul, dan kode identifikasi.
    """
    if val is None:
        return ""
    raw = str(val).strip()
    safe_chars = re.escape(allow_chars)
    pattern = rf'[^a-zA-Z0-9{safe_chars}]'
    cleaned = re.sub(pattern, '', raw)
    return cleaned[:max_len]

def sanitize_placeholder_id(val: str) -> str:
    """
    Membersihkan ID placeholder agar hanya memuat karakter alfanumerik dan garis bawah.
    Mencegah path traversal saat membuat nama berkas gambar screenshot.
    """
    if not val:
        return "placeholder"
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '', str(val))
    return cleaned[:40] or "placeholder"

def sanitize_upload_filename(raw_filename: str, allowed_ext: str = None) -> tuple[str, str]:
    """
    Membersihkan nama berkas yang diunggah pengguna menggunakan secure_filename.
    Memeriksa ekstensi berkas terhadap ekstensi yang diizinkan.
    Mengembalikan (safe_filename, lowercase_ext).
    """
    if not raw_filename:
        return "", ""

    # Dapatkan nama berkas aman
    safe_name = secure_filename(os.path.basename(raw_filename))
    ext = os.path.splitext(safe_name)[1].lower()

    if allowed_ext and ext != allowed_ext.lower():
        return "", ext

    return safe_name, ext

def verify_and_sanitize_image(file_storage, allowed_formats=("PNG", "JPEG", "WEBP")) -> tuple[bool, str]:
    """
    Memverifikasi integritas berkas gambar menggunakan Pillow.
    Mengecek magic bytes dan memastikan berkas bukan skrip yang disamarkan sebagai gambar.
    Mengembalikan (is_valid, error_or_format).
    """
    try:
        # Buka dan verifikasi header gambar asli
        img = Image.open(file_storage)
        img_format = img.format.upper() if img.format else ""
        img.verify()

        if img_format not in allowed_formats:
            return False, f"Format gambar '{img_format}' tidak didukung. Harap unggah format PNG, JPEG, atau WebP."

        # Kembalikan pointer stream ke awal agar siap disimpan ke disk
        if hasattr(file_storage, "seek"):
            file_storage.seek(0)
        return True, img_format.lower()
    except Exception as e:
        return False, f"Berkas gambar rusak atau tidak valid: {str(e)}"

def verify_pdf_safety(file_storage_or_path, max_size_bytes: int = 30 * 1024 * 1024) -> tuple[bool, str]:
    """
    Memverifikasi bahwa berkas adalah PDF yang valid melalui magic bytes (%PDF-).
    Mencegah file executable atau skrip HTML/PHP disamarkan sebagai file PDF.
    Mengembalikan (is_valid, error_or_format).
    """
    try:
        if isinstance(file_storage_or_path, str):
            if not os.path.isfile(file_storage_or_path):
                return False, "Berkas PDF tidak ditemukan pada sistem penyimpanan."
            if os.path.getsize(file_storage_or_path) > max_size_bytes:
                return False, f"Ukuran berkas PDF melebihi batas maksimal {max_size_bytes // (1024 * 1024)} MB."
            with open(file_storage_or_path, "rb") as f:
                header = f.read(1024)
        else:
            pos = file_storage_or_path.tell()
            header = file_storage_or_path.read(1024)
            file_storage_or_path.seek(pos)

        if not header.startswith(b"%PDF-") and b"%PDF-" not in header[:512]:
            return False, "Berkas bukan format PDF yang valid (magic byte %PDF- tidak ditemukan)."

        return True, "valid_pdf"
    except Exception as e:
        return False, f"Gagal memvalidasi berkas PDF: {str(e)}"

def verify_docx_safety(file_storage_or_path, max_uncompressed_bytes: int = 60 * 1024 * 1024, max_ratio: int = 100) -> tuple[bool, str]:
    """
    Memeriksa integritas berkas .docx (OpenXML) terhadap serangan Zip Slip,
    Decompression Bomb (Zip Bomb), serta memvalidasi struktur XML internal.
    Mengembalikan (is_valid, error_or_format).
    """
    try:
        # Jika berupa file storage Flask, gunakan stream langsung
        if hasattr(file_storage_or_path, "stream"):
            target = file_storage_or_path.stream
        else:
            target = file_storage_or_path

        z = zipfile.ZipFile(target)
        names = z.namelist()

        # Validasi struktur OpenXML: harus memuat [Content_Types].xml atau word/document.xml
        has_content_types = "[Content_Types].xml" in names
        has_document_xml = any(name.startswith("word/") for name in names)

        if not (has_content_types or has_document_xml):
            return False, "Berkas bukan dokumen Microsoft Word (.docx) OpenXML yang sah."

        total_uncompressed = 0
        total_compressed = 0

        for info in z.infolist():
            # Cegah Zip Slip (path traversal dalam arsip)
            fname = info.filename
            if fname.startswith(("/", "\\")) or ".." in fname:
                return False, "Berkas terdeteksi memuat struktur berbahaya (Zip Slip attempt)."

            total_uncompressed += info.file_size
            total_compressed += info.compress_size or 1

            # Batas total ukuran dekompresi
            if total_uncompressed > max_uncompressed_bytes:
                return False, f"Ukuran dekompresi dokumen melebihi batas aman ({max_uncompressed_bytes // (1024 * 1024)} MB). Terindikasi Zip Bomb."

        # Cek rasio kompresi berbahaya jika ukuran substansial
        if total_compressed > 0 and (total_uncompressed / total_compressed) > max_ratio and total_uncompressed > 5 * 1024 * 1024:
            return False, "Rasio kompresi arsip tidak wajar. Berkas ditolak untuk keamanan memori server."

        if hasattr(file_storage_or_path, "seek"):
            file_storage_or_path.seek(0)

        return True, "valid_docx"
    except zipfile.BadZipFile:
        return False, "Berkas bukan arsip Word .docx yang valid atau berkas telah rusak."
    except Exception as e:
        return False, f"Verifikasi dokumen Word gagal: {str(e)}"

def is_safe_file_path(target_path: str, base_dir: str) -> bool:
    """
    Memverifikasi secara ketat bahwa target_path berada di dalam base_dir
    untuk mencegah serangan Path Traversal / Arbitrary File Download.
    """
    try:
        canonical_target = os.path.realpath(os.path.abspath(target_path))
        canonical_base = os.path.realpath(os.path.abspath(base_dir))
        return os.path.commonpath([canonical_target, canonical_base]) == canonical_base and os.path.isfile(canonical_target)
    except Exception:
        return False

def sanitize_images_map(images_map: dict, base_images_dir: str) -> dict:
    """
    Memastikan seluruh path berkas gambar pada images_map benar-benar berada
    di dalam direktori upload gambar resmi (IMAGES_DIR) tanpa celah path traversal.
    """
    if not isinstance(images_map, dict):
        return {}

    safe_map = {}
    canonical_base = os.path.realpath(os.path.abspath(base_images_dir))

    for raw_id, raw_path in images_map.items():
        if not raw_id or not isinstance(raw_path, str):
            continue

        safe_id = sanitize_placeholder_id(raw_id)
        
        # Validasi path absolut gambar
        abs_img_path = os.path.realpath(os.path.abspath(raw_path))
        
        # Pastikan path gambar berada di bawah direktori base_images_dir
        if abs_img_path.startswith(canonical_base) and os.path.isfile(abs_img_path):
            safe_map[safe_id] = abs_img_path

    return safe_map

def sanitize_student_info(data: dict) -> dict:
    """
    Menyaring formulir identitas mahasiswa dan mata kuliah.
    """
    data = data or {}
    return {
        "name": sanitize_text(data.get("name", ""), max_len=120) or "MOH. YUSFI LAKHAFIDUN",
        "nim": sanitize_alphanumeric(data.get("nim", ""), max_len=30, allow_chars="-_./") or "F5512520089",
        "class": sanitize_text(data.get("class", ""), max_len=50) or "Informatika C",
        "course": sanitize_text(data.get("course", ""), max_len=100) or "Sistem Informasi Geografis",
        "module_number": sanitize_alphanumeric(data.get("module_number", ""), max_len=10)
    }

def sanitize_book_metadata(data: dict) -> dict:
    """
    Menyaring formulir metadata pembukuan laporan akhir (merge).
    """
    data = data or {}
    return {
        "course_name": sanitize_text(data.get("course_name", "Sistem Informasi Geografis"), max_len=100),
        "title": sanitize_text(data.get("title", ""), max_len=200),
        "student_name": sanitize_text(data.get("student_name", ""), max_len=120),
        "student_nim": sanitize_alphanumeric(data.get("student_nim", ""), max_len=30, allow_chars="-_./"),
        "student_class": sanitize_text(data.get("student_class", ""), max_len=50),
        "institution": sanitize_text(
            data.get("institution", "PROGRAM STUDI S1 TEKNIK INFORMATIKA\nJURUSAN TEKNOLOGI INFORMASI\nFAKULTAS TEKNIK\nUNIVERSITAS TADULAKO"),
            max_len=300,
            allow_multiline=True
        ),
        "academic_year": sanitize_alphanumeric(data.get("academic_year", "2026"), max_len=20, allow_chars="/-"),
        "include_kata_pengantar": str(data.get("include_kata_pengantar", "true")).lower() in ("true", "1", "yes"),
        "include_daftar_isi": str(data.get("include_daftar_isi", "true")).lower() in ("true", "1", "yes")
    }
