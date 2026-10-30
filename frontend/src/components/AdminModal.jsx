import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, X, RefreshCw, Trash2, Database, Zap, Lock, User, KeyRound, 
  AlertTriangle, CheckCircle, LogOut
} from 'lucide-react';
import { 
  loginUser, logoutUser, getCurrentUser, changeUserPassword,
  getAdminStats, clearAdminCache, resetAdminLimits, cleanupAdminDisk 
} from '../services/api';

export default function AdminModal({ isOpen, onClose }) {
  const [token, setToken] = useState(() => sessionStorage.getItem('laprak_auth_token') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'password'

  // Form Login
  const [usernameInput, setUsernameInput] = useState('admin');
  const [passwordInput, setPasswordInput] = useState('');

  // Form Ganti Password
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Muat data stats jika token valid
  const loadData = async (activeAuthToken) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const meData = await getCurrentUser(activeAuthToken);
      setCurrentUser(meData.user);
      
      const statsData = await getAdminStats(activeAuthToken);
      setStats(statsData);
      
      sessionStorage.setItem('laprak_auth_token', activeAuthToken);
      setToken(activeAuthToken);
    } catch (err) {
      // Token tidak valid atau kedaluwarsa
      sessionStorage.removeItem('laprak_auth_token');
      setToken('');
      setCurrentUser(null);
      setErrorMsg(err.message || 'Sesi telah kedaluwarsa, silakan login kembali');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && token) {
      loadData(token);
    }
    if (!isOpen) {
      setErrorMsg('');
      setSuccessMsg('');
      setPasswordInput('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!usernameInput.trim() || !passwordInput) {
      setErrorMsg('Username dan kata sandi wajib diisi');
      return;
    }
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await loginUser(usernameInput.trim(), passwordInput);
      setToken(res.token);
      setCurrentUser(res.user);
      setPasswordInput('');
      await loadData(res.token);
    } catch (err) {
      setErrorMsg(err.message || 'Login gagal');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    if (token) {
      await logoutUser(token);
    }
    sessionStorage.removeItem('laprak_auth_token');
    setToken('');
    setCurrentUser(null);
    setStats(null);
    setActiveTab('dashboard');
    setSuccessMsg('Anda telah berhasil keluar');
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!oldPassword || !newPassword) {
      setErrorMsg('Semua kolom kata sandi wajib diisi');
      return;
    }
    if (newPassword.length < 6) {
      setErrorMsg('Kata sandi baru minimal 6 karakter');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Konfirmasi kata sandi baru tidak cocok');
      return;
    }

    setIsLoading(true);
    try {
      const res = await changeUserPassword(token, oldPassword, newPassword);
      setSuccessMsg(res.message || 'Kata sandi berhasil diubah');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setActiveTab('dashboard');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearCache = async () => {
    setIsLoading(true);
    try {
      const res = await clearAdminCache(token);
      setSuccessMsg(res.message);
      await loadData(token);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetLimits = async () => {
    setIsLoading(true);
    try {
      const res = await resetAdminLimits(token);
      setSuccessMsg(res.message);
      await loadData(token);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCleanupDisk = async () => {
    setIsLoading(true);
    try {
      const res = await cleanupAdminDisk(token);
      setSuccessMsg(res.message);
      await loadData(token);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isAuthenticated = !!token && !!currentUser;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white border-3 border-black rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-neo-lg space-y-6 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b-2 border-black/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#FF5B99] border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm">
              <ShieldCheck className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="font-black text-xl text-black">Admin Security & Auth</h3>
              <p className="text-xs font-bold text-gray-500">
                {isAuthenticated ? `Terautentikasi: ${currentUser.username} (${currentUser.role})` : 'Autentikasi Kriptografis Token Bearer'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            aria-label="Tutup jendela Admin"
            className="w-8 h-8 rounded-lg border-2 border-black flex items-center justify-center neo-btn hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
          >
            <X className="w-4 h-4 text-black" strokeWidth={3} />
          </button>
        </div>

        {/* Feedback Messages */}
        {errorMsg && (
          <div className="bg-[#FF5B99]/15 border-2 border-[#FF5B99] rounded-xl p-3 flex items-center gap-2 text-xs font-bold text-red-800">
            <AlertTriangle className="w-4 h-4 shrink-0 text-[#FF5B99]" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="bg-[#38EF7D]/20 border-2 border-[#38EF7D] rounded-xl p-3 flex items-center gap-2 text-xs font-bold text-green-900">
            <CheckCircle className="w-4 h-4 shrink-0 text-green-700" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* 1. Form Login (Jika Belum Terautentikasi) */}
        {!isAuthenticated ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                  Username
                </label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="admin"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    className="w-full bg-[#FBF9F4] border-2 border-black p-3.5 pl-10 rounded-xl font-bold text-sm focus:outline-none focus:ring-2 focus:ring-[#FF5B99] shadow-neo-sm"
                  />
                  <User className="w-4 h-4 text-gray-400 absolute left-3.5 top-4" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                  Kata Sandi
                </label>
                <div className="relative">
                  <input
                    type="password"
                    placeholder="Masukkan kata sandi admin..."
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    className="w-full bg-[#FBF9F4] border-2 border-black p-3.5 pl-10 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#FF5B99] shadow-neo-sm"
                  />
                  <KeyRound className="w-4 h-4 text-gray-400 absolute left-3.5 top-4" />
                </div>
                <p className="text-[11px] font-bold text-gray-500 mt-1">
                  Kredensial disimpan terenkripsi dengan algoritma <code className="bg-gray-200 px-1 py-0.5 rounded">scrypt</code> di database SQLite lokal.
                </p>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#FFE600] border-2 border-black py-3.5 rounded-xl font-black text-sm neo-btn shadow-neo flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Masuk...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" strokeWidth={2.5} /> Masuk dengan Token Bearer
                </>
              )}
            </button>
          </form>
        ) : (
          /* 2. Panel Admin Terautentikasi */
          <div className="space-y-6">
            
            {/* Navigasi Tab */}
            <div className="flex border-2 border-black rounded-xl p-1 bg-gray-100 gap-1">
              <button
                type="button"
                onClick={() => setActiveTab('dashboard')}
                className={`flex-1 py-2 rounded-lg text-xs font-black transition-all ${
                  activeTab === 'dashboard' 
                    ? 'bg-white border-2 border-black shadow-neo-sm text-black' 
                    : 'text-gray-600 hover:text-black'
                }`}
              >
                Dashboard Metrik
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('password')}
                className={`flex-1 py-2 rounded-lg text-xs font-black transition-all ${
                  activeTab === 'password' 
                    ? 'bg-white border-2 border-black shadow-neo-sm text-black' 
                    : 'text-gray-600 hover:text-black'
                }`}
              >
                Ganti Kata Sandi
              </button>
            </div>

            {activeTab === 'dashboard' ? (
              <>
                {/* Grid Kartu Metrik */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Kartu AI Provider */}
                  <div className="bg-[#FAF8F5] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black uppercase text-gray-600">
                      <Zap className="w-4 h-4 text-[#FFE600] fill-black" /> Status AI Server
                    </div>
                    <div className="space-y-1 text-xs font-bold">
                      <div className="flex justify-between items-center">
                        <span>Gemini AI:</span>
                        <span className={stats?.has_gemini_key ? "text-green-600" : "text-red-500"}>
                          {stats?.has_gemini_key ? "🟢 Terpasang" : "🔴 Kosong"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Groq LPU (Backup):</span>
                        <span className={stats?.has_groq_key ? "text-green-600" : "text-red-500"}>
                          {stats?.has_groq_key ? "🟢 Terpasang" : "🔴 Kosong"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Kartu Cache */}
                  <div className="bg-[#FAF8F5] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black uppercase text-gray-600">
                      <Database className="w-4 h-4 text-[#9D71FD]" /> Cache Dokumen (SHA-256)
                    </div>
                    <div className="text-xl font-black text-black">
                      {stats?.cache?.count || 0} <span className="text-xs font-bold text-gray-500">berkas ({stats?.cache?.size_kb || 0} KB)</span>
                    </div>
                    <p className="text-[11px] font-bold text-gray-500">Ekstraksi instan tanpa panggil AI.</p>
                  </div>

                  {/* Kartu Rate Limit */}
                  <div className="bg-[#FAF8F5] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black uppercase text-gray-600">
                      <ShieldCheck className="w-4 h-4 text-[#38EF7D]" /> Proteksi Rate Limit
                    </div>
                    <div className="text-xl font-black text-black">
                      {Object.keys(stats?.rate_limited_active_ips || {}).length}{' '}
                      <span className="text-xs font-bold text-gray-500">IP aktif di window</span>
                    </div>
                    <p className="text-[11px] font-bold text-gray-500">
                      Maks {stats?.rate_limit_policy?.max_requests || 5} req / {((stats?.rate_limit_policy?.window_seconds || 600) / 60)} menit
                    </p>
                  </div>

                  {/* Kartu Berkas Temporer */}
                  <div className="bg-[#FAF8F5] border-2 border-black p-4 rounded-2xl shadow-neo-sm space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black uppercase text-gray-600">
                      <Trash2 className="w-4 h-4 text-[#FF5B99]" /> Berkas Upload
                    </div>
                    <div className="text-xl font-black text-black">
                      {stats?.uploads?.file_count || 0}{' '}
                      <span className="text-xs font-bold text-gray-500">berkas ({stats?.uploads?.size_kb || 0} KB)</span>
                    </div>
                    <p className="text-[11px] font-bold text-gray-500">Dibersihkan otomatis berkala.</p>
                  </div>
                </div>

                {/* Tombol Aksi Kontrol */}
                <div className="space-y-2 pt-2">
                  <h4 className="text-xs font-black uppercase text-gray-500 tracking-wider">Tindakan Admin</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <button
                      onClick={handleClearCache}
                      disabled={isLoading}
                      className="bg-[#FFE600] border-2 border-black py-2.5 px-3 rounded-xl font-bold text-xs neo-btn shadow-neo-sm flex items-center justify-center gap-1.5"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Hapus Cache
                    </button>
                    <button
                      onClick={handleResetLimits}
                      disabled={isLoading}
                      className="bg-[#E2F87B] border-2 border-black py-2.5 px-3 rounded-xl font-bold text-xs neo-btn shadow-neo-sm flex items-center justify-center gap-1.5"
                    >
                      <RefreshCw className="w-3.5 h-3.5" /> Reset Limit IP
                    </button>
                    <button
                      onClick={handleCleanupDisk}
                      disabled={isLoading}
                      className="bg-[#FF8A65] border-2 border-black py-2.5 px-3 rounded-xl font-bold text-xs neo-btn shadow-neo-sm flex items-center justify-center gap-1.5"
                    >
                      <Database className="w-3.5 h-3.5" /> Bersihkan Disk
                    </button>
                  </div>
                </div>
              </>
            ) : (
              /* Tab Form Ganti Password */
              <form onSubmit={handleChangePassword} className="space-y-3">
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                    Kata Sandi Lama
                  </label>
                  <input
                    type="password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full bg-[#FBF9F4] border-2 border-black p-3 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#FF5B99] shadow-neo-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                    Kata Sandi Baru (Min. 6 Karakter)
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-[#FBF9F4] border-2 border-black p-3 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#FF5B99] shadow-neo-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                    Konfirmasi Kata Sandi Baru
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full bg-[#FBF9F4] border-2 border-black p-3 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#FF5B99] shadow-neo-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-[#FFE600] border-2 border-black py-3 rounded-xl font-black text-sm neo-btn shadow-neo mt-2 flex items-center justify-center gap-2"
                >
                  <KeyRound className="w-4 h-4" /> Simpan Kata Sandi Baru
                </button>
              </form>
            )}

            {/* Footer Kontrol */}
            <div className="flex items-center justify-between border-t-2 border-black/10 pt-4">
              <button
                onClick={() => loadData(token)}
                disabled={isLoading}
                className="text-xs font-bold text-gray-600 hover:text-black flex items-center gap-1 underline"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} /> Refresh Data
              </button>
              <button
                onClick={handleLogout}
                className="bg-gray-100 hover:bg-red-50 hover:text-red-600 border-2 border-black px-4 py-2 rounded-xl text-xs font-black neo-btn flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5" /> Logout
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
