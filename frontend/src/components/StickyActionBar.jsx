import React from 'react';
import { Check, Eye, Download, Loader2 } from 'lucide-react';

export default function StickyActionBar({ 
  onPreview, 
  onDownload, 
  isDownloading, 
  hasData 
}) {
  if (!hasData) return null;

  return (
    <div className="bg-white border-3 border-black rounded-3xl p-4 sm:p-5 shadow-neo-lg flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 sticky bottom-4 sm:bottom-6 z-40 mb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-[#38EF7D] border-2 border-black rounded-xl flex items-center justify-center font-bold shadow-neo-sm shrink-0">
          <Check className="w-6 h-6 text-black" strokeWidth={3} />
        </div>
        <div>
          <p className="font-black text-sm text-black">Dokumen Siap Diekspor</p>
          <p className="text-xs font-bold text-gray-600">Margin 4-4-3-3 cm • Times New Roman 12 pt • 1.5 Spasi</p>
        </div>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto">
        <button 
          onClick={onPreview}
          aria-label="Lihat Pratinjau Teks Laporan"
          className="flex-1 sm:flex-none bg-[#F3EFE6] border-2 border-black px-5 py-3 rounded-xl font-black text-sm neo-btn shadow-neo-sm flex items-center justify-center gap-2 focus:outline-none focus-visible:ring-3 focus-visible:ring-black"
        >
          <Eye className="w-4 h-4 text-black" strokeWidth={2.5} />
          <span>Preview Teks</span>
        </button>

        <button 
          onClick={onDownload}
          disabled={isDownloading}
          aria-label="Unduh Dokumen Microsoft Word"
          className={`flex-1 sm:flex-none border-3 border-black px-6 py-3 rounded-xl font-black text-sm shadow-neo flex items-center justify-center gap-2 transition-all focus:outline-none focus-visible:ring-3 focus-visible:ring-black ${
            isDownloading 
              ? 'bg-gray-200 text-gray-500 cursor-not-allowed shadow-none' 
              : 'bg-[#FFE600] text-black neo-btn'
          }`}
        >
          {isDownloading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" strokeWidth={3} />
              <span>Membuat Word...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5 text-black" strokeWidth={2.5} />
              <span>Unduh Word (.docx)</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
