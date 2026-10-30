import React from 'react';
import { X, Eye, FileCheck } from 'lucide-react';

export default function PreviewModal({ isOpen, onClose, reportData }) {
  if (!isOpen || !reportData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm">
      <div className="bg-white border-3 border-black rounded-3xl max-w-3xl w-full h-[85vh] flex flex-col shadow-neo-lg overflow-hidden">
        
        {/* Header */}
        <div className="p-4 sm:p-6 border-b-3 border-black bg-[#FBF9F4] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#E2F87B] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm font-black">
              <Eye className="w-5 h-5 text-black" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="font-black text-xl tracking-tight leading-none">
                Pratinjau Draf Laporan
              </h3>
              <p className="text-xs font-bold text-gray-500 mt-1">
                Ikhtisar teks laporan sebelum diekspor ke Microsoft Word (.docx)
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Tutup jendela pratinjau"
            className="w-10 h-10 rounded-xl border-2 border-black bg-white flex items-center justify-center neo-btn hover:bg-gray-100 shadow-neo-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
          >
            <X className="w-5 h-5 text-black" strokeWidth={3} />
          </button>
        </div>

        {/* Content Viewer (Simulasi Tata Letak Dokumen) */}
        <div className="flex-1 p-6 sm:p-8 overflow-y-auto space-y-8 bg-[#FAF8F5] text-xs font-serif leading-relaxed text-gray-800">

          {/* Halaman Sampul */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm text-center space-y-3 font-sans">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400">--- HALAMAN 1: SAMPUL ---</p>
            <h4 className="font-black text-sm whitespace-pre-line">{reportData.header_title}</h4>
            <div className="text-xs font-bold text-gray-600 pt-2 space-y-0.5">
              <p>Nama : {reportData.student_name}</p>
              <p>NIM : {reportData.student_nim}</p>
              <p>Kelas : {reportData.student_class}</p>
            </div>
          </div>

          {/* Bab II */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm space-y-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 font-sans">--- HALAMAN 2: BAB II LANDASAN TEORI ---</p>
            <h4 className="font-black text-sm font-sans">
              2.1.{reportData.module_number}&emsp;{reportData.bab2?.subbab_title || reportData.module_title}
            </h4>
            <div className="space-y-2 text-justify">
              {reportData.bab2?.content?.map((item, i) => (
                <p key={i} className={item.type === 'list' ? 'pl-6 font-sans' : 'indent-6'}>
                  {item.type === 'list' ? `${item.prefix} ${item.text}` : item.text}
                </p>
              ))}
            </div>
          </div>

          {/* Bab III */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm space-y-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 font-sans">--- HALAMAN 3: BAB III LANGKAH KERJA ---</p>
            <h4 className="font-black text-sm font-sans">
              3.1.{reportData.module_number}&emsp;{reportData.bab3?.subbab_title || reportData.module_title}
            </h4>
            <div className="space-y-2">
              {reportData.bab3?.content?.map((item, i) => {
                if (item.type === 'placeholder') {
                  return (
                    <p key={i} className="pl-6 text-[11px] font-sans font-bold italic text-gray-500">
                      [Sisipkan Gambar: {item.text}]
                    </p>
                  );
                }
                return (
                  <p key={i} className="pl-6 font-sans">
                    {item.prefix ? `${item.prefix} ${item.text}` : item.text}
                  </p>
                );
              })}
            </div>
          </div>

          {/* Bab IV */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm space-y-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 font-sans">--- HALAMAN 4: BAB IV HASIL DAN PEMBAHASAN ---</p>
            <h4 className="font-black text-sm font-sans">
              4.1.{reportData.module_number}&emsp;{reportData.bab4?.subbab_title || reportData.module_title}
            </h4>
            <div className="space-y-3">
              {reportData.bab4?.content?.map((item, i) => {
                if (item.type === 'placeholder') {
                  return (
                    <p key={i} className="pl-6 text-[11px] font-sans font-bold italic text-gray-500">
                      [Sisipkan Gambar: {item.text}]
                    </p>
                  );
                }
                if (item.type === 'list_body') {
                  return (
                    <p key={i} className="pl-6 text-justify">
                      {item.text}
                    </p>
                  );
                }
                return (
                  <p key={i} className="pl-6 font-sans font-bold text-gray-900">
                    {item.prefix ? `${item.prefix} ${item.text}` : item.text}
                  </p>
                );
              })}
            </div>
          </div>

          {/* Bab V */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm space-y-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 font-sans">--- HALAMAN 5: BAB V PENUTUP ---</p>
            <h4 className="font-black text-sm font-sans">
              5.1.{reportData.module_number}&emsp;{reportData.bab5?.current_title || reportData.module_title}
            </h4>
            <p className="indent-6 text-justify">
              {reportData.bab5?.current_conclusion}
            </p>
          </div>

          {/* Daftar Pustaka */}
          <div className="bg-white border-2 border-black p-6 rounded-2xl shadow-neo-sm space-y-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 font-sans">--- HALAMAN 6: DAFTAR PUSTAKA ---</p>
            <h4 className="font-black text-sm font-sans text-center">DAFTAR PUSTAKA</h4>
            <div className="space-y-2 font-sans text-xs">
              {reportData.daftar_pustaka?.map((ref, i) => (
                <p key={i} className="pl-6 -indent-6">
                  {typeof ref === 'string' ? ref : `${ref.author} (${ref.year}). ${ref.title}. ${ref.source}. ${ref.url}`}
                </p>
              ))}
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 sm:p-6 border-t-3 border-black bg-white flex items-center justify-between">
          <span className="text-xs font-bold text-gray-500 flex items-center gap-1.5">
            <FileCheck className="w-4 h-4 text-green-600" /> Format patuh 4-4-3-3 & APA 7th Edition
          </span>
          <button
            onClick={onClose}
            className="bg-[#FFE600] border-2 border-black px-6 py-2.5 rounded-xl font-black text-sm neo-btn shadow-neo"
          >
            Tutup Pratinjau
          </button>
        </div>

      </div>
    </div>
  );
}
