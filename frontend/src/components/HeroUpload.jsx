import React, { useRef } from 'react';
import { FileText, Sparkles, UploadCloud, Loader2 } from 'lucide-react';

export default function HeroUpload({ 
  selectedFile, 
  onFileSelect, 
  studentInfo, 
  setStudentInfo, 
  onExtract, 
  isLoading,
  loadingStep,
  onError 
}) {
  const fileInputRef = useRef(null);

  const validateAndSelectFile = (file) => {
    if (!file) return;
    const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
    if (!isPdf) {
      if (onError) onError('Berkas harus berformat PDF (.pdf)');
      return;
    }
    // Batas maksimal 30 MB
    if (file.size > 30 * 1024 * 1024) {
      if (onError) onError('Ukuran berkas PDF melebihi batas maksimal yang diizinkan (30 MB)');
      return;
    }
    onFileSelect(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-white border-3 border-black rounded-3xl p-6 md:p-8 shadow-neo-lg space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight leading-tight text-black">
            Upload PDF.<br />
            <span className="text-[#FF5B99]">Auto Siap Kumpul.</span>
          </h2>
          <p className="text-gray-700 font-bold mt-2 text-sm sm:text-base">
            Ubah modul praktikum asdos ke dokumen Microsoft Word .docx siap cetak sesuai standar akademik.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          <span className="bg-[#38EF7D] border-2 border-black px-3 py-1 rounded-full text-xs font-black shadow-neo-sm flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-black"></span>
            AI ENGINE READY
          </span>
          <span className="bg-[#FFE600] border-2 border-black px-3 py-1 rounded-full text-xs font-black shadow-neo-sm">
            MODUL {studentInfo.module_number ? studentInfo.module_number : 'AUTO'}
          </span>
        </div>
      </div>

      {/* Input Bar Upload */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          ref={fileInputRef}
          type="file"
          id="pdf-upload-input"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              validateAndSelectFile(e.target.files[0]);
            }
          }}
        />

        <div
          role="button"
          tabIndex={0}
          aria-label="Pilih atau seret berkas PDF Modul Praktikum"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          className="flex-1 bg-[#FBF9F4] border-3 border-black rounded-2xl p-4 flex items-center justify-between shadow-neo-sm hover:bg-[#F3EFE6] transition-colors cursor-pointer group focus:outline-none focus-visible:ring-3 focus-visible:ring-black"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm group-hover:bg-[#FFE600] transition-colors">
              {selectedFile ? (
                <FileText className="w-5 h-5 text-black" strokeWidth={2.5} />
              ) : (
                <UploadCloud className="w-5 h-5 text-black" strokeWidth={2.5} />
              )}
            </div>
            <div>
              <p className="font-black text-sm text-black truncate max-w-xs sm:max-w-md">
                {selectedFile ? selectedFile.name : 'Klik atau seret file PDF Modul Asdos ke sini'}
              </p>
              <p className="text-xs font-bold text-gray-600">
                {selectedFile 
                  ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Berkas PDF terpilih` 
                  : 'Mendukung format PDF teks digital & scan gambar (dengan OCR AI)'}
              </p>
            </div>
          </div>
          <span className="bg-white border-2 border-black px-3 py-1.5 rounded-xl text-xs font-black shadow-neo-sm">
            {selectedFile ? 'Ganti File' : 'Pilih File'}
          </span>
        </div>

        <button
          onClick={onExtract}
          disabled={!selectedFile || isLoading}
          aria-label="Susun Draf Laporan Otomatis"
          className={`border-3 border-black px-8 py-4 rounded-2xl font-black text-base shadow-neo flex items-center justify-center gap-2 transition-all focus:outline-none focus-visible:ring-3 focus-visible:ring-black ${
            !selectedFile || isLoading 
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none' 
              : 'bg-[#FFE600] text-black neo-btn'
          }`}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" strokeWidth={3} />
              <span>{loadingStep || 'Menganalisis...'}</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-black" strokeWidth={2.5} />
              <span>Susun Draf Laporan</span>
            </>
          )}
        </button>
      </div>

      {/* Profil Mahasiswa Pill Form (Terstruktur 5 Field) */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-black uppercase tracking-wider text-gray-700">
            Identitas Mahasiswa & Praktikum
          </span>
          <span className="text-[11px] font-bold text-gray-500">
            *Otomatis tersimpan di browser
          </span>
        </div>

        {/* Baris 1: Nama, NIM, Kelas */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="bg-[#F8F6F0] border-2 border-black p-3 rounded-2xl shadow-neo-sm">
            <label htmlFor="student-name" className="text-xs font-black text-gray-700 uppercase tracking-wider block mb-1">
              Nama Mahasiswa
            </label>
            <input
              id="student-name"
              type="text"
              maxLength={120}
              value={studentInfo.name || ''}
              onChange={(e) => setStudentInfo({ ...studentInfo, name: e.target.value })}
              className="w-full bg-transparent font-bold text-sm text-black placeholder:text-gray-400 focus:outline-none"
              placeholder="Contoh: Ahmad Dahlan"
            />
          </div>

          <div className="bg-[#F8F6F0] border-2 border-black p-3 rounded-2xl shadow-neo-sm">
            <label htmlFor="student-nim" className="text-xs font-black text-gray-700 uppercase tracking-wider block mb-1">
              NIM
            </label>
            <input
              id="student-nim"
              type="text"
              maxLength={30}
              value={studentInfo.nim || ''}
              onChange={(e) => setStudentInfo({ ...studentInfo, nim: e.target.value })}
              className="w-full bg-transparent font-bold text-sm text-black placeholder:text-gray-400 focus:outline-none"
              placeholder="Contoh: F55123001"
            />
          </div>

          <div className="bg-[#F8F6F0] border-2 border-black p-3 rounded-2xl shadow-neo-sm">
            <label htmlFor="student-class" className="text-xs font-black text-gray-700 uppercase tracking-wider block mb-1">
              Kelas
            </label>
            <input
              id="student-class"
              type="text"
              maxLength={50}
              value={studentInfo.class || ''}
              onChange={(e) => setStudentInfo({ ...studentInfo, class: e.target.value })}
              className="w-full bg-transparent font-bold text-sm text-black placeholder:text-gray-400 focus:outline-none"
              placeholder="Contoh: Informatika A"
            />
          </div>
        </div>

        {/* Baris 2: Mata Kuliah & Nomor Modul */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-2 bg-[#F8F6F0] border-2 border-black p-3 rounded-2xl shadow-neo-sm">
            <label htmlFor="student-course" className="text-xs font-black text-gray-700 uppercase tracking-wider block mb-1">
              Mata Kuliah Praktikum
            </label>
            <input
              id="student-course"
              type="text"
              maxLength={100}
              value={studentInfo.course || ''}
              onChange={(e) => setStudentInfo({ ...studentInfo, course: e.target.value })}
              className="w-full bg-transparent font-bold text-sm text-black placeholder:text-gray-400 focus:outline-none"
              placeholder="Contoh: Sistem Informasi Geografis"
            />
          </div>

          <div className="bg-[#F8F6F0] border-2 border-black p-3 rounded-2xl shadow-neo-sm">
            <label htmlFor="student-module" className="text-xs font-black text-gray-700 uppercase tracking-wider block mb-1">
              Nomor Modul (Opsional)
            </label>
            <input
              id="student-module"
              type="text"
              maxLength={10}
              value={studentInfo.module_number || ''}
              onChange={(e) => setStudentInfo({ ...studentInfo, module_number: e.target.value })}
              className="w-full bg-transparent font-bold text-sm text-[#9D71FD] placeholder:text-gray-400 focus:outline-none"
              placeholder="Deteksi otomatis"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
