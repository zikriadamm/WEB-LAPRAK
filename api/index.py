"""
api/index.py
Vercel Serverless Function entrypoint untuk backend Flask Web Laprak.
Mengarahkan seluruh rute /api/* ke aplikasi Flask secara serverless.
"""

import sys
import os
from urllib.parse import parse_qs, urlencode

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for path in [ROOT_DIR, BACKEND_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ["VERCEL"] = "1"

from backend.app import app

class VercelPathFixMiddleware:
    """
    Middleware WSGI untuk memulihkan rute asli /api/... dari rewrite Vercel.
    Memastikan PATH_INFO cocok dengan rute Flask @app.route('/api/...').
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        if "__path=" in qs:
            params = parse_qs(qs)
            if "__path" in params and params["__path"]:
                subpath = params.pop("__path")[0]
                environ["PATH_INFO"] = f"/api/{subpath.lstrip('/')}"
                environ["QUERY_STRING"] = urlencode(params, doseq=True)
        elif environ.get("PATH_INFO") in ["/api/index.py", "/api/index", "/api/"]:
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
