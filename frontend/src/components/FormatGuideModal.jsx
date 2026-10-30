import React from 'react';
import { BookOpen, X, CheckCircle2 } from 'lucide-react';

export default function FormatGuideModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white border-3 border-black rounded-3xl p-6 sm:p-8 max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-neo-lg space-y-6">
        <div className="flex items-center justify-between sticky top-0 bg-white pb-3 border-b-2 border-black">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#E2F87B] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm">
              <BookOpen className="w-5 h-5 text-black" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="font-black text-xl">Standar Format Akademik (format.md)</h3>
              <p className="text-xs font-bold text-gray-500">Aturan baku Microsoft Word .docx siap kumpul</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            aria-label="Tutup panduan standar format"
            className="w-8 h-8 rounded-lg border-2 border-black flex items-center justify-center neo-btn hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
          >
            <X className="w-4 h-4 text-black" strokeWidth={3} />
          </button>
        </div>

        <div className="space-y-4 text-sm font-bold text-gray-800">
          <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
            <h4 className="font-black text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38EF7D]" strokeWidth={3} /> 1. Tata Letak & Margin 4-4-3-3 cm
            </h4>
            <p className="text-xs text-gray-600 font-semibold pl-6">
              Kertas A4. Margin Atas 4 cm, Kiri 4 cm, Bawah 3 cm, Kanan 3 cm. Font Times New Roman 12 pt, 1.5 line spacing, Justified, identasi 1,27 cm.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
            <h4 className="font-black text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38EF7D]" strokeWidth={3} /> 2. Page Break Mutlak per Bab
            </h4>
            <p className="text-xs text-gray-600 font-semibold pl-6">
              Tiap bab (Cover, Bab II, Bab III, Bab IV, Bab V, Daftar Pustaka) selalu berdiri di halaman baru secara terpisah. Dilarang 2 bab bertumpuk di 1 halaman.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
            <h4 className="font-black text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38EF7D]" strokeWidth={3} /> 3. Bab II Verbatim + Full-Page Kalibrasi
            </h4>
            <p className="text-xs text-gray-600 font-semibold pl-6">
              Teks asdos tidak diubah. Ditambahkan materi pengayaan ilmiah (sitasi jurnal open-access &ge; 2020 format APA 7th) yang dipas-kan panjangnya agar halaman terisi penuh tanpa tumpah ke halaman baru.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
            <h4 className="font-black text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38EF7D]" strokeWidth={3} /> 4. Bab IV Dinamis 100% Patuh Modul Asdos
            </h4>
            <p className="text-xs text-gray-600 font-semibold pl-6">
              Jumlah butir luaran murni mengikuti jumlah butir pada Hasil Percobaan di modul asdos. Tidak mencampur atau mengambil poin dari bagian Tugas.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
            <h4 className="font-black text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38EF7D]" strokeWidth={3} /> 5. Aturan Header Modul Terusan (Modul &gt; 1)
            </h4>
            <p className="text-xs text-gray-600 font-semibold pl-6">
              Untuk modul terusan (seperti Modul 8), Bab V tidak memakai header BAB V PENUTUP dan 5.1 Kesimpulan, melainkan langsung mulai dengan Heading 3 (5.1.8) khusus modul terkait.
            </p>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={onClose}
            className="w-full bg-[#FFE600] border-2 border-black py-3 rounded-xl font-black text-sm neo-btn shadow-neo"
          >
            Tutup Panduan
          </button>
        </div>
      </div>
    </div>
  );
}
