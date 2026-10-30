import React, { useState } from 'react';
import { 
  X, Check, Upload, Image as ImageIcon, Trash2, Plus, 
  FileText, BookOpen, Layers, BarChart3, Flag, Bookmark, RefreshCw 
} from 'lucide-react';
import { uploadScreenshot } from '../services/api';

export default function EditorModal({ 
  isOpen, 
  onClose, 
  activeTab, 
  setActiveTab, 
  reportData, 
  setReportData, 
  imagesMap, 
  setImagesMap,
  onResetVerbatim,
  onError 
}) {
  const [uploadingId, setUploadingId] = useState(null);

  if (!isOpen || !reportData) return null;

  const handleImageUpload = async (e, placeholderId) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setUploadingId(placeholderId);
    try {
      const res = await uploadScreenshot(file, placeholderId);
      // Simpan path ke imagesMap
      setImagesMap(prev => ({
        ...prev,
        [placeholderId]: res.image_path,
        // Buat preview data URL di browser
        [`${placeholderId}_preview`]: URL.createObjectURL(file)
      }));
    } catch (err) {
      if (onError) {
        onError(`Gagal mengunggah screenshot: ${err.message}`);
      }
    } finally {
      setUploadingId(null);
    }
  };

  const removeImage = (placeholderId) => {
    setImagesMap(prev => {
      const next = { ...prev };
      delete next[placeholderId];
      delete next[`${placeholderId}_preview`];
      return next;
    });
  };

  const tabs = [
    { id: 'cover', label: 'Cover', icon: FileText, color: 'bg-gray-300' },
    { id: 'bab2', label: 'Bab II', icon: BookOpen, color: 'bg-[#38EF7D]' },
    { id: 'bab3', label: 'Bab III', icon: Layers, color: 'bg-[#FFE600]' },
    { id: 'bab4', label: 'Bab IV', icon: BarChart3, color: 'bg-[#FF5B99]' },
    { id: 'bab5', label: 'Bab V', icon: Flag, color: 'bg-[#9D71FD]' },
    { id: 'pustaka', label: 'Pustaka', icon: Bookmark, color: 'bg-[#FF8A65]' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm">
      <div className="bg-white border-3 border-black rounded-3xl max-w-4xl w-full h-[90vh] flex flex-col shadow-neo-lg overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 sm:p-6 border-b-3 border-black bg-[#FBF9F4] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#FFE600] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm font-black">
              ✏️
            </div>
            <div>
              <h3 className="font-black text-xl tracking-tight leading-none">
                Editor Laporan Praktikum
              </h3>
              <p className="text-xs font-bold text-gray-500 mt-1">
                Modul {reportData.module_number}: {reportData.module_title}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onResetVerbatim && (
              <button
                type="button"
                onClick={() => onResetVerbatim(activeTab)}
                title="Kembalikan teks bab ini ke draf asli asdos"
                aria-label="Kembalikan teks bab ini ke draf asli asdos"
                className="text-xs font-bold text-gray-700 bg-white hover:bg-gray-100 border-2 border-black px-3 py-2 rounded-xl neo-btn shadow-neo-sm flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
              >
                <RefreshCw className="w-3.5 h-3.5 text-black" strokeWidth={2.5} />
                <span className="hidden sm:inline">Reset ke Asli Asdos</span>
              </button>
            )}

            <button
              onClick={onClose}
              aria-label="Tutup jendela editor"
              className="w-10 h-10 rounded-xl border-2 border-black bg-white flex items-center justify-center neo-btn hover:bg-gray-100 shadow-neo-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
            >
              <X className="w-5 h-5 text-black" strokeWidth={3} />
            </button>
          </div>
        </div>

        {/* Tab Bar (Folder Tabs Style) */}
        <div className="flex gap-1.5 px-4 sm:px-6 pt-3 bg-[#F3EFE6] border-b-2 border-black overflow-x-auto select-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-t-xl font-black text-xs transition-all border-t-2 border-x-2 border-black ${
                  isActive 
                    ? 'bg-white translate-y-[2px] shadow-none' 
                    : `${tab.color} text-black opacity-80 hover:opacity-100`
                }`}
              >
                <Icon className="w-3.5 h-3.5" strokeWidth={2.5} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-6">

          {/* TAB 1: COVER */}
          {activeTab === 'cover' && (
            <div className="space-y-4 max-w-xl mx-auto">
              <div className="bg-[#FFFDF9] border-2 border-black p-4 rounded-2xl shadow-neo-sm">
                <p className="text-xs font-bold text-gray-500 mb-2">Teks Halaman Sampul (Tengah Halaman)</p>
                <div className="space-y-3 font-bold text-sm">
                  <div>
                    <label className="text-[10px] text-gray-400 uppercase">Header Judul Modul</label>
                    <textarea
                      value={reportData.header_title || `MODUL PRAKTIKUM ${reportData.module_number}\n(${reportData.module_title?.toUpperCase()})`}
                      onChange={(e) => setReportData({ ...reportData, header_title: e.target.value })}
                      rows={2}
                      className="w-full bg-white border-2 border-black p-2.5 rounded-xl font-black text-center text-sm"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                    <div>
                      <label className="text-[10px] text-gray-400 uppercase">Nama</label>
                      <input
                        type="text"
                        value={reportData.student_name}
                        onChange={(e) => setReportData({ ...reportData, student_name: e.target.value })}
                        className="w-full bg-white border-2 border-black p-2 rounded-xl text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-400 uppercase">NIM</label>
                      <input
                        type="text"
                        value={reportData.student_nim}
                        onChange={(e) => setReportData({ ...reportData, student_nim: e.target.value })}
                        className="w-full bg-white border-2 border-black p-2 rounded-xl text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-400 uppercase">Kelas</label>
                      <input
                        type="text"
                        value={reportData.student_class}
                        onChange={(e) => setReportData({ ...reportData, student_class: e.target.value })}
                        className="w-full bg-white border-2 border-black p-2 rounded-xl text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: BAB II LANDASAN TEORI */}
          {activeTab === 'bab2' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-[#E2F87B] border-2 border-black p-3 rounded-xl shadow-neo-sm">
                <span className="text-xs font-black">
                  Sub-bab: 2.1.{reportData.module_number} {reportData.bab2?.subbab_title || reportData.module_title}
                </span>
                <span className="bg-white border border-black px-2 py-0.5 rounded text-[11px] font-black">
                  Full-Page Mode (Margin 4-4-3-3 cm)
                </span>
              </div>

              <div className="space-y-3">
                {reportData.bab2?.content?.map((item, idx) => (
                  <div key={idx} className="bg-white border-2 border-black p-3.5 rounded-2xl shadow-neo-sm space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-bold text-gray-500">
                      <span>{item.type === 'list' ? `Butir Daftar (${item.prefix})` : `Paragraf ${idx + 1}`}</span>
                      <span className="text-gray-400">~{Math.round((item.text?.length || 0) / 60) + 1} baris</span>
                    </div>
                    <textarea
                      value={item.text}
                      onChange={(e) => {
                        const newContent = [...reportData.bab2.content];
                        newContent[idx] = { ...item, text: e.target.value };
                        setReportData({
                          ...reportData,
                          bab2: { ...reportData.bab2, content: newContent }
                        });
                      }}
                      rows={item.type === 'list' ? 2 : 4}
                      className="w-full bg-[#FBF9F4] border border-black p-2.5 rounded-xl font-medium text-xs leading-relaxed focus:bg-white"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: BAB III LANGKAH KERJA */}
          {activeTab === 'bab3' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-[#FFE600] border-2 border-black p-3 rounded-xl shadow-neo-sm">
                <span className="text-xs font-black">
                  Sub-bab: 3.1.{reportData.module_number} {reportData.bab3?.subbab_title || reportData.module_title}
                </span>
                <span className="bg-white border border-black px-2 py-0.5 rounded text-[11px] font-black">
                  Verbatim Asdos + Sisip Screenshot
                </span>
              </div>

              <div className="space-y-3">
                {reportData.bab3?.content?.map((item, idx) => {
                  const placeholderId = item.id || `bab3_ph_${idx}`;
                  const hasImage = imagesMap[placeholderId] || imagesMap[item.text];
                  const previewUrl = imagesMap[`${placeholderId}_preview`];

                  if (item.type === 'placeholder') {
                    return (
                      <div key={idx} className="bg-[#FFF8E6] border-2 border-dashed border-black p-4 rounded-2xl shadow-neo-sm space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-black text-gray-700 flex items-center gap-1.5">
                            <ImageIcon className="w-4 h-4 text-[#FF5B99]" /> Slot Foto: {item.text}
                          </span>
                          {hasImage && (
                            <button
                              onClick={() => removeImage(placeholderId)}
                              className="text-red-600 hover:text-black font-bold text-xs flex items-center gap-1"
                            >
                              <Trash2 className="w-3.5 h-3.5" /> Hapus Foto
                            </button>
                          )}
                        </div>

                        {hasImage ? (
                          <div className="space-y-2">
                            {previewUrl && (
                              <img 
                                src={previewUrl} 
                                alt="Screenshot Praktikum" 
                                className="max-h-48 rounded-xl border-2 border-black object-contain bg-white mx-auto shadow-neo-sm"
                              />
                            )}
                            <p className="text-[11px] font-bold text-green-700 text-center">
                              ✓ Foto screenshot tersimpan dan siap disisipkan ke Word
                            </p>
                          </div>
                        ) : (
                          <label className="block bg-white border-2 border-black p-4 rounded-xl text-center cursor-pointer neo-btn shadow-neo-sm hover:bg-gray-50">
                            <input
                              type="file"
                              accept="image/*"
                              className="hidden"
                              onChange={(e) => handleImageUpload(e, placeholderId)}
                            />
                            <div className="flex items-center justify-center gap-2 font-black text-xs">
                              <Upload className="w-4 h-4" />
                              <span>{uploadingId === placeholderId ? 'Mengunggah...' : 'Upload Screenshot Praktikum Asli'}</span>
                            </div>
                            <p className="text-[10px] text-gray-400 font-bold mt-1">
                              (Jika tidak diunggah, otomatis tetap mempertahankan teks placeholder abu-abu)
                            </p>
                          </label>
                        )}
                      </div>
                    );
                  }

                  return (
                    <div key={idx} className="bg-white border-2 border-black p-3 rounded-2xl shadow-neo-sm flex items-start gap-2">
                      <span className="font-black text-xs text-[#9D71FD] min-w-[24px]">
                        {item.prefix || '•'}
                      </span>
                      <textarea
                        value={item.text}
                        onChange={(e) => {
                          const newContent = [...reportData.bab3.content];
                          newContent[idx] = { ...item, text: e.target.value };
                          setReportData({
                            ...reportData,
                            bab3: { ...reportData.bab3, content: newContent }
                          });
                        }}
                        rows={1}
                        className="w-full bg-transparent font-medium text-xs leading-relaxed focus:outline-none"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: BAB IV HASIL DAN PEMBAHASAN */}
          {activeTab === 'bab4' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-[#FF5B99] text-white border-2 border-black p-3 rounded-xl shadow-neo-sm">
                <span className="text-xs font-black">
                  Sub-bab: 4.1.{reportData.module_number} {reportData.bab4?.subbab_title || reportData.module_title}
                </span>
                <span className="bg-white text-black border border-black px-2 py-0.5 rounded text-[11px] font-black">
                  Dinamis Sesuai Modul Asdos
                </span>
              </div>

              <div className="space-y-4">
                {reportData.bab4?.content?.map((item, idx) => {
                  const placeholderId = item.id || `bab4_ph_${idx}`;
                  const hasImage = imagesMap[placeholderId] || imagesMap[item.text];
                  const previewUrl = imagesMap[`${placeholderId}_preview`];

                  if (item.type === 'placeholder') {
                    return (
                      <div key={idx} className="bg-[#FFF0F5] border-2 border-dashed border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-black text-gray-700">Slot Bukti Luaran: {item.text}</span>
                          {hasImage && (
                            <button
                              onClick={() => removeImage(placeholderId)}
                              className="text-red-600 hover:text-black font-bold text-xs flex items-center gap-1"
                            >
                              <Trash2 className="w-3.5 h-3.5" /> Hapus
                            </button>
                          )}
                        </div>

                        {hasImage ? (
                          <div className="space-y-2">
                            {previewUrl && (
                              <img 
                                src={previewUrl} 
                                alt="Luaran Praktikum" 
                                className="max-h-48 rounded-xl border-2 border-black object-contain bg-white mx-auto shadow-neo-sm"
                              />
                            )}
                            <p className="text-[11px] font-bold text-green-700 text-center">✓ Foto luaran tersimpan</p>
                          </div>
                        ) : (
                          <label className="block bg-white border-2 border-black p-3.5 rounded-xl text-center cursor-pointer neo-btn shadow-neo-sm">
                            <input
                              type="file"
                              accept="image/*"
                              className="hidden"
                              onChange={(e) => handleImageUpload(e, placeholderId)}
                            />
                            <div className="flex items-center justify-center gap-2 font-black text-xs">
                              <Upload className="w-4 h-4" />
                              <span>{uploadingId === placeholderId ? 'Mengunggah...' : 'Upload Foto Hasil / Screenshot Lembar Kerja'}</span>
                            </div>
                          </label>
                        )}
                      </div>
                    );
                  }

                  return (
                    <div key={idx} className="bg-white border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                      <label className="text-[11px] font-black text-gray-500 uppercase">
                        {item.type === 'list' ? `Poin Hasil (${item.prefix || idx + 1})` : 'Ulasan / Pembahasan Teknis'}
                      </label>
                      <textarea
                        value={item.text}
                        onChange={(e) => {
                          const newContent = [...reportData.bab4.content];
                          newContent[idx] = { ...item, text: e.target.value };
                          setReportData({
                            ...reportData,
                            bab4: { ...reportData.bab4, content: newContent }
                          });
                        }}
                        rows={item.type === 'list' ? 2 : 5}
                        className="w-full bg-[#FBF9F4] border border-black p-3 rounded-xl font-medium text-xs leading-relaxed focus:bg-white"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 5: BAB V PENUTUP */}
          {activeTab === 'bab5' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-[#9D71FD] text-white border-2 border-black p-3 rounded-xl shadow-neo-sm">
                <span className="text-xs font-black">
                  Sub-bab: 5.1.{reportData.module_number} {reportData.bab5?.current_title || reportData.module_title}
                </span>
                <span className="bg-white text-black border border-black px-2 py-0.5 rounded text-[11px] font-black">
                  Hanya Modul Terkait (Tanpa Parent Header)
                </span>
              </div>

              <div className="bg-white border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                <label className="text-xs font-black text-gray-600 block">
                  Narasi Kesimpulan Komprehensif
                </label>
                <textarea
                  value={reportData.bab5?.current_conclusion || ''}
                  onChange={(e) => setReportData({
                    ...reportData,
                    bab5: { ...reportData.bab5, current_conclusion: e.target.value }
                  })}
                  rows={8}
                  className="w-full bg-[#FBF9F4] border border-black p-3.5 rounded-xl font-medium text-xs leading-relaxed focus:bg-white"
                  placeholder="Praktikum ini menyimpulkan bahwa..."
                />
              </div>
            </div>
          )}

          {/* TAB 6: DAFTAR PUSTAKA */}
          {activeTab === 'pustaka' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-[#FF8A65] border-2 border-black p-3 rounded-xl shadow-neo-sm">
                <span className="text-xs font-black">
                  Format APA 7th Edition (Hanging Indent 1,27 cm)
                </span>
                <span className="bg-white border border-black px-2 py-0.5 rounded text-[11px] font-black">
                  Open-Access Free &ge; 2020
                </span>
              </div>

              <div className="space-y-3">
                {reportData.daftar_pustaka?.map((ref, idx) => (
                  <div key={idx} className="bg-white border-2 border-black p-3.5 rounded-2xl shadow-neo-sm flex items-start gap-2">
                    <span className="font-black text-xs text-gray-400 mt-2">[{idx + 1}]</span>
                    <textarea
                      value={typeof ref === 'string' ? ref : `${ref.author} (${ref.year}). ${ref.title}. *${ref.source}*. ${ref.url}`}
                      onChange={(e) => {
                        const newRefs = [...reportData.daftar_pustaka];
                        newRefs[idx] = e.target.value;
                        setReportData({ ...reportData, daftar_pustaka: newRefs });
                      }}
                      rows={2}
                      className="w-full bg-[#FBF9F4] border border-black p-2 rounded-xl font-medium text-xs focus:bg-white"
                    />
                    <button
                      onClick={() => {
                        const newRefs = reportData.daftar_pustaka.filter((_, i) => i !== idx);
                        setReportData({ ...reportData, daftar_pustaka: newRefs });
                      }}
                      className="p-2 text-red-500 hover:text-black"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}

                <button
                  onClick={() => {
                    const newRefs = [...(reportData.daftar_pustaka || []), 'Penulis, A. B. (2022). Judul Artikel. *Nama Jurnal*, 1(1), 1-10. https://doi.org/...'];
                    setReportData({ ...reportData, daftar_pustaka: newRefs });
                  }}
                  className="w-full bg-white border-2 border-dashed border-black py-3 rounded-xl font-black text-xs flex items-center justify-center gap-1.5 hover:bg-gray-50 neo-btn shadow-neo-sm"
                >
                  <Plus className="w-4 h-4" /> Tambah Referensi
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-6 border-t-3 border-black bg-white flex items-center justify-between">
          <p className="text-xs font-bold text-gray-500">
            Perubahan otomatis tersimpan ke draf laporan.
          </p>
          <button
            onClick={onClose}
            className="bg-[#FFE600] border-2 border-black px-6 py-2.5 rounded-xl font-black text-sm neo-btn shadow-neo flex items-center gap-2"
          >
            <Check className="w-4 h-4" strokeWidth={3} /> Selesai Mengedit
          </button>
        </div>

      </div>
    </div>
  );
}
