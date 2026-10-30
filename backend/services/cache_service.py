"""
cache_service.py
Layanan caching draf laporan akademik berdasarkan SHA256 dari berkas PDF modul asdos.
Memungkinkan ekstraksi instan (< 50ms) dan anti 503 jika berkas modul yang sama diproses ulang.
"""

import os
import json
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def compute_pdf_hash(file_path: str = None, file_bytes: bytes = None) -> str:
    """Menghitung sha256 hash dari berkas PDF."""
    hasher = hashlib.sha256()
    if file_bytes:
        hasher.update(file_bytes)
    elif file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    else:
        return ""
    return hasher.hexdigest()

def get_cached_report(file_path: str = None, file_bytes: bytes = None, student_info: dict = None) -> dict:
    """Mengambil draf laporan dari cache jika hash berkas PDF cocok."""
    pdf_hash = compute_pdf_hash(file_path=file_path, file_bytes=file_bytes)
    if not pdf_hash:
        return None

    cache_file = os.path.join(CACHE_DIR, f"{pdf_hash}.json")
    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Inject identitas mahasiswa terbaru jika ada
        if student_info:
            if student_info.get("name"):
                data["student_name"] = student_info["name"]
            if student_info.get("nim"):
                data["student_nim"] = student_info["nim"]
            if student_info.get("class"):
                data["student_class"] = student_info["class"]
            if student_info.get("module_number"):
                try:
                    data["module_number"] = int(student_info["module_number"])
                except ValueError:
                    data["module_number"] = student_info["module_number"]
        
        print(f"[Cache] HIT untuk berkas PDF hash {pdf_hash[:12]}... (Instan tanpa panggil AI)")
        return data
    except Exception as e:
        print(f"[Cache] Gagal membaca cache: {e}")
        return None

def save_cached_report(report_data: dict, file_path: str = None, file_bytes: bytes = None):
    """Menyimpan hasil draf laporan yang sukses ke disk cache."""
    pdf_hash = compute_pdf_hash(file_path=file_path, file_bytes=file_bytes)
    if not pdf_hash or not report_data:
        return

    cache_file = os.path.join(CACHE_DIR, f"{pdf_hash}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"[Cache] Sukses menyimpan cache untuk hash {pdf_hash[:12]}...")
    except Exception as e:
        print(f"[Cache] Gagal menyimpan cache: {e}")

def get_cache_stats() -> dict:
    """Mengembalikan statistik jumlah dan total ukuran berkas cache."""
    count = 0
    total_bytes = 0
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".json"):
                p = os.path.join(CACHE_DIR, f)
                try:
                    count += 1
                    total_bytes += os.path.getsize(p)
                except Exception:
                    pass
    return {
        "count": count,
        "size_kb": round(total_bytes / 1024, 2)
    }

def clear_all_cache() -> int:
    """Menghapus semua file cache laporan dan mengembalikan jumlah file yang dihapus."""
    count = 0
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(CACHE_DIR, f))
                    count += 1
                except Exception:
                    pass
    return count
