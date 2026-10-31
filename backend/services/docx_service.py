"""
docx_service.py
Layanan penghubung antara data JSON laporan dengan mesin pembuatan Word (report_engine.py).
"""

import os
import uuid
from core.report_engine import build_report_document

_base_dir = "/tmp" if os.environ.get("VERCEL") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(_base_dir, "uploads")
OUTPUT_DIR = os.path.join(UPLOAD_DIR, "generated_docs")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def generate_docx_report(report_data: dict, images_map: dict = None) -> str:
    """
    Mengompilasi berkas Microsoft Word (.docx) dari data laporan yang telah disunting.
    
    :param report_data: dict data laporan sesuai format.md
    :param images_map: dict ID placeholder ke path file gambar yang diunggah
    :return: path absolut file .docx yang siap diunduh
    """
    mod_num = report_data.get("module_number", 1)
    nim = report_data.get("student_nim", "f5512520089").lower()
    
    # Format nama file: <nim>_prak_gis_<mod_num>.docx
    safe_nim = "".join(c for c in nim if c.isalnum() or c in ("_", "-"))
    doc_id = uuid.uuid4().hex[:8]
    filename = f"{safe_nim}_prak_gis_{mod_num}_{doc_id}.docx"
    output_path = os.path.join(OUTPUT_DIR, filename)

    build_report_document(
        data=report_data,
        output_path=output_path,
        images_map=images_map or {}
    )

    return output_path
