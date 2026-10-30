import React, { useState, useEffect } from 'react';
import { Key, X, Check, ExternalLink } from 'lucide-react';

export default function ApiKeyModal({ isOpen, onClose, onSave, currentKey, serverHasQuota }) {
  const [keyInput, setKeyInput] = useState('');

  useEffect(() => {
    setKeyInput(currentKey || '');
  }, [currentKey, isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(keyInput.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white border-3 border-black rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-neo-lg space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#FFE600] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm">
              <Key className="w-5 h-5 text-black" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="font-black text-xl">Google Gemini API Key</h3>
              <p className="text-xs font-bold text-gray-500">Tersimpan aman di peramban lokal Anda</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            aria-label="Tutup jendela API Key"
            className="w-8 h-8 rounded-lg border-2 border-black flex items-center justify-center neo-btn hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
          >
            <X className="w-4 h-4 text-black" strokeWidth={3} />
          </button>
        </div>

        {serverHasQuota && (
          <div className="bg-[#E2F87B]/40 border-2 border-black rounded-xl p-3 flex items-start gap-2.5 text-xs font-bold text-gray-800">
            <span className="w-2.5 h-2.5 rounded-full bg-[#38EF7D] border border-black mt-0.5 shrink-0"></span>
            <span>Server telah menyediakan kuota AI gratis. Pengisian API Key pribadi bersifat opsional (dianjurkan jika Anda ingin memproses dokumen tanpa antrean).</span>
          </div>
        )}

        <div className="space-y-3">
          <label className="block text-xs font-black uppercase tracking-wider text-gray-600">
            API Key
          </label>
          <input
            type="password"
            placeholder="AIzaSy..."
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            className="w-full bg-[#FBF9F4] border-2 border-black p-3.5 rounded-xl font-bold text-sm focus:outline-none focus:ring-2 focus:ring-[#FFE600] shadow-neo-sm"
          />
          <div className="flex items-center justify-between text-xs font-bold text-gray-500 pt-1">
            <span>Gratis dari Google AI Studio</span>
            <a 
              href="https://aistudio.google.com/" 
              target="_blank" 
              rel="noreferrer"
              className="text-[#9D71FD] underline flex items-center gap-1 hover:text-black"
            >
              Dapatkan Key <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-100 border-2 border-black py-3 rounded-xl font-black text-sm neo-btn shadow-neo-sm"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            className="flex-1 bg-[#FFE600] border-2 border-black py-3 rounded-xl font-black text-sm neo-btn shadow-neo flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4" strokeWidth={3} /> Simpan Key
          </button>
        </div>
      </div>
    </div>
  );
}
