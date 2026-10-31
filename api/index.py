"""
api/index.py
Vercel Serverless Function entrypoint untuk backend Flask Web Laprak.
Mengarahkan seluruh rute /api/* ke aplikasi Flask secara serverless.
"""

import sys
import os

# Tambahkan direktori root dan backend ke sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for path in [ROOT_DIR, BACKEND_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Tandai bahwa aplikasi berjalan di lingkungan Vercel Serverless
os.environ["VERCEL"] = "1"

# Impor instance Flask app
from backend.app import app

# Handler diekspor langsung sebagai app untuk WSGI runner Vercel
app = app
