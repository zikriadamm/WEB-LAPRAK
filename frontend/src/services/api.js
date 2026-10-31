
async function parseJsonResponse(res, fallbackErrMsg) {
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error('Server backend belum aktif atau belum terhubung di cloud. Pastikan backend sudah running.');
  }
  try {
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || fallbackErrMsg);
    }
    return data;
  } catch (err) {
    if (err.message.includes('Server backend')) throw err;
    throw new Error('Gagal memproses data dari backend (Respons tidak valid).');
  }
}
/**
 * api.js
 * Layanan komunikasi frontend ke backend Flask REST API.
 */

const RAW_API = import.meta.env.VITE_API_URL || '';
const API_BASE = RAW_API ? `${RAW_API.replace(/\/$/, '')}/api` : '/api';

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return await res.json();
  } catch (err) {
    console.error('Backend offline:', err);
    return { status: 'offline', error: err.message };
  }
}

export async function extractReport(pdfFile, studentInfo, apiKey = '') {
  const formData = new FormData();
  formData.append('file', pdfFile);
  formData.append('name', studentInfo.name || '');
  formData.append('nim', studentInfo.nim || '');
  formData.append('class', studentInfo.class || '');
  formData.append('course', studentInfo.course || '');
  formData.append('module_number', studentInfo.module_number || '');
  if (apiKey) {
    formData.append('api_key', apiKey);
  }

  const res = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  return await parseJsonResponse(res, 'Gagal mengekstrak laporan dari PDF');
}

export async function uploadScreenshot(imageFile, placeholderId) {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('placeholder_id', placeholderId);

  const res = await fetch(`${API_BASE}/upload-image`, {
    method: 'POST',
    body: formData,
  });

  return await parseJsonResponse(res, 'Gagal mengunggah gambar');
}

export async function generateAndDownloadDocx(reportData, imagesMap = {}) {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      report_data: reportData,
      images_map: imagesMap,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.error || 'Gagal mengunduh dokumen Word');
  }

  // Unduh blob berkas .docx
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  
  const contentDisposition = res.headers.get('Content-Disposition');
  let filename = 'laporan_praktikum.docx';
  if (contentDisposition && contentDisposition.includes('filename=')) {
    filename = contentDisposition.split('filename=')[1].replace(/"/g, '').trim();
  } else {
    const nim = (reportData.student_nim || 'mahasiswa').toLowerCase();
    const mod = reportData.module_number || 1;
    filename = `${nim}_prak_gis_${mod}.docx`;
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function inspectModuleDocx(docxFile) {
  const formData = new FormData();
  formData.append('file', docxFile);

  const res = await fetch(`${API_BASE}/inspect-module-docx`, {
    method: 'POST',
    body: formData,
  });

  return await parseJsonResponse(res, 'Gagal membedah modul docx');
}

export async function compileAndDownloadBook(files, metadata = {}, modulesMetadata = []) {
  const formData = new FormData();
  files.forEach((f) => {
    formData.append('files', f);
  });

  if (modulesMetadata && modulesMetadata.length > 0) {
    formData.append('modules_metadata', JSON.stringify(modulesMetadata));
  }

  formData.append('course_name', metadata.course_name || 'Sistem Informasi Geografis');
  formData.append('title', metadata.title || '');
  formData.append('student_name', metadata.student_name || '');
  formData.append('student_nim', metadata.student_nim || '');
  formData.append('student_class', metadata.student_class || '');
  formData.append('academic_year', metadata.academic_year || '2026');
  formData.append('institution', metadata.institution || '');
  formData.append('include_kata_pengantar', metadata.include_kata_pengantar !== false ? 'true' : 'false');
  formData.append('include_daftar_isi', metadata.include_daftar_isi !== false ? 'true' : 'false');

  const res = await fetch(`${API_BASE}/compile-book`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.error || 'Gagal menyatukan pembukuan');
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;

  const contentDisposition = res.headers.get('Content-Disposition');
  let filename = 'pembukuan_laporan_akhir.docx';
  if (contentDisposition && contentDisposition.includes('filename=')) {
    filename = contentDisposition.split('filename=')[1].replace(/"/g, '').trim();
  } else {
    const nim = (metadata.student_nim || 'laprak').toLowerCase();
    const course = (metadata.course_name || 'prak').toLowerCase().replace(/\s+/g, '_');
    filename = `pembukuan_${nim}_${course}.docx`;
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ==========================================
// PROPER AUTHENTICATION & ADMIN API METHODS
// ==========================================

export async function loginUser(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal masuk');
  return data;
}

export async function logoutUser(token) {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  } catch (err) {
    console.warn('Logout warning:', err);
  }
}

export async function getCurrentUser(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal memuat profil');
  return data;
}

export async function changeUserPassword(token, oldPassword, newPassword) {
  const res = await fetch(`${API_BASE}/auth/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal mengubah kata sandi');
  return data;
}

export async function getAdminStats(token) {
  const res = await fetch(`${API_BASE}/admin/stats`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Admin-Key': token
    }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal memuat statistik admin');
  return data;
}

export async function clearAdminCache(token) {
  const res = await fetch(`${API_BASE}/admin/clear-cache`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Admin-Key': token
    }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal membersihkan cache');
  return data;
}

export async function resetAdminLimits(token) {
  const res = await fetch(`${API_BASE}/admin/reset-limits`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Admin-Key': token
    }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal mereset rate limit');
  return data;
}

export async function cleanupAdminDisk(token) {
  const res = await fetch(`${API_BASE}/admin/cleanup-disk`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Admin-Key': token
    }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Gagal membersihkan disk');
  return data;
}
