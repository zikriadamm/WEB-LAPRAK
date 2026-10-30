import React from 'react';
import { Zap, BookOpen, Settings, Shield } from 'lucide-react';

export default function Header({ onOpenApiKey, onOpenGuide, onOpenAdmin, backendStatus }) {
  return (
    <header className="flex items-center justify-between bg-white border-3 border-black rounded-2xl p-4 shadow-neo">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-[#FFE600] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm">
          <Zap className="w-6 h-6 text-black fill-black" />
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tight leading-none">
            LAPRAK<span className="text-[#FF5B99]">.AI</span>
          </h1>
          <p className="text-xs font-bold text-gray-600 mt-1">Otomasi Word 4-4-3-3 Akademik</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <button 
          onClick={onOpenGuide}
          className="bg-[#E2F87B] border-2 border-black px-3 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm neo-btn shadow-neo-sm flex items-center gap-2"
        >
          <BookOpen className="w-4 h-4 text-black" strokeWidth={2.5} />
          <span className="hidden sm:inline">Standar Format</span> (4-4-3-3)
        </button>
        
        <button 
          onClick={onOpenApiKey}
          aria-label="Pengaturan Gemini API Key"
          className="bg-white border-2 border-black p-2.5 min-w-[44px] min-h-[44px] rounded-xl neo-btn shadow-neo-sm flex items-center justify-center gap-1.5 focus:outline-none focus-visible:ring-3 focus-visible:ring-black" 
          title="Pengaturan Gemini API Key"
        >
          <Settings className="w-5 h-5 text-black" strokeWidth={2.5} />
          {backendStatus?.has_env_key && (
            <span className="w-2.5 h-2.5 rounded-full bg-[#38EF7D] border border-black" title="API Key Aktif"></span>
          )}
        </button>

        <button 
          onClick={onOpenAdmin}
          aria-label="Panel Admin & Kuota"
          className="bg-white border-2 border-black p-2.5 min-w-[44px] min-h-[44px] rounded-xl neo-btn shadow-neo-sm flex items-center justify-center hover:bg-gray-50 focus:outline-none focus-visible:ring-3 focus-visible:ring-black" 
          title="Panel Admin & Kuota"
        >
          <Shield className="w-5 h-5 text-[#FF5B99]" strokeWidth={2.5} />
        </button>
      </div>
    </header>
  );
}
