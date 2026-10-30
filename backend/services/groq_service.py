"""
groq_service.py
Layanan integrasi Groq Cloud API (High-Speed LPU Inference)
Sebagai cadangan otomatis (zero-downtime fallback) jika Google Gemini mengalami lonjakan beban (503/429).
"""

import os
import json
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)
load_dotenv()

from services.gemini_service import SYSTEM_INSTRUCTION

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b"
]

def extract_report_with_groq(
    pdf_text: str,
    student_info: dict = None,
    api_key: str = None
) -> dict:
    """
    Memanggil Groq API untuk memproses teks modul praktikum menjadi JSON terstruktur
    sesuai standar format.md.
    """
    student_info = student_info or {}
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("Groq API Key tidak ditemukan di environment/backend/.env.")

    nama = student_info.get("name", "MOH. YUSFI LAKHAFIDUN")
    nim = student_info.get("nim", "F5512520089")
    kelas = student_info.get("class", "Informatika C")
    mod_num = student_info.get("module_number", "")
    matkul = student_info.get("course", "Sistem Informasi Geografis")

    user_prompt = f"""Berikut adalah teks modul praktikum dari asisten dosen:

=== MULAI TEKS MODUL ===
{pdf_text}
=== SELESAI TEKS MODUL ===

Identitas Mahasiswa:
- Nama: {nama}
- NIM: {nim}
- Kelas: {kelas}
- Mata Kuliah: {matkul}
- Nomor Modul Pilihan: {mod_num if mod_num else 'Deteksi otomatis dari judul modul di PDF'}

Instruksi:
- Susun draf laporan sesuai aturan yang tertera pada System Instructions.
- WAJIB keluarkan HANYA string JSON valid murni tanpa markdown triple-backticks.
"""

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    last_error = None
    for model_name in GROQ_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            print(f"[Groq] Memanggil model cadangan: {model_name}...")
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                res_json = resp.json()
                content = res_json["choices"][0]["message"]["content"].strip()
                data = json.loads(content)
                print(f"[Groq] Sukses mengekstrak laporan menggunakan {model_name}!")
                
                # Pastikan identitas terisi
                data["student_name"] = nama
                data["student_nim"] = nim
                data["student_class"] = kelas
                if mod_num:
                    try:
                        data["module_number"] = int(mod_num)
                    except ValueError:
                        data["module_number"] = mod_num
                return data
            else:
                last_error = f"Groq {model_name} HTTP {resp.status_code}: {resp.text}"
                print(f"[Groq] {last_error}, mencoba model berikutnya...")
        except Exception as e:
            last_error = f"Groq {model_name} Exception: {e}"
            print(f"[Groq] {last_error}, mencoba model berikutnya...")

    raise RuntimeError(f"Gagal memanggil model Groq: {last_error}")
