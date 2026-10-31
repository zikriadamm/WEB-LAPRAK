"""
gemini_service.py
Layanan integrasi Google Gemini API untuk analisis teks modul PDF asdos
dan penyusunan draf laporan terstruktur sesuai acuan d:\\WEB LAPRAK\\format.md.
"""

import os
import json
import requests
import time

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash"
]

SYSTEM_INSTRUCTION = """
Anda adalah asisten AI akademik ahli dalam menyusun Laporan Praktikum perguruan tinggi berstandar tinggi.
Tugas Anda adalah membaca teks modul praktikum dari asisten dosen (asdos) dan mengekstrak serta menyusunnya menjadi data laporan terstruktur JSON yang patuh 100% pada aturan berikut:

1. ATURAN VERBATIM (BAB II & BAB III):
   - Teks Bab II (Teori Dasar) asdos WAJIB DISALIN PERSIS (verbatim) tanpa merubah kalimat aslinya.
   - Teks Bab III (Langkah Kerja) asdos WAJIB DISALIN PERSIS (verbatim). Tangkapan layar/foto asdos dibersihkan dan diganti item placeholder dengan deskripsi yang jelas.

2. ATURAN HALAMAN PENUH BAB II (FULL-PAGE RULE):
   - Jika materi asdos di Bab II tidak cukup memenuhi halaman (menyisakan ruang kosong nanggung sebelum Bab III), Anda WAJIB menambahkan 1-2 paragraf materi pengayaan teknis ilmiah mendalam yang relevan.
   - Paragraf pengayaan WAJIB menyertakan sitasi ilmiah format APA 7th Edition dari artikel Jurnal Ilmiah Akses Terbuka (Open-Access Free) dengan tahun terbit >= 2020 (dilarang buku berbayar).
   - Panjang kalimat pengayaan harus pas (sweet spot ~200-250 kata) agar halaman terisi penuh hingga batas margin bawah tanpa tumpah ke halaman baru.

3. ATURAN BAB IV (HASIL DAN PEMBAHASAN) DINAMIS PATUH MODUL:
   - Jumlah butir nomor pada Bab IV WAJIB DINAMIS dan 100% PATUH pada berapa poin luaran yang diminta pada bagian 'HASIL PERCOBAAN' modul asdos.
   - DILARANG KERAS mengambil atau mencampur butir dari bagian 'TUGAS' ke dalam Bab IV.
   - Jika modul meminta 2 nomor, buat 2 nomor. Jika modul meminta 3 nomor, buat 3 nomor.
   - Untuk setiap nomor: buat judul hasil, placeholder gambar hasil percobaan, dan pembahasan analisis teknis mendalam.

4. ATURAN BAB V (PENUTUP):
   - Hanya memuat kesimpulan untuk modul yang sedang dibahas saja (tidak menyertakan riwayat kesimpulan modul lampau).
   - Nomor kesimpulan menggunakan format 5.1.N (di mana N adalah nomor modul).

5. DAFTAR PUSTAKA:
   - Format APA 7th Edition, mencakup seluruh sitasi open-access >= 2020 yang disitasi pada Bab II.

6. ATURAN HIERARKI PENOMORAN MUTLAK (1. > a. > 1)):
   - Penomoran daftar langsung di bawah sub-bab WAJIB dimulai dari nomor angka desimal: 1., 2., 3. (level 1).
   - DILARANG KERAS melompat langsung ke huruf 'a.' jika tidak berada di dalam sub-butir nomor angka. Sekalipun modul asdos menulis huruf 'a.', Anda WAJIB menormalisasikannya menjadi angka '1.' (level 1).
   - Sub-butir di dalam butir angka menggunakan huruf: a., b., c. (level 2).
   - Sub-butir di dalam huruf menggunakan angka berkurung: 1), 2), 3) (level 3).
   - Setiap daftar butir yang terputus oleh paragraf narasi atau subjudul (misal: 'B. Button UI') harus di-reset kembali dari nomor 1.

STRUKTUR KELUARAN WAJIB FORMAT JSON:
{
  "module_number": 8,
  "module_title": "Judul Modul",
  "header_title": "MODUL PRAKTIKUM VIII\\n(JUDUL MODUL)",
  "student_name": "Nama Mahasiswa",
  "student_nim": "NIM",
  "student_class": "Kelas",
  "bab2": {
    "subbab_title": "Judul Modul",
    "content": [
      {"type": "paragraph", "text": "..."},
      {"type": "list", "prefix": "1.", "level": 1, "text": "..."}
    ]
  },
  "bab3": {
    "subbab_title": "Judul Modul",
    "content": [
      {"type": "list", "prefix": "1.", "level": 1, "text": "..."},
      {"type": "list", "prefix": "a.", "level": 2, "text": "..."},
      {"type": "placeholder", "text": "Deskripsi Gambar", "id": "placeholder_1"}
    ]
  },
  "bab4": {
    "subbab_title": "Judul Modul",
    "content": [
      {"type": "list", "prefix": "1.", "level": 1, "text": "Judul Hasil 1"},
      {"type": "placeholder", "text": "Deskripsi Gambar Luaran 1", "id": "bab4_img_1"},
      {"type": "list_body", "level": 1, "text": "Paragraf pembahasan analisis teknis..."}
    ]
  },
  "bab5": {
    "current_number": "5.1.8",
    "current_title": "Judul Modul",
    "current_conclusion": "Paragraf narasi kesimpulan komprehensif..."
  },
  "daftar_pustaka": [
    "Penulis, A. B. (2021). Judul Artikel. *Nama Jurnal*, 10(2), 100-110. https://doi.org/..."
  ]
}
"""

def extract_report_from_pdf_content(
    pdf_text: str,
    student_info: dict = None,
    api_key: str = None
) -> dict:
    """
    Memanggil Gemini API untuk memproses teks PDF modul dan menghasilkan draf laporan JSON.
    """
    student_info = student_info or {}
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API Key tidak ditemukan. Harap masukkan API Key di web atau konfigurasikan GEMINI_API_KEY di file .env.")

    nama = student_info.get("name", "")
    nim = student_info.get("nim", "")
    kelas = student_info.get("class", "Informatika C")
    mod_num = student_info.get("module_number", "")
    matkul = student_info.get("course", "Sistem Informasi Geografis")

    user_prompt = f"""
Berikut adalah teks modul praktikum yang diberikan oleh asisten dosen:

=== MULAI TEKS MODUL ===
{pdf_text}
=== SELESAI TEKS MODUL ===

Identitas Mahasiswa:
- Nama: {nama}
- NIM: {nim}
- Kelas: {kelas}
- Mata Kuliah: {matkul}
- Nomor Modul Pilihan: {mod_num if mod_num else 'Deteksi otomatis dari judul modul di PDF'}

Instruksi Tambahan:
- Susun laporan sesuai aturan format.md yang telah diberikan pada System Instructions.
- Keluarkan HANYA string JSON murni tanpa markdown codeblock (no ```json).
"""

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": SYSTEM_INSTRUCTION}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    last_error = None
    data = None

    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        for attempt in range(2):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=90)
                if resp.status_code == 200:
                    result = resp.json()
                    candidate_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    data = json.loads(candidate_text)
                    print(f"[Gemini] Berhasil mengekstrak modul menggunakan model: {model_name}")
                    break
                elif resp.status_code in [503, 429] and attempt == 0:
                    time.sleep(1.5)
                    continue
                else:
                    error_detail = resp.text
                    try:
                        err_json = resp.json()
                        if "error" in err_json and "message" in err_json["error"]:
                            error_detail = err_json["error"]["message"]
                    except Exception:
                        pass
                    last_error = f"Model {model_name} HTTP {resp.status_code}: {error_detail}"
                    print(f"[Gemini] {last_error}, mencoba model berikutnya...")
                    break
            except Exception as ex:
                last_error = f"Model {model_name} Exception: {ex}"
                print(f"[Gemini] {last_error}, mencoba model berikutnya...")
                break
        if data is not None:
            break

    if data is None:
        raise RuntimeError(f"Gagal memanggil seluruh kandidat model Gemini: {last_error}")

    # Pastikan identitas mahasiswa terisi
    data["student_name"] = nama
    data["student_nim"] = nim
    data["student_class"] = kelas
    if mod_num:
        try:
            data["module_number"] = int(mod_num)
        except ValueError:
            data["module_number"] = mod_num

    return data
