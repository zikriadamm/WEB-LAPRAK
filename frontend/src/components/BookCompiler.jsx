import React, { useState } from 'react';
import { 
  BookMarked, UploadCloud, Trash2, ArrowUp, ArrowDown, Download, 
  CheckCircle2, AlertCircle, FileText, 
  GraduationCap, RefreshCw, Layers
} from 'lucide-react';
import { inspectModuleDocx, compileAndDownloadBook } from '../services/api';

export default function BookCompiler({ initialStudentInfo = {} }) {
  const [modules, setModules] = useState([]);
  const [loadingInspect, setLoadingInspect] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [metadata, setMetadata] = useState({
    course_name: initialStudentInfo.course || 'Sistem Informasi Geografis',
    title: '',
    student_name: initialStudentInfo.name || 'MOH. YUSFI LAKHAFIDUN',
    student_nim: initialStudentInfo.nim || 'F5512520089',
    student_class: initialStudentInfo.class || 'Informatika C',
    institution: 'PROGRAM STUDI S1 TEKNIK INFORMATIKA\nJURUSAN TEKNOLOGI INFORMASI\nFAKULTAS TEKNIK\nUNIVERSITAS TADULAKO',
    academic_year: '2026',
    include_kata_pengantar: true,
    include_daftar_isi: true
  });

  const handleFileChange = async (e) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    setErrorMsg('');
    setSuccessMsg('');
    setLoadingInspect(true);

    const docxOnly = selectedFiles.filter(f => f.name.toLowerCase().endsWith('.docx'));
    if (docxOnly.length === 0) {
      setErrorMsg('Semua berkas yang diunggah harus berformat Word (.docx).');
      setLoadingInspect(false);
      return;
    }

    const oversized = docxOnly.some(f => f.size > 30 * 1024 * 1024);
    if (oversized) {
      setErrorMsg('Terdapat berkas Word yang melebihi batas ukuran maksimal (30 MB).');
      setLoadingInspect(false);
      return;
    }

    const newModules = [...modules];

    for (const file of docxOnly) {
      try {
        const info = await inspectModuleDocx(file);
        
        // Auto-fill metadata mahasiswa dari modul jika belum diisi
        setMetadata(prev => ({
          ...prev,
          student_name: prev.student_name || info.student_name || '',
          student_nim: prev.student_nim || info.student_nim || '',
          student_class: prev.student_class || info.student_class || '',
        }));

        newModules.push({
          id: Math.random().toString(36).substring(2, 9),
          file: file,
          filename: file.name,
          module_number: info.module_number || (newModules.length + 1),
          module_title: info.module_title || file.name.replace(/\.docx$/i, ''),
          bab2_count: info.bab2_count || 0,
          bab3_count: info.bab3_count || 0,
          bab4_count: info.bab4_count || 0,
          bab5_count: info.bab5_count || 0,
          bib_count: info.bib_count || 0
        });
      } catch (err) {
        console.error('Gagal membaca info docx:', err);
        // Tetap masukkan sebagai modul dengan fallback
        newModules.push({
          id: Math.random().toString(36).substring(2, 9),
          file: file,
          filename: file.name,
          module_number: newModules.length + 1,
          module_title: file.name.replace(/\.docx$/i, ''),
          bab2_count: '-',
          bab3_count: '-',
          bab4_count: '-',
          bab5_count: '-',
          bib_count: '-'
        });
      }
    }

    // Urutkan otomatis berdasarkan nomor modul
    newModules.sort((a, b) => {
      const numA = typeof a.module_number === 'number' ? a.module_number : 999;
      const numB = typeof b.module_number === 'number' ? b.module_number : 999;
      return numA - numB;
    });

    setModules(newModules);
    setLoadingInspect(false);
    // Reset file input
    e.target.value = '';
  };

  const updateModuleField = (id, field, value) => {
    setModules(prev => prev.map(m => {
      if (m.id === id) {
        return { ...m, [field]: value };
      }
      return m;
    }));
  };

  const handleRemoveModule = (id) => {
    setModules(modules.filter(m => m.id !== id));
  };

  const moveModule = (index, direction) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= modules.length) return;
    const updated = [...modules];
    const temp = updated[index];
    updated[index] = updated[targetIndex];
    updated[targetIndex] = temp;
    setModules(updated);
  };

  const handleCompile = async () => {
    if (modules.length === 0) {
      setErrorMsg('Harap unggah minimal 1 berkas modul .docx terlebih dahulu.');
      return;
    }

    setErrorMsg('');
    setSuccessMsg('');
    setCompiling(true);

    try {
      const filesToCompile = modules.map(m => m.file);
      const modulesMetadata = modules.map(m => ({
        filename: m.filename,
        module_number: m.module_number,
        module_title: m.module_title
      }));
      await compileAndDownloadBook(filesToCompile, metadata, modulesMetadata);
      setSuccessMsg('Pembukuan berhasil dikompilasi! Berkas Word terpadu telah diunduh ke komputer Anda.');
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menyatukan pembukuan.');
    } finally {
      setCompiling(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Neo-Brutalist Banner */}
      <div className="bg-[#FFE600] border-3 border-black rounded-2xl p-6 shadow-neo">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 bg-white border-3 border-black rounded-xl flex items-center justify-center shadow-neo-sm shrink-0">
              <BookMarked className="w-7 h-7 text-black" strokeWidth={2.5} />
            </div>
            <div>
              <div className="inline-block bg-[#FF5B99] text-white text-xs font-black px-2.5 py-0.5 border-2 border-black rounded-md shadow-neo-sm mb-1.5 uppercase">
                Model 1: Bab Terpadu (format.md)
              </div>
              <h2 className="text-2xl font-black tracking-tight">Kompilasi Pembukuan Laporan Akhir</h2>
              <p className="text-sm font-bold text-black/80 mt-1">
                Satukan seluruh berkas <code className="bg-white px-1.5 py-0.5 rounded border border-black font-mono">.docx</code> modul praktikum menjadi 1 buku laporan akhir dengan penomoran bab terpadu otomatis.
              </p>
            </div>
          </div>
          <div className="bg-white border-2 border-black rounded-xl px-4 py-2 font-mono text-xs font-bold shadow-neo-sm shrink-0">
            {modules.length} Modul Terpilih
          </div>
        </div>

        {/* Alur Bab Terpadu */}
        <div className="mt-5 pt-4 border-t-2 border-black/20 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center text-xs font-black">
          <div className="bg-white/80 border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            1. Sampul Buku
          </div>
          <div className="bg-white/80 border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            2. Kata Pengantar
          </div>
          <div className="bg-white/80 border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            3. Daftar Isi
          </div>
          <div className="bg-[#A3E7FC] border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            4. Bab II (2.1.1..N)
          </div>
          <div className="bg-[#E2F87B] border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            5. Bab III (3.1.1..N)
          </div>
          <div className="bg-[#FF90E8] border-2 border-black rounded-lg py-1.5 px-1 shadow-neo-sm">
            6. Bab IV & V
          </div>
        </div>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="bg-[#FF6B6B] border-3 border-black rounded-xl p-4 shadow-neo flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-white shrink-0 mt-0.5" strokeWidth={2.5} />
          <div>
            <h4 className="font-black text-white text-base">Terjadi Kesalahan</h4>
            <p className="text-sm font-bold text-white/95 mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="bg-[#38EF7D] border-3 border-black rounded-xl p-4 shadow-neo flex items-start gap-3">
          <CheckCircle2 className="w-6 h-6 text-black shrink-0 mt-0.5" strokeWidth={2.5} />
          <div>
            <h4 className="font-black text-black text-base">Berhasil Disatukan!</h4>
            <p className="text-sm font-bold text-black/90 mt-0.5">{successMsg}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Kolom Kiri: Upload & Daftar Modul (7 Kolom) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Dropzone Upload */}
          <div className="bg-white border-3 border-black rounded-2xl p-6 shadow-neo text-center relative hover:bg-[#FFFDF0] transition-colors">
            <input 
              type="file" 
              multiple 
              accept=".docx"
              onChange={handleFileChange}
              disabled={loadingInspect || compiling}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="w-16 h-16 bg-[#A3E7FC] border-3 border-black rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-neo-sm">
              <UploadCloud className="w-8 h-8 text-black" strokeWidth={2.5} />
            </div>
            <h3 className="text-lg font-black tracking-tight">Pilih atau Seret Berkas .docx Modul</h3>
            <p className="text-xs font-bold text-gray-600 mt-1 max-w-md mx-auto">
              Unggah sekaligus beberapa berkas Word modul praktikum (misal: Modul 1 sampai Modul 8) yang sudah selesai dikerjakan.
            </p>
            <div className="mt-4 inline-flex items-center gap-2 bg-[#E2F87B] border-2 border-black px-4 py-2 rounded-xl text-xs font-black shadow-neo-sm">
              <FileText className="w-4 h-4 text-black" strokeWidth={2.5} />
              Pilih Berkas Word (.docx)
            </div>
          </div>

          {/* Loading Indicator */}
          {loadingInspect && (
            <div className="bg-[#FFFDF9] border-3 border-black rounded-xl p-4 shadow-neo flex items-center justify-center gap-3">
              <RefreshCw className="w-5 h-5 text-black animate-spin" strokeWidth={2.5} />
              <span className="font-bold text-sm">Membedah struktur modul Word yang diunggah...</span>
            </div>
          )}

          {/* Module List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-black text-lg tracking-tight flex items-center gap-2">
                <Layers className="w-5 h-5 text-black" strokeWidth={2.5} />
                Urutan Modul yang Akan Digabung
              </h3>
              <span className="text-xs font-bold bg-white border-2 border-black px-2.5 py-1 rounded-lg shadow-neo-sm">
                {modules.length} Berkas
              </span>
            </div>

            {modules.length === 0 ? (
              <div className="bg-white border-3 border-dashed border-black/40 rounded-2xl p-8 text-center">
                <p className="text-sm font-bold text-gray-500">
                  Belum ada berkas modul yang dipilih. Unggah berkas .docx di atas untuk memulai pembukuan.
                </p>
              </div>
            ) : (
              modules.map((mod, idx) => (
                <div 
                  key={mod.id} 
                  className="bg-white border-3 border-black rounded-xl p-4 shadow-neo-sm flex items-center justify-between gap-3 hover:translate-x-0.5 transition-transform"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="flex flex-col items-center shrink-0">
                      <span className="text-[9px] font-black uppercase text-gray-500">No.</span>
                      <input 
                        type="number"
                        min="1"
                        max="99"
                        value={mod.module_number}
                        onChange={(e) => updateModuleField(mod.id, 'module_number', parseInt(e.target.value) || 1)}
                        className="w-11 h-8 bg-[#FFE600] border-2 border-black rounded-lg font-black text-center text-xs shadow-neo-sm focus:outline-none"
                        title="Ubah nomor modul"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="bg-[#E2F87B] border border-black text-[10px] font-black px-1.5 py-0.5 rounded">
                          Modul {mod.module_number}
                        </span>
                        <span className="text-xs font-bold text-gray-500 truncate max-w-[220px]" title={mod.filename}>
                          {mod.filename}
                        </span>
                      </div>
                      <input 
                        type="text"
                        value={mod.module_title}
                        onChange={(e) => updateModuleField(mod.id, 'module_title', e.target.value)}
                        className="w-full bg-[#FFFDF9] border border-black rounded-md px-2 py-0.5 text-xs font-black text-black outline-none focus:ring-1 focus:ring-[#FFE600]"
                        placeholder="Judul Modul"
                        title="Klik untuk menyunting judul modul"
                      />
                      <div className="flex items-center gap-3 text-[11px] font-bold text-gray-600 mt-1">
                        <span>Bab II: {mod.bab2_count}</span>
                        <span>•</span>
                        <span>Bab III: {mod.bab3_count}</span>
                        <span>•</span>
                        <span>Bab IV: {mod.bab4_count}</span>
                        <span>•</span>
                        <span>Dafpus: {mod.bib_count}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions (Reorder & Delete) */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button 
                      onClick={() => moveModule(idx, -1)}
                      disabled={idx === 0}
                      className="p-1.5 bg-gray-100 hover:bg-[#E2F87B] border-2 border-black rounded-lg disabled:opacity-30 disabled:hover:bg-gray-100 transition-colors"
                      title="Geser ke Atas"
                    >
                      <ArrowUp className="w-4 h-4 text-black" strokeWidth={2.5} />
                    </button>
                    <button 
                      onClick={() => moveModule(idx, 1)}
                      disabled={idx === modules.length - 1}
                      className="p-1.5 bg-gray-100 hover:bg-[#E2F87B] border-2 border-black rounded-lg disabled:opacity-30 disabled:hover:bg-gray-100 transition-colors"
                      title="Geser ke Bawah"
                    >
                      <ArrowDown className="w-4 h-4 text-black" strokeWidth={2.5} />
                    </button>
                    <button 
                      onClick={() => handleRemoveModule(mod.id)}
                      className="p-1.5 bg-gray-100 hover:bg-[#FF6B6B] hover:text-white border-2 border-black rounded-lg transition-colors ml-1"
                      title="Hapus Modul"
                    >
                      <Trash2 className="w-4 h-4" strokeWidth={2.5} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Kolom Kanan: Pengaturan Sampul & Aksi Kompilasi (5 Kolom) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border-3 border-black rounded-2xl p-5 shadow-neo space-y-4">
            <div className="flex items-center gap-2 border-b-2 border-black pb-3">
              <GraduationCap className="w-5 h-5 text-black" strokeWidth={2.5} />
              <h3 className="font-black text-base tracking-tight">Identitas & Sampul Pembukuan</h3>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-black uppercase mb-1">Mata Kuliah</label>
                <input 
                  type="text" 
                  value={metadata.course_name}
                  onChange={(e) => setMetadata({ ...metadata, course_name: e.target.value })}
                  className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600]"
                  placeholder="Contoh: Sistem Informasi Geografis"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-black uppercase mb-1">Nama Mahasiswa</label>
                  <input 
                    type="text" 
                    value={metadata.student_name}
                    onChange={(e) => setMetadata({ ...metadata, student_name: e.target.value })}
                    className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600]"
                    placeholder="Nama Lengkap"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black uppercase mb-1">NIM</label>
                  <input 
                    type="text" 
                    value={metadata.student_nim}
                    onChange={(e) => setMetadata({ ...metadata, student_nim: e.target.value })}
                    className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600]"
                    placeholder="F551..."
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-black uppercase mb-1">Kelas</label>
                  <input 
                    type="text" 
                    value={metadata.student_class}
                    onChange={(e) => setMetadata({ ...metadata, student_class: e.target.value })}
                    className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600]"
                    placeholder="Informatika C"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black uppercase mb-1">Tahun Akademik</label>
                  <input 
                    type="text" 
                    value={metadata.academic_year}
                    onChange={(e) => setMetadata({ ...metadata, academic_year: e.target.value })}
                    className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600]"
                    placeholder="2026"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-black uppercase mb-1">Institusi / Universitas</label>
                <textarea 
                  rows={3}
                  value={metadata.institution}
                  onChange={(e) => setMetadata({ ...metadata, institution: e.target.value })}
                  className="w-full bg-[#FFFDF9] border-2 border-black rounded-xl p-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-[#FFE600] font-sans resize-none"
                  placeholder="Program Studi, Jurusan, Fakultas, Universitas"
                />
              </div>

              {/* Opsi Halaman Tambahan */}
              <div className="pt-2 border-t-2 border-black/10 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input 
                    type="checkbox"
                    checked={metadata.include_kata_pengantar}
                    onChange={(e) => setMetadata({ ...metadata, include_kata_pengantar: e.target.checked })}
                    className="w-4 h-4 border-2 border-black rounded accent-black cursor-pointer"
                  />
                  <span className="text-xs font-bold">Sertakan Halaman Kata Pengantar</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input 
                    type="checkbox"
                    checked={metadata.include_daftar_isi}
                    onChange={(e) => setMetadata({ ...metadata, include_daftar_isi: e.target.checked })}
                    className="w-4 h-4 border-2 border-black rounded accent-black cursor-pointer"
                  />
                  <span className="text-xs font-bold">Sertakan Halaman Daftar Isi Otomatis (MS Word TOC)</span>
                </label>
              </div>
            </div>

            {/* Tombol Eksekusi Kompilasi */}
            <div className="pt-3 border-t-2 border-black">
              <button 
                onClick={handleCompile}
                disabled={modules.length === 0 || compiling}
                className="w-full bg-[#38EF7D] hover:bg-[#2DD36F] disabled:bg-gray-200 border-3 border-black rounded-xl p-4 font-black text-sm sm:text-base tracking-wide flex items-center justify-center gap-2 shadow-neo neo-btn transition-all cursor-pointer disabled:cursor-not-allowed"
              >
                {compiling ? (
                  <>
                    <RefreshCw className="w-5 h-5 text-black animate-spin" strokeWidth={2.5} />
                    Menyatukan Dokumen Pembukuan...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5 text-black" strokeWidth={2.5} />
                    SATUKAN & UNDUH PEMBUKUAN (.DOCX)
                  </>
                )}
              </button>
              <p className="text-[11px] font-bold text-center text-gray-500 mt-2">
                Format standar Word 4-4-3-3 cm dengan Navigation Pane & TOC terpadu.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
