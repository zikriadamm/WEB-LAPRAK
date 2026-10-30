"""
pdf_service.py
Layanan ekstraksi teks dan struktur berkas PDF modul asdos menggunakan PyMuPDF (fitz)
dilengkapi kecerdasan OCR Multimodal otomatis berbasis Google Gemini Vision untuk PDF scan/gambar.
"""

import os
import base64
import requests
import pymupdf as fitz

def ocr_pdf_with_gemini(pdf_path: str, api_key: str = None) -> str:
    """
    Mengekstrak teks dari berkas PDF scan/gambar secara multimodal menggunakan Gemini Vision API.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return ""

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        
        models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash",
            "gemini-3-flash-preview",
            "gemini-3.8-flash",
            "gemini-3.7-flash"
        ]

        prompt = (
            "Anda adalah sistem OCR cerdas berakurasi tinggi. "
            "Baca seluruh teks dari dokumen PDF modul praktikum ini secara lengkap, runtut, dan verbatim "
            "(kata demi kata) dari halaman pertama sampai halaman terakhir tanpa merangkum atau memotong teks. "
            "Tuliskan seluruh isi modulnya secara jelas."
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": key
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "application/pdf",
                                "data": pdf_b64
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }

        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=90)
                if resp.status_code == 200:
                    result = resp.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        print(f"[OCR Gemini] Berhasil mengekstrak teks PDF scan dengan model: {m} ({len(text)} karakter).")
                        return text
                elif resp.status_code in [404, 503, 429]:
                    continue
            except Exception as model_err:
                print(f"[OCR Gemini] Error pada model {m}: {model_err}")
                continue

    except Exception as e:
        print(f"[OCR Gemini] Gagal membaca PDF secara visual: {e}")

    return ""

def extract_text_from_pdf(pdf_path: str, api_key: str = None) -> dict:
    """
    Mengekstrak seluruh teks dari berkas PDF modul asdos beserta informasi halaman.
    Jika PDF berupa scan gambar tanpa teks (0 karakter), otomatis memicu OCR AI Gemini Vision.
    
    :param pdf_path: Path absolut ke file PDF
    :param api_key: API Key Gemini opsional
    :return: dict berisi total_pages, full_text, pages list, dan is_ocr
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Berkas PDF tidak ditemukan: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages_data = []
    full_text_list = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        pages_data.append({
            "page_number": page_num + 1,
            "text": text
        })
        if text:
            full_text_list.append(f"--- [Halaman {page_num + 1}] ---\n{text}")

    total_pages = len(pages_data)
    doc.close()

    full_text = "\n\n".join(full_text_list).strip()

    # Jika teks kosong atau sangat sedikit (< 50 karakter), picu fallback OCR AI Gemini
    if len(full_text) < 50:
        print(f"[pdf_service] Teks PDF hanya {len(full_text)} karakter (terdeteksi scan gambar). Mengaktifkan OCR Multimodal Gemini...")
        ocr_text = ocr_pdf_with_gemini(pdf_path, api_key=api_key)
        if ocr_text:
            return {
                "total_pages": total_pages,
                "full_text": ocr_text,
                "pages": [{"page_number": 1, "text": ocr_text}],
                "is_ocr": True
            }

    return {
        "total_pages": total_pages,
        "full_text": full_text,
        "pages": pages_data,
        "is_ocr": False
    }
