"""
rate_limiter.py
Sistem pembatasan laju permintaan (Rate Limiter) komprehensif berbasis algoritma Sliding-Window.
Mendukung standar IETF HTTP Header:
- RateLimit-Limit
- RateLimit-Remaining
- RateLimit-Reset
- Retry-After (pada HTTP 429 Too Many Requests)
"""

import time
import os
from functools import wraps
from collections import defaultdict
from flask import request, jsonify, make_response

class SlidingWindowRateLimiter:
    """
    Mesin pembatas laju permintaan dengan pencatatan waktu dinamis (sliding-window log).
    Akurat 100%, bebas dari lonjakan di batas interval (boundary spikes).
    """
    def __init__(self):
        # Struktur: { bucket_name: { client_ip: [timestamp1, timestamp2, ...] } }
        self.buckets = defaultdict(lambda: defaultdict(list))

    def check(self, bucket_name: str, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        Memeriksa apakah permintaan diizinkan.
        Mengembalikan tuple: (is_allowed: bool, remaining: int, reset_seconds: int)
        """
        now = time.time()
        cutoff = now - window_seconds

        timestamps = self.buckets[bucket_name][key]
        # Pangkas jejak waktu lama di luar window
        timestamps = [t for t in timestamps if t > cutoff]
        self.buckets[bucket_name][key] = timestamps

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            reset_seconds = max(1, int(oldest + window_seconds - now))
            return False, 0, reset_seconds

        timestamps.append(now)
        remaining = max_requests - len(timestamps)
        oldest = timestamps[0]
        reset_seconds = max(1, int(oldest + window_seconds - now))
        return True, remaining, reset_seconds

    def reset_all(self) -> int:
        """Membersihkan semua bucket dan riwayat IP."""
        total = sum(len(clients) for clients in self.buckets.values())
        self.buckets.clear()
        return total

    def get_active_summary(self, window_seconds: int = 600) -> dict:
        """Mengembalikan jumlah klien aktif per bucket."""
        now = time.time()
        summary = {}
        for b_name, clients in self.buckets.items():
            active = sum(1 for ts_list in clients.values() if any(now - t < window_seconds for t in ts_list))
            if active > 0:
                summary[b_name] = active
        return summary

# Instance global singleton
RATE_LIMITER = SlidingWindowRateLimiter()

def get_real_ip() -> str:
    """Mendeteksi alamat IP asli di balik reverse proxy (Railway, Vercel, Cloudflare)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.headers.get("CF-Connecting-IP") or request.remote_addr or "unknown_ip"

def rate_limit(max_requests: int, window_seconds: int, bucket: str = None, exempt_func = None):
    """
    Decorator penegak batas rate limiting per endpoint.
    
    :param max_requests: Batas maksimal request dalam window waktu
    :param window_seconds: Durasi window waktu dalam detik
    :param bucket: Nama kategori limit (default: nama endpoint)
    :param exempt_func: Fungsi opsional () -> bool. Jika mengembalikan True, limit di-bypass.
    """
    def decorator(f):
        bucket_name = bucket or f.__name__

        @wraps(f)
        def wrapper(*args, **kwargs):
            # Cek pengecualian (misal: user pakai API key pribadi atau role admin)
            if exempt_func and exempt_func():
                return f(*args, **kwargs)

            client_ip = get_real_ip()
            allowed, remaining, reset_sec = RATE_LIMITER.check(
                bucket_name, client_ip, max_requests, window_seconds
            )

            # Jika batas terlampaui, kembalikan HTTP 429 dengan Retry-After
            if not allowed:
                minutes_text = f"{window_seconds // 60} menit" if window_seconds >= 60 else f"{window_seconds} detik"
                resp = make_response(jsonify({
                    "error": (
                        f"Batas laju permintaan tercapai ({max_requests} request per {minutes_text}). "
                        f"Silakan tunggu {reset_sec} detik sebelum mencoba lagi."
                    ),
                    "retry_after_seconds": reset_sec
                }), 429)
                resp.headers["Retry-After"] = str(reset_sec)
                resp.headers["RateLimit-Limit"] = str(max_requests)
                resp.headers["RateLimit-Remaining"] = "0"
                resp.headers["RateLimit-Reset"] = str(reset_sec)
                return resp

            # Jika diizinkan, jalankan fungsi handler dan sematkan header RateLimit
            result = f(*args, **kwargs)
            resp = make_response(result)
            resp.headers["RateLimit-Limit"] = str(max_requests)
            resp.headers["RateLimit-Remaining"] = str(remaining)
            resp.headers["RateLimit-Reset"] = str(reset_sec)
            return resp

        return wrapper
    return decorator
