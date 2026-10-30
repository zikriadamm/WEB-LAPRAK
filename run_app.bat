@echo off
title Menjalankan Web Laprak (Fullstack)
echo ========================================================
echo [Web Laprak] Menjalankan Backend & Frontend Sekaligus...
echo ========================================================

:: Jalankan Backend Flask di jendela terpisah
start "Web Laprak Backend (Port 5000)" cmd /k "cd /d "%~dp0backend" && py app.py"

:: Tunggu 2 detik agar backend siap
timeout /t 2 /nobreak >nul

:: Buka Browser otomatis
start http://localhost:5173/

:: Jalankan Frontend Vite
cd /d "%~dp0frontend"
npm run dev
