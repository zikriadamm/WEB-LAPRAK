---
title: Web Laprak API
emoji: 📑
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Web Laprak Generator ⚡

Aplikasi web modern untuk otomatisasi pembuatan dokumen **Laporan Praktikum Microsoft Word (.docx)** berstandar akademik tinggi dari berkas PDF modul asisten dosen (asdos).

---

## 🎨 Tampilan & Desain
Mengusung gaya desain **Neubrutalism (Neo-Brutalist Pop)**:
- Garis tepi hitam tegas (`border-3 border-black`) dan sudut melengkung kokoh.
- *Hard solid shadow* blok hitam murni (`box-shadow: 4px 4px 0px #000`).
- Kartu bergaya map folder arsip dengan tab warna-warni (`COVER`, `2.1.N`, `3.1.N`, `4.1.N`, `5.1.N`, `APA 7TH`).
- 100% menggunakan ikon vektor *line-art* SVG hitam presisi tanpa emoji.

---

## 📜 Kepatuhan Format Akademik (format.md)
1. **Margin 4-4-3-3 cm**: Atas 4 cm, Kiri 4 cm, Bawah 3 cm, Kanan 3 cm, Kertas A4.
2. **Tipografi Baku**: Times New Roman 12 pt, 1.5 line spacing, Justified, indentasi baris pertama 1,27 cm.
3. **Pemisahan Halaman Mutlak (*Page Break*)**: Halaman Sampul, Bab II, Bab III, Bab IV, Bab V, dan Daftar Pustaka masing-masing berdiri di halaman baru secara terpisah.
4. **Bab II Full-Page & Kalibrasi Presisi**: Teks asdos verbatim + sitasi ilmiah jurnal *Open-Access* $\ge 2020$ yang dikalibrasi presisi agar halaman penuh hingga margin bawah tanpa meluap ke halaman baru.
5. **Bab III Langkah Kerja**: Verbatim asdos + fitur unggah screenshot praktikum asli mahasiswa (atau mempertahankan placeholder abu-abu jika belum ada foto).
6. **Bab IV Dinamis Patuh Modul**: Jumlah poin luaran murni mengikuti jumlah butir pada bagian *Hasil Percobaan* modul asdos (tanpa mencampur butir Tugas).
7. **Bab V Modul Terusan ($N > 1$)**: Langsung dimulai dengan Heading 3 (`\t5.1.N\t<Judul>`) tanpa parent heading, khusus kesimpulan modul terkait.
8. **Daftar Pustaka**: Format APA 7th Edition, *hanging indent* 1,27 cm.
9. **Cetak Miring Non-KBBI Otomatis**: Istilah teknis/asing otomatis dicetak miring (*italic*).

---

## 🚀 Cara Menjalankan

### Cara Cepat (1-Klik):
Cukup klik ganda berkas:
👉 **`run_app.bat`**

Peramban akan otomatis membuka antarmuka di `http://localhost:5173/`.

### Cara Manual:

#### 1. Jalankan Backend (Port 5000):
```powershell
cd "d:\WEB LAPRAK\backend"
py app.py
```

#### 2. Jalankan Frontend (Port 5173):
```powershell
cd "d:\WEB LAPRAK\frontend"
npm run dev
```
Buka peramban di `http://localhost:5173/`.
