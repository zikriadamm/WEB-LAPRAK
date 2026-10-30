"""
auth_service.py
Layanan autentikasi berbasis SQLite, password hashing (scrypt/pbkdf2),
dan signed session token (itsdangerous/HMAC-SHA256) dengan masa kedaluwarsa.
"""

import os
import sqlite3
import hashlib
import hmac
import time
import re
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv

# Muat variabel lingkungan
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Direktori dan path database SQLite
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "auth.db")

# Kunci rahasia untuk menandatangani token
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("ADMIN_SECRET_KEY") or "laprak_default_auth_secret_key_2026"
TOKEN_SERIALIZER = URLSafeTimedSerializer(SECRET_KEY)
TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", 86400))  # 24 jam

# Hash tiruan untuk mencegah serangan timing user-enumeration (konstan ~100ms)
DUMMY_HASH = generate_password_hash("dummy_protection_password_2026", method="scrypt")

COMMON_WEAK_PASSWORDS = {
    "password", "password123", "12345678", "123456789", "1234567890",
    "admin123", "admin2026", "qwertyuiop", "qwerty123", "rahasia123",
    "untad2026", "laprak2026"
}

def hash_password(plain_password: str) -> str:
    """
    Menghasilkan password hash dengan algoritma scrypt memory-hard
    (OWASP recommended standard, N=32768, r=8, p=1, salt 16 bytes).
    """
    if not plain_password:
        raise ValueError("Password tidak boleh kosong.")
    # Batasi panjang maksimal 128 karakter untuk mencegah serangan Hash-DoS
    trimmed = str(plain_password)[:128]
    return generate_password_hash(trimmed, method="scrypt")

def verify_password(stored_hash: str, plain_password: str) -> bool:
    """
    Memverifikasi kecocokan kata sandi dengan hash tersimpan secara timing-safe.
    """
    if not stored_hash or not plain_password or len(plain_password) > 128:
        return False
    return check_password_hash(stored_hash, plain_password)

def validate_password_strength(password: str, username: str = "") -> tuple[bool, str]:
    """
    Memvalidasi kekuatan dan kebijakan keamanan kata sandi baru:
    - Panjang 8 - 128 karakter
    - Mengombinasikan huruf besar, huruf kecil, dan angka
    - Tidak memuat username
    - Bukan kata sandi umum yang mudah ditebak
    """
    if not password or len(password) < 8:
        return False, "Kata sandi baru minimal harus 8 karakter."
    if len(password) > 128:
        return False, "Kata sandi tidak boleh melebihi 128 karakter."
    if not re.search(r'[a-z]', password) or not re.search(r'[A-Z]', password):
        return False, "Kata sandi baru harus memuat kombinasi huruf besar dan huruf kecil."
    if not re.search(r'[0-9]', password):
        return False, "Kata sandi baru harus memuat setidaknya satu angka."
    if username and username.lower() in password.lower():
        return False, "Kata sandi tidak boleh memuat nama pengguna (username)."
    if password.lower() in COMMON_WEAK_PASSWORDS:
        return False, "Kata sandi terlalu umum atau mudah ditebak. Harap gunakan kata sandi yang lebih unik."
    return True, "valid"

def get_db_connection():
    """
    Membuka koneksi aman ke database SQLite dengan konfigurasi PRAGMA:
    - WAL Mode (Write-Ahead Logging untuk konkurensi tinggi & anti-korupsi)
    - secure_delete = ON (menghapus data secara permanen dengan overwrite nol di disk)
    - trusted_schema = OFF (mencegah eksploitasi skema berbahaya / view injection)
    - foreign_keys = ON (menjamin integritas referensial data)
    - timeout = 10.0 (mencegah kegagalan lock pada konkurensi tinggi)
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row

    # Konfigurasi keamanan dan stabilitas SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA trusted_schema = OFF;")
    conn.execute("PRAGMA secure_delete = ON;")
    return conn

def init_auth_db():
    """Inisialisasi tabel pengguna dan token blacklist jika belum ada, dengan pengamanan izin berkas."""
    # Batasi hak akses direktori & berkas database di level OS (chmod 700 / 600)
    try:
        os.chmod(DATA_DIR, 0o700)
        if os.path.exists(DB_PATH):
            os.chmod(DB_PATH, 0o600)
    except Exception:
        pass

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Audit integritas basis data
        integrity = cursor.execute("PRAGMA integrity_check;").fetchone()
        if integrity and integrity[0] != "ok":
            print(f"[Database Warning] Pemeriksaan integritas DB: {integrity[0]}")
        
        # Tabel Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Tabel Token Blacklist (untuk proses logout instan)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                token_hash TEXT PRIMARY KEY,
                revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indeks untuk mempercepat pencarian username dan token revoked
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_revoked_tokens_hash ON revoked_tokens(token_hash);")

        # Pembersihan otomatis token kadaluarsa yang lebih tua dari 7 hari
        cursor.execute("DELETE FROM revoked_tokens WHERE datetime(revoked_at) < datetime('now', '-7 days')")

        conn.commit()

        # Seed admin otomatis jika belum ada akun admin
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin_exists = cursor.fetchone()

        if not admin_exists:
            admin_user = os.environ.get("ADMIN_USERNAME", "admin").strip()
            admin_pass = os.environ.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_SECRET_KEY") or "admin_laprak_2026_secret"
            
            pwd_hash = hash_password(admin_pass)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (admin_user, pwd_hash, "admin")
            )
            conn.commit()
            print(f"[Auth] Akun admin default berhasil diinisialisasi (username: '{admin_user}').")

def optimize_database():
    """Menjalankan pembersihan berkas token kedaluwarsa dan pemadatan ruang database."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM revoked_tokens WHERE datetime(revoked_at) < datetime('now', '-7 days')")
        conn.execute("PRAGMA incremental_vacuum;")
        conn.commit()

def backup_database(backup_dir: str = None) -> str:
    """
    Membuat snapshot cadangan database SQLite secara aman (hot backup tanpa downtime).
    Mengembalikan path berkas backup.
    """
    target_dir = backup_dir or DATA_DIR
    os.makedirs(target_dir, exist_ok=True)
    backup_file = os.path.join(target_dir, f"auth_backup_{int(time.time())}.db")
    src_conn = get_db_connection()
    dst_conn = sqlite3.connect(backup_file)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    try:
        os.chmod(backup_file, 0o600)
    except Exception:
        pass
    return backup_file

def hash_token(token: str) -> str:
    """Menghasilkan sha256 hash dari token untuk penyimpanan blacklist yang efisien."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def is_token_revoked(token: str) -> bool:
    """Memeriksa apakah token telah dicabut (logout)."""
    t_hash = hash_token(token)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM revoked_tokens WHERE token_hash = ?", (t_hash,))
        return cursor.fetchone() is not None

def revoke_token(token: str):
    """Menambahkan token ke tabel blacklist."""
    t_hash = hash_token(token)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO revoked_tokens (token_hash) VALUES (?)",
            (t_hash,)
        )
        conn.commit()

def generate_auth_token(user: dict) -> str:
    """Membuat token bertanda tangan kriptografis berisi identitas pengguna dan role."""
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": int(time.time())
    }
    return TOKEN_SERIALIZER.dumps(payload)

def verify_auth_token(token: str) -> dict:
    """
    Memverifikasi keabsahan tanda tangan token dan masa kedaluwarsa.
    Mengembalikan dict user jika valid, atau None jika tidak valid/kedaluwarsa/dicabut.
    """
    if not token or is_token_revoked(token):
        return None

    try:
        payload = TOKEN_SERIALIZER.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return payload
    except (SignatureExpired, BadSignature):
        return None

def authenticate_user(username: str, password: str) -> dict:
    """
    Memverifikasi username dan password pengguna secara timing-safe.
    Dilengkapi mitigasi anti User-Enumeration Timing Attack dan proteksi Hash-DoS buffer.
    """
    if not username or not password or len(password) > 128:
        # Jika panjang password melebihi batas wajar, tolak seketika untuk mencegah Hash-DoS
        return None

    clean_user = username.strip()[:80]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (clean_user,))
        user_row = cursor.fetchone()

        if not user_row:
            # Timing-attack mitigation: Jalankan hash dummy dengan durasi setara scrypt (~100ms)
            # agar penyerang tidak bisa mendeteksi apakah username ada atau tidak dari latency respons
            check_password_hash(DUMMY_HASH, password[:128])
            return None

        if not verify_password(user_row["password_hash"], password):
            return None

        # Perbarui waktu login terakhir
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_row["id"],)
        )
        conn.commit()

        return {
            "id": user_row["id"],
            "username": user_row["username"],
            "role": user_row["role"],
            "created_at": user_row["created_at"],
            "last_login": user_row["last_login"]
        }

def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Mengubah kata sandi pengguna terdaftar dengan validasi kompleksitas OWASP,
    pengecekan kata sandi lama, pencegahan password mirip username, dan hashing scrypt.
    """
    is_strong, msg = validate_password_strength(new_password)
    if not is_strong:
        return False, msg

    if old_password == new_password:
        return False, "Kata sandi baru tidak boleh sama dengan kata sandi saat ini."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            return False, "Pengguna tidak ditemukan."

        if not verify_password(row["password_hash"], old_password):
            return False, "Kata sandi lama salah."

        # Cek username tidak ada dalam password
        is_strong_user, user_msg = validate_password_strength(new_password, username=row["username"])
        if not is_strong_user:
            return False, user_msg

        new_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id)
        )
        conn.commit()
        return True, "Kata sandi berhasil diperbarui."

def extract_bearer_token(req) -> str:
    """Mengekstrak token dari header Authorization (Bearer <token>) atau X-Auth-Token."""
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return req.headers.get("X-Auth-Token", "").strip()

def require_auth(role: str = None):
    """
    Decorator proteksi endpoint dengan autentikasi Token Bearer.
    Opsional: role='admin' untuk memastikan hanya role admin yang diizinkan.
    Dilengkapi perlindungan anti timing-attack untuk validasi legacy key.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = extract_bearer_token(request)
            
            # Fallback backward-compatible: jika menggunakan legacy X-Admin-Key yang cocok dengan ADMIN_SECRET_KEY
            legacy_key = request.headers.get("X-Admin-Key")
            expected_secret = os.environ.get("ADMIN_SECRET_KEY")
            if legacy_key and expected_secret and role == "admin":
                if hmac.compare_digest(str(legacy_key).strip(), str(expected_secret).strip()):
                    request.current_user = {"id": 1, "username": "admin", "role": "admin"}
                    return f(*args, **kwargs)

            if not token:
                return jsonify({"error": "Autentikasi diperlukan: Token Bearer tidak disertakan."}), 401

            payload = verify_auth_token(token)
            if not payload:
                return jsonify({"error": "Sesi tidak valid atau telah kedaluwarsa. Silakan login kembali."}), 401

            if role and payload.get("role") != role:
                return jsonify({"error": f"Akses Ditolak: Memerlukan hak akses role '{role}'."}), 403

            request.current_user = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator
