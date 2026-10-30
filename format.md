# Standar Format Laporan Praktikum Akademik

Dokumen ini adalah acuan format baku yang **wajib dipatuhi 100% tanpa kompromi** dalam pembuatan dan generasi dokumen Laporan Praktikum (.docx) pada proyek ini.

---

## 1. Tata Letak Halaman & Tipografi Dokumen

| Parameter | Spesifikasi Resmi | Keterangan Teknis OpenXML |
|---|---|---|
| **Ukuran Kertas** | A4 (21,0 cm × 29,7 cm) | `w:pgSz w:w="11906" w:h="16838"` |
| **Margin Atas (Top)** | **4,0 cm** | `w:top="2268"` |
| **Margin Kiri (Left)** | **4,0 cm** | `w:left="2268"` |
| **Margin Bawah (Bottom)** | **3,0 cm** | `w:bottom="1701"` |
| **Margin Kanan (Right)** | **3,0 cm** | `w:right="1701"` |
| **Font Utama** | **Times New Roman**, 12 pt | `w:rFonts w:ascii="Times New Roman"` |
| **Font Placeholder Gambar** | **Times New Roman**, 11 pt, Italic Bold, Warna Abu-abu (`#646464`) | `[Sisipkan Gambar: <Deskripsi>]` |
| **Spasi Baris** | **1,5 Line Spacing** | `w:spacing w:line="360" w:lineRule="auto"` |
| **Warna Teks** | Hitam Pekat (`#000000`) | `w:color w:val="000000"` |
| **Perataan Teks** | Rata Kiri-Kanan (*Justified*) | `w:jc w:val="both"` |
| **Indentasi Paragraf** | **1,27 cm** (0,5 inci) pada baris pertama | `w:ind w:firstLine="720"` |

---

## 2. Aturan Pemisahan Halaman Mutlak (*Page Break*)

> **Aturan Mutlak**: **TIAP BAB TIDAK BOLEH BERTEMU DI HALAMAN YANG SAMA!**
> Setiap bab wajib dipisahkan dengan elemen OpenXML `<w:br w:type="page"/>`:
> 1. **Halaman 1**: Halaman Sampul (Identitas Mahasiswa) $\rightarrow$ *Page Break*
> 2. **Halaman 2**: Bab II (Landasan Teori) $\rightarrow$ *Page Break*
> 3. **Halaman Baru**: Bab III (Langkah Kerja) $\rightarrow$ *Page Break*
> 4. **Halaman Baru**: Bab IV (Hasil dan Pembahasan) $\rightarrow$ *Page Break*
> 5. **Halaman Baru**: Bab V (Penutup) $\rightarrow$ *Page Break*
> 6. **Halaman Baru**: DAFTAR PUSTAKA

---

## 3. Penomoran Sub-Bab Dinamis Sesuai Nomor Modul

Nomor modul ditentukan secara dinamis dari input pengguna atau dokumen modul asdos ($N$):
- Halaman Sampul: `MODUL PRAKTIKUM <ROMAWI>` (contoh: `MODUL PRAKTIKUM VIII`)
- Bab II: `\t2.1.<N>\t<Judul Modul>` (contoh: `\t2.1.8\tIntegrasi Data Lapangan...`)
- Bab III: `\t3.1.<N>\t<Judul Modul>` (contoh: `\t3.1.8\tIntegrasi Data Lapangan...`)
- Bab IV: `\t4.1.<N>\t<Judul Modul>` (contoh: `\t4.1.8\tIntegrasi Data Lapangan...`)
- Bab V: `\t5.1.<N>\t<Judul Modul>` (contoh: `\t5.1.8\tIntegrasi Data Lapangan...`)
- Nama Berkas Output: `<nim>_prak_<matkul>_<N>.docx` (contoh: `f5512520089_prak_gis_8.docx`)

---

## 4. Aturan Hierarki Penomoran Butir (List) & Pemisahan Paragraf

### A. Hierarki Penomoran Mutlak: `1. > a. > 1)`
1. **Tingkat 1 (List Utama)**: Wajib diawali dengan angka desimal bertitik: `1.`, `2.`, `3.`, dst.
   - **Aturan Mutlak**: Daftar butir langsung di bawah judul sub-bab atau paragraf **DILARANG KERAS** melompat langsung ke huruf `a.`. Sekalipun di modul asdos tertulis huruf, sistem wajib menormalisasikannya menjadi angka `1.`, `2.`, dst.
2. **Tingkat 2 (Sub-Butir)**: Huruf kecil bertitik: `a.`, `b.`, `c.`, dst.
   - Hanya boleh digunakan jika merupakan anak butir di bawah butir angka (Tingkat 1).
3. **Tingkat 3 (Sub-Sub-Butir)**: Angka berkurung tutup: `1)`, `2)`, `3)`, dst.
   - Hanya boleh digunakan jika merupakan anak butir di bawah huruf (Tingkat 2).

### B. Aturan Pemisahan List oleh Paragraf (Auto-Reset Numbering)
1. **Dilarang Menyambung Butir yang Terpisah Paragraf**:
   - Jika suatu daftar butir telah berakhir, kemudian diselingi oleh teks paragraf narasi biasa, subjudul (misal: `B. Button UI`), atau penjelasan lainnya, maka daftar butir berikutnya **WAJIB DI-RESET KEMBALI DARI NOMOR 1** (atau `a.` jika di dalam sub-butir).
   - Dilarang keras melanjutkan urutan nomor (misal dari `7.` langsung menyambung ke `8.` setelah paragraf narasi).
2. **Implementasi Teknis OpenXML**:
   - Setiap kemunculan blok daftar baru setelah jeda teks non-list wajib dialokasikan instance `<w:num w:numId="...">` baru dengan `<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>` agar Microsoft Word merender ulang nomor dari awal.

---

## 5. Sistematika Rinci per Bab

### A. Halaman Sampul (Halaman 1)
- Mandiri pada Halaman 1, perataan tengah (*Center Aligned*), diposisikan di area tengah secara vertikal:
  ```text
  MODUL PRAKTIKUM <NO_MODUL_ROMAWI>
  (<JUDUL MODUL PRAKTIKUM>)
  Nama : <NAMA MAHASISWA>
  NIM : <NIM MAHASISWA>
  Kelas : <KELAS MAHASISWA>
  ```
- Diakhiri dengan *Page Break*.

### B. Bab II (Landasan Teori - Halaman 2 Baru)
1. **Heading**:
   - Jika Modul Terusan ($N > 1$): Langsung dimulai dengan **Heading 3** `\t2.1.<N>\t<Judul Modul>` (diawali tab, nomor di 1,27 cm, judul di 2,54 cm). Tanpa Heading 1 dan 2.
   - Jika Modul Mandiri / Modul 1 ($N = 1$): Heading 1 `BAB II \nLANDASAN TEORI`, Heading 2 `2.1\tLandasan Teori`, Heading 3 `\t2.1.1\t<Judul Modul>`.
2. **Teks Asdos Verbatim**: Seluruh materi asli yang diberikan asdos disalin **persis tanpa mengubah susunan kalimat aslinya**.
3. **Prinsip Halaman Penuh Mutlak (*Full-Page Rule*) & Kalibrasi Presisi**:
   - Setiap halaman yang ditempati Bab II **WAJIB TERISI PENUH HINGGA BATAS MARGIN BAWAH**.
   - Dilarang keras ada halaman terakhir Bab II yang menyisakan ruang kosong nanggung di bawahnya.
   - **DILARANG KERAS** menambahkan materi pengayaan yang tumpah sedikit (1–6 baris) ke halaman baru, sehingga halaman baru tersebut menjadi kosong melompong.
   - Panjang paragraf pengayaan ilmiah wajib **dikalibrasi secara presisi** (*sweet spot* ~200–250 kata untuk mengisi sisa ruang yang ada) sehingga pas memenuhi halaman tersebut dan **TIDAK meluap satu kalimat pun ke halaman baru**.
4. **Sitasi Ilmiah Open-Access (Free $\ge$ 2020)**:
   - Teks materi pengayaan wajib memuat sitasi ilmiah format APA 7th Edition (contoh: `Ariyanto & Hani'ah, 2021`).
   - Wajib berasal dari artikel Jurnal Ilmiah Akses Terbuka (*Open-Access Free*) terbitan tahun **$\ge 2020$** dengan DOI atau tautan repositori aktif.
   - **Dilarang menggunakan buku berbayar (*paid books*)**.
5. Diakhiri dengan *Page Break*.

### C. Bab III (Langkah Kerja - Halaman Baru)
1. **Heading**:
   - Jika Modul Terusan ($N > 1$): Langsung dimulai dengan **Heading 3** `\t3.1.<N>\t<Judul Modul>`.
   - Jika Modul 1: Heading 1 `BAB III \nLANGKAH KERJA`, Heading 2 `3.1\tLangkah Kerja`, Heading 3 `\t3.1.1\t<Judul Modul>`.
2. **Teks Langkah Kerja Verbatim**: Seluruh kalimat instruksi langkah kerja disalin persis sesuai modul asdos.
3. **Pembersihan Foto & Placeholder Gambar**:
   - Seluruh tangkapan layar/foto asdos dibersihkan dan diganti dengan placeholder `[Sisipkan Gambar: <Deskripsi>]` (atau disisipi foto asli praktikum mahasiswa).
   - Format placeholder: Font Times New Roman 11 pt, Italic Bold, Warna Abu-abu (`#646464`).
4. **Penjajaran List & Gambar (Pola 1 Presisi)**:
   - Penomoran native Word (`<w:numPr>`): Angka list berada di **2,54 cm**.
   - Huruf pertama teks langkah kerja dan placeholder gambar berada di **3,29 cm** (*hanging indent* 0,75 cm, rata kiri *left-aligned*).
5. Diakhiri dengan *Page Break*.

### D. Bab IV (Hasil dan Pembahasan - Halaman Baru)
1. **Heading**:
   - Jika Modul Terusan ($N > 1$): Langsung dimulai dengan **Heading 3** `\t4.1.<N>\t<Judul Modul>`.
   - Jika Modul 1: Heading 1 `BAB IV \nHASIL DAN PEMBAHASAN`, Heading 2 `4.1\tHasil dan Pembahasan`, Heading 3 `\t4.1.1\t<Judul Modul>`.
2. **Jumlah Butir DINAMIS 100% Patuh Modul Asdos**:
   - Jumlah butir luaran pada Bab IV **murni mengikuti berapa poin yang diminta pada bagian `HASIL PERCOBAAN` modul asdos**.
   - Dilarang keras berasumsi atau menggabungkan butir dari bagian lain (seperti dari bagian `TUGAS`) ke dalam Bab IV.
   - Jika di modul hanya ada 2 poin, maka Bab IV hanya berisi 2 nomor. Jika di modul ada 3 atau 4 poin, maka Bab IV berisi 3 atau 4 nomor.
3. **Struktur Tiap Poin Hasil**:
   - Sub-judul nomor hasil: Angka di **2,54 cm**, teks judul di **3,29 cm**.
   - Placeholder gambar: `[Sisipkan Gambar: <Deskripsi Luaran>]` rata kiri sejajar teks di **3,29 cm**.
   - Pembahasan teknis: Analisis mendalam mengenai hasil percobaan diletakkan lurus di posisi **3,29 cm** (`first_line_indent = 0`, Justified).
4. Diakhiri dengan *Page Break*.

### E. Bab V (Penutup - Halaman Baru)
1. **Aturan Header Modul Terusan (Poin > 5.1.1 / Modul > 1)**:
   - Jika modul yang dikerjakan adalah modul lanjutan ($N > 1$):
     - **TIDAK USAH memakai Heading 1 (`BAB V PENUTUP`)**
     - **TIDAK USAH memakai Heading 2 (`5.1 Kesimpulan`)**
     - **LANGSUNG DIMULAI DENGAN HEADING 3**: `\t5.1.<N>\t<Judul Modul>` (diawali karakter tab, nomor di 1,27 cm, judul di 2,54 cm).
   - Jika Modul 1 ($N = 1$): Heading 1 `BAB V \nPENUTUP`, Heading 2 `5.1\tKesimpulan`, lalu Heading 3 `\t5.1.1\t<Judul Modul>`.
2. **Hanya Kesimpulan Modul Terkait**:
   - Bab V **hanya memuat kesimpulan untuk modul yang sedang dikerjakan saja**.
   - Riwayat kesimpulan kumulatif dari modul-modul terdahulu ditiadakan.
3. **Penjajaran Paragraf Kesimpulan**:
   - Baris pertama menjorok di **2,54 cm** (sejajar huruf pertama judul sub-bab).
   - Baris kalimat berikutnya membungkus lurus sejajar di **1,27 cm** (sejajar angka 5).
4. Diakhiri dengan *Page Break*.

### F. Daftar Pustaka (Halaman Baru)
1. Berdiri di halaman baru dengan Heading 1 `DAFTAR PUSTAKA` (Center, Bold, Outline Level 0).
2. Format **APA 7th Edition**:
   - *Hanging indent* 1,27 cm (`left_indent = 1.27 cm`, `first_line_indent = -1.27 cm`).
   - Spasi baris 1,5, urut abjad.
   - Judul buku atau jurnal wajib dicetak miring (*italic*).
3. Memuat seluruh sumber jurnal ilmiah *Open-Access* $\ge 2020$ yang disitasi pada Bab II.

---

## 6. Aturan Cetak Miring Istilah Non-KBBI Otomatis

> **Aturan Mutlak**: Seluruh kata, istilah teknis, atau frasa yang **bukan bahasa Indonesia resmi (tidak tercantum dalam KBBI)** WAJIB dicetak miring (*italic*).

- Berlaku konsisten di seluruh bab (Bab II, Bab III, Bab IV, Bab V).
- Contoh istilah yang otomatis dicetak miring:
  *smartphone*, *basemap*, *real-time*, *layers*, *shapefile*, *toolbar*, *field calculator*, *interchange format*, *waypoint*, *track*, *route*, *Delimited Text*, *Decimal Degrees*, *buffer*, *clipping*, *intersect*, *geoprocessing*, dll.
