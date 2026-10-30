import React, { useState, useEffect } from 'react';
import { 
  FileText, BookOpen, Layers, BarChart3, Flag, Bookmark, CheckCircle, BookMarked,
  AlertTriangle, Info, X
} from 'lucide-react';
import Header from './components/Header';
import HeroUpload from './components/HeroUpload';
import FolderCard from './components/FolderCard';
import EditorModal from './components/EditorModal';
import PreviewModal from './components/PreviewModal';
import ApiKeyModal from './components/ApiKeyModal';
import AdminModal from './components/AdminModal';
import FormatGuideModal from './components/FormatGuideModal';
import StickyActionBar from './components/StickyActionBar';
import BookCompiler from './components/BookCompiler';
import { checkBackendHealth, extractReport, generateAndDownloadDocx } from './services/api';

// Draf awal bawaan (Modul 8 demo)
const INITIAL_DEMO_REPORT = {
  module_number: 8,
  module_title: "Integrasi Data Lapangan (GPS & Crowdsourcing)",
  header_title: "MODUL PRAKTIKUM VIII\n(INTEGRASI DATA LAPANGAN (GPS & CROWDSOURCING))",
  student_name: "",
  student_nim: "",
  student_class: "",
  student_course: "",
  has_parent_headings: false,
  bab2: {
    subbab_title: "Integrasi Data Lapangan (GPS & Crowdsourcing)",
    content: [
      {
        type: "paragraph",
        text: "Dalam siklus pengembangan Sistem Informasi Geografis (SIG), data spasial tidak hanya diperoleh melalui kegiatan pemetaan sekunder (seperti digitasi peta analog atau klasifikasi citra satelit), melainkan juga melalui akuisisi data primer langsung dari lapangan. Teknologi Global Navigation Satellite System (GNSS) / Global Positioning System (GPS) serta sensor lokasi pada perangkat smartphone modern memungkinkan perekaman posisi objek geografis di bumi secara real-time. Berikut beberapa format data interchange lapangan dan kegunaannya:"
      },
      {
        type: "list",
        prefix: "1.",
        text: "CSV / TXT: Delimited Text: Tabel koordinat X (Bujur/Easting) dan Y (Lintang/Northing) beserta atribut objek."
      },
      {
        type: "list",
        prefix: "2.",
        text: "Gpx: GPS Exchange Format: Format XML standar industri untuk data Waypoint, Track, dan Route GPS."
      },
      {
        type: "list",
        prefix: "3.",
        text: "KML/KMZ: Keyhole Markup Language: Format representasi spasial Google Earth/Google Maps."
      },
      {
        type: "paragraph",
        text: "Perangkat GPS lapangan sering kali mencatat koordinat dalam notasi Degrees, Minutes, Seconds (DMS). Namun, perangkat lunak SIG seperti QGIS memerlukan notasi Decimal Degrees (DD) untuk kalkulasi matematis spasial. Formula Konversi DMS ke DD:\nDecimalDegree(DD) = Degree + (Minute / 60) + (Second / 3600)"
      },
      {
        type: "list",
        prefix: "1.",
        restart: true,
        text: "Aturan Tanda Lintang/Bujur di QGIS:"
      },
      {
        type: "list",
        prefix: "a.",
        level: 2,
        text: "Bujur Timur (BT / East): Nilai Positif (+) – Kota Palu berada sekitar + 119.8 BT."
      },
      {
        type: "list",
        prefix: "b.",
        level: 2,
        text: "Lintang Selatan (LS / South): Nilai Negatif (–) – Kota Palu berada di selatan khatulistiwa, sekitar - 0.8 hingga - 0.9 LS."
      },
      {
        type: "list",
        prefix: "2.",
        text: "Waypoints (Titik Lokasi): Koordinat tunggal (X, Y, Z) yang menandai posisi lokasi fisik spesifik (misal: posisi Gedung Rektorat UNTAD)."
      },
      {
        type: "list",
        prefix: "3.",
        text: "Tracks (Jejak Rekam): Urutan pasangan titik koordinat yang direkam secara berkala sesuai interval waktu/jarak, menggambarkan rute pergerakan aktual di lapangan."
      },
      {
        type: "list",
        prefix: "4.",
        text: "Routes (Rute Rencana): Urutan titik navigasi yang direncanakan untuk dilalui dari lokasi awal menuju lokasi tujuan."
      },
      {
        type: "paragraph",
        text: "Akurasi penentuan posisi berbasis GNSS pada perangkat bergerak sangat dipengaruhi oleh geometri konstelasi satelit (Geometric Dilution of Precision / GDOP), efek multipath, serta kerapatan tutupan kanopi vegetasi dan gedung perkotaan. Dalam integrasi data spasial lapangan menggunakan perangkat lunak sumber terbuka QGIS, proses transformasi koordinat dan verifikasi topologi menjadi tahapan krusial guna meminimalkan distorsi geometris saat data koordinat mentah dikonversi menjadi entitas vektor berformat Shapefile (Ariyanto & Hani'ah, 2021). Pendekatan crowdsourcing berbasis partisipasi lapangan memungkinkan pemutakhiran basis data geospasial secara dinamis, di mana data waypoint dan track yang dihimpun secara terdistribusi dapat divalidasi silang terhadap basemap citra satelit resolusi tinggi guna menghasilkan informasi geospasial tematik yang andal, akurat, dan terstandarisasi bagi kebutuhan analisis spasial perkotaan."
      },
      {
        type: "paragraph",
        text: "Pengelolaan data spasial berbasis interchange format seperti GPX dan KML dalam lingkungan SIG modern menuntut pemahaman terhadap struktur skema XML yang mendasarinya. Berkas GPX menyimpan elemen data temporal dan elevasi secara terstruktur melalui tag trkpt untuk lintasan serta wpt untuk titik acuan, yang saat diimpor ke dalam QGIS secara otomatis ditranslasikan menjadi tabel atribut berkoordinat geografis WGS 84. Sementara itu, format KML memfasilitasi visualisasi spasial interaktif tiga dimensi yang terintegrasi dengan sensor orientasi perangkat bergerak (Pratama & Sugianto, 2022). Standarisasi data hasil survei lapangan melalui penyesuaian sistem referensi koordinat serta eliminasi distorsi rambat sinyal menjamin konsistensi topologi antarentitas spasial, sehingga saat dilakukan integrasi dengan data sekunder maupun citra satelit resolusi spasial tinggi, pergeseran posisi (spatial displacement) dapat ditekan di bawah ambang batas toleransi ketelitian pemetaan skala besar."
      }
    ]
  },
  bab3: {
    subbab_title: "Integrasi Data Lapangan (GPS & Crowdsourcing)",
    content: [
      { type: "list", prefix: "1.", text: "Impor Tabel Koordinat CSV (Add Delimited Text Layer)" },
      { type: "list", prefix: "a.", level: 2, text: "Buka aplikasi QGIS Desktop." },
      { type: "list", prefix: "b.", level: 2, text: "Aktifkan Basemap Google Satellite atau OpenStreetMap via QuickMapServices." },
      { type: "list", prefix: "c.", level: 2, text: "Buka menu Layer > Add Layer > Add Delimited Text Layer... (atau klik ikon petik dua koma pada toolbar samping)." },
      { type: "list", prefix: "d.", level: 2, text: "Pada kolom File name, klik tombol Browse dan pilih file data koordinat lapangan (misal: titik_lapangan.csv)." },
      { type: "list", prefix: "e.", level: 2, text: "Pada bagian File format, pilih opsi CSV (comma separated values)." },
      { type: "list", prefix: "f.", level: 2, text: "Pada bagian Geometry Definition, pilih Point coordinates. Atur X field menjadi Bujur (Longitude) dan Y field menjadi Lintang (Latitude)." },
      { type: "list", prefix: "g.", level: 2, text: "Atur Geometry CRS ke EPSG:4326 - WGS 84." },
      { type: "list", prefix: "h.", level: 2, text: "Klik tombol Add lalu Close. Titik koordinat survei lapangan kini berhasil dimuat di atas basemap citra satelit." },
      { 
        type: "placeholder", 
        id: "bab3_ph_1", 
        title: "Tampilan Impor Tabel Koordinat CSV", 
        description: "Tangkapan layar lembar kerja QGIS saat layer Delimited Text CSV titik koordinat lapangan berhasil dimuat dan ditumpangsusunkan secara presisi di atas basemap citra satelit." 
      },
      { type: "list", prefix: "2.", text: "Ekspor Layer CSV Menjadi Esri Shapefile (.shp)" },
      { type: "list", prefix: "a.", level: 2, text: "Klik kanan layer CSV pada panel Layers, pilih Export > Save Features As..." },
      { type: "list", prefix: "b.", level: 2, text: "Pilih Format: ESRI Shapefile." },
      { type: "list", prefix: "c.", level: 2, text: "Simpan dengan nama titik_survei.shp pada direktori kerja praktikum." },
      { type: "list", prefix: "d.", level: 2, text: "Klik OK untuk menyimpan data vektor permanen." },
      { 
        type: "placeholder", 
        id: "bab3_ph_2", 
        title: "Jendela Konfigurasi Ekspor Shapefile", 
        description: "Screenshot jendela Save Vector Layer as saat konfigurasi format ESRI Shapefile dan CRS WGS 84." 
      }
    ]
  },
  bab4: {
    subbab_title: "Integrasi Data Lapangan (GPS & Crowdsourcing)",
    content: [
      {
        type: "list",
        prefix: "1.",
        title: "Hasil Visualisasi Sebaran Titik Koordinat GPS Lapangan",
        analysis: "Berdasarkan hasil pengolahan data lapangan, titik-titik koordinat survei yang diimpor dari format Delimited Text CSV berhasil dipetakan secara akurat di atas basemap satelit dengan sistem koordinat WGS 84. Distribusi spasial titik survei menunjukkan kesesuaian posisi fisik fasilitas umum di lapangan dengan ketelitian tinggi, membuktikan efektivitas metode akuisisi koordinat langsung untuk verifikasi ground-truth data spasial perkotaan."
      },
      {
        type: "placeholder",
        id: "bab4_ph_1",
        title: "Peta Sebaran Titik Survei Lapangan",
        description: "Tampilan screenshot peta digital yang menyajikan sebaran titik koordinat GPS lapangan lengkap dengan basemap satelit dan pelabelan nama objek."
      },
      {
        type: "list",
        prefix: "2.",
        title: "Hasil Struktur Tabel Atribut Layer Survei Lapangan",
        analysis: "Tabel atribut dari layer Shapefile hasil konversi menyajikan informasi atributif lengkap meliputi koordinat bujur, lintang, elevasi, dan kategori objek lapangan. Integrasi data tabel ke dalam entitas spasial QGIS memungkinkan dilakukannya manipulasi kalkulasi spasial lebih lanjut serta penyusunan basis data geospasial terstandar."
      },
      {
        type: "placeholder",
        id: "bab4_ph_2",
        title: "Tabel Atribut Titik Lapangan",
        description: "Screenshot jendela Attribute Table dari layer titik_survei.shp yang menampilkan data atribut lapangan secara terstruktur."
      }
    ]
  },
  bab5: {
    subbab_title: "Kesimpulan Modul 8",
    content: [
      {
        type: "paragraph",
        text: "Berdasarkan praktikum Integrasi Data Lapangan (GPS & Crowdsourcing) yang telah dilaksanakan, dapat disimpulkan bahwa:"
      },
      {
        type: "list",
        prefix: "1.",
        text: "Format data spasial interchange seperti CSV dan GPX dapat diintegrasikan secara presisi ke dalam perangkat lunak SIG QGIS melalui penyesuaian sistem referensi koordinat geografis WGS 84 (EPSG:4326), memastikan akurasi posisi objek lapangan tanpa distorsi geometris."
      },
      {
        type: "list",
        prefix: "2.",
        text: "Transformasi data koordinat teks lapangan menjadi entitas vektor Shapefile memfasilitasi interoperabilitas basis data spasial dan memungkinkan validasi ground-truth terhadap basemap citra satelit resolusi tinggi secara efisien."
      }
    ]
  },
  daftar_pustaka: [
    "Ariyanto, D., & Hani'ah. (2021). Integrasi data GNSS handheld untuk pemutakhiran peta tematik skala besar menggunakan open source GIS. Jurnal Geodesi dan Geomatika, 16(2), 112–121. https://doi.org/10.14710/jgg.16.2.112-121",
    "Pratama, R. A., & Sugianto, B. (2022). Pemanfaatan format data spasial GPX dan KML dalam pemetaan partisipatif berbasis crowdsourcing. Geomatika Mandiri, 8(1), 45–54. https://doi.org/10.31227/osf.io/gm81p"
  ]
};

export default function App() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [backendStatus, setBackendStatus] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  // Inisialisasi identitas dari localStorage agar tidak hardcoded
  const [studentInfo, setStudentInfo] = useState(() => {
    try {
      const saved = localStorage.getItem('laprak_student_info');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {}
    return {
      name: '',
      nim: '',
      class: '',
      course: '',
      module_number: ''
    };
  });

  const [reportData, setReportData] = useState(INITIAL_DEMO_REPORT);
  const [originalReportData, setOriginalReportData] = useState(INITIAL_DEMO_REPORT);
  const [imagesMap, setImagesMap] = useState({});

  // Toast Notification System
  const [toast, setToast] = useState(null);

  // Navigation mode ('single' | 'book')
  const [appMode, setAppMode] = useState('single');

  // Loading states
  const [isExtracting, setIsExtracting] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);

  // Modal states
  const [isApiKeyOpen, setIsApiKeyOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorActiveTab, setEditorActiveTab] = useState('bab2');

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Simpan studentInfo ke localStorage tiap kali berubah
  const handleUpdateStudentInfo = (newInfo) => {
    setStudentInfo(newInfo);
    try {
      localStorage.setItem('laprak_student_info', JSON.stringify(newInfo));
    } catch (e) {}
  };

  // Cek koneksi backend pada inisialisasi
  useEffect(() => {
    checkBackendHealth().then(status => {
      setBackendStatus(status);
    });
  }, []);

  const handleSaveApiKey = (key) => {
    setApiKey(key);
    localStorage.setItem('gemini_api_key', key);
    showToast('Gemini API Key berhasil disimpan!', 'success');
  };

  const handleExtract = async () => {
    if (!selectedFile) {
      showToast('Silakan pilih berkas PDF modul asdos terlebih dahulu.', 'error');
      return;
    }

    setIsExtracting(true);
    setLoadingStep('Membaca PDF modul...');

    try {
      setTimeout(() => setLoadingStep('Analisis struktur & OCR dengan Gemini AI...'), 1000);
      const res = await extractReport(selectedFile, studentInfo, apiKey);
      setReportData(res.data);
      setOriginalReportData(res.data);
      showToast('Draf laporan berhasil disusun sesuai standar akademik!', 'success');
    } catch (err) {
      showToast(`Gagal menyusun laporan: ${err.message}`, 'error');
    } finally {
      setIsExtracting(false);
      setLoadingStep('');
    }
  };

  const handleDownload = async () => {
    if (!reportData) return;

    // Validasi data identitas (Mencegah submit cover kosong)
    if (!studentInfo.name.trim() || !studentInfo.nim.trim()) {
      showToast('Harap lengkapi Nama dan NIM Anda terlebih dahulu pada formulir di atas!', 'error');
      return;
    }

    setIsDownloading(true);
    try {
      // Sinkronkan data profil terbaru ke reportData
      const finalReport = {
        ...reportData,
        student_name: studentInfo.name || reportData.student_name,
        student_nim: studentInfo.nim || reportData.student_nim,
        student_class: studentInfo.class || reportData.student_class,
        course_name: studentInfo.course || reportData.course_name
      };

      await generateAndDownloadDocx(finalReport, imagesMap);
      showToast('Dokumen Word (.docx) berhasil dibuat dan diunduh!', 'success');
    } catch (err) {
      showToast(`Gagal mengunduh dokumen: ${err.message}`, 'error');
    } finally {
      setIsDownloading(false);
    }
  };

  const openEditorTab = (tabId) => {
    setEditorActiveTab(tabId);
    setIsEditorOpen(true);
  };

  const handleResetVerbatim = (tabKey) => {
    if (!originalReportData) return;
    if (tabKey === 'all') {
      setReportData(JSON.parse(JSON.stringify(originalReportData)));
      showToast('Seluruh teks laporan dikembalikan ke draf asli asdos!', 'info');
    } else if (originalReportData[tabKey]) {
      setReportData(prev => ({
        ...prev,
        [tabKey]: JSON.parse(JSON.stringify(originalReportData[tabKey]))
      }));
      showToast(`Teks ${tabKey.toUpperCase()} dikembalikan ke draf asli asdos!`, 'info');
    }
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden p-4 sm:p-8 md:p-10">
      
      {/* Toast Notification (Non-blocking Neubrutalism Banner) */}
      {toast && (
        <div 
          role="alert"
          aria-live="assertive"
          className={`fixed bottom-24 right-4 sm:right-8 z-50 max-w-md w-full border-3 border-black p-4 rounded-2xl shadow-neo-lg flex items-start justify-between gap-3 transition-all duration-200 ${
            toast.type === 'error' ? 'bg-[#FF5B99] text-white' : 
            toast.type === 'success' ? 'bg-[#38EF7D] text-black' : 
            'bg-[#FFE600] text-black'
          }`}
        >
          <div className="flex items-start gap-2.5">
            {toast.type === 'error' && <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-white" strokeWidth={2.5} />}
            {toast.type === 'success' && <CheckCircle className="w-5 h-5 shrink-0 mt-0.5 text-black" strokeWidth={2.5} />}
            {toast.type === 'info' && <Info className="w-5 h-5 shrink-0 mt-0.5 text-black" strokeWidth={2.5} />}
            <p className="font-black text-sm leading-snug">{toast.message}</p>
          </div>
          <button 
            onClick={() => setToast(null)}
            aria-label="Tutup notifikasi"
            className="shrink-0 p-1 rounded-lg border-2 border-black bg-white text-black hover:bg-gray-100 neo-btn focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
          >
            <X className="w-3.5 h-3.5" strokeWidth={3} />
          </button>
        </div>
      )}

      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Navigation Bar */}
        <Header 
          onOpenApiKey={() => setIsApiKeyOpen(true)}
          onOpenGuide={() => setIsGuideOpen(true)}
          onOpenAdmin={() => setIsAdminOpen(true)}
          backendStatus={backendStatus}
        />

        {/* Mode Switcher: Modul Mandiri vs Pembukuan Akhir */}
        <div className="flex flex-wrap items-center justify-center gap-3 p-2 bg-white border-3 border-black rounded-2xl shadow-neo max-w-xl mx-auto">
          <button
            type="button"
            onClick={() => setAppMode('single')}
            aria-label="Mode Modul Mandiri"
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 border-black font-black text-xs sm:text-sm transition-all duration-150 focus:outline-none focus-visible:ring-3 focus-visible:ring-black ${
              appMode === 'single'
                ? 'bg-[#FFE600] shadow-neo-sm -translate-x-0.5 -translate-y-0.5 text-black'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border-dashed'
            }`}
          >
            <FileText className="w-4 h-4 text-black" />
            <span>MODUL MANDIRI</span>
          </button>
          <button
            type="button"
            onClick={() => setAppMode('book')}
            aria-label="Mode Pembukuan Akhir"
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 border-black font-black text-xs sm:text-sm transition-all duration-150 focus:outline-none focus-visible:ring-3 focus-visible:ring-black ${
              appMode === 'book'
                ? 'bg-[#FF5B99] text-white shadow-neo-sm -translate-x-0.5 -translate-y-0.5'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border-dashed'
            }`}
          >
            <BookMarked className="w-4 h-4" />
            <span>PEMBUKUAN AKHIR (MERGE)</span>
          </button>
        </div>

        {appMode === 'single' ? (
          <>
            {/* Hero Upload & Metadata Form */}
            <HeroUpload
              selectedFile={selectedFile}
              onFileSelect={setSelectedFile}
              studentInfo={studentInfo}
              setStudentInfo={handleUpdateStudentInfo}
              onExtract={handleExtract}
              isLoading={isExtracting}
              loadingStep={loadingStep}
              onError={(msg) => showToast(msg, 'error')}
            />

            {/* Section: Bab Cards (Folder Tabs Style) */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-black tracking-tight text-black">Koleksi Bab Laporan</h3>
                  <p className="text-xs sm:text-sm font-bold text-gray-600">
                    Klik kartu bab untuk mengedit teks atau mengunggah screenshot praktikum asli Anda
                  </p>
                </div>
                <span className="hidden sm:inline-flex items-center gap-1.5 bg-[#38EF7D] border-2 border-black px-3 py-1 rounded-full text-xs font-black shadow-neo-sm">
                  <CheckCircle className="w-3.5 h-3.5 text-black" strokeWidth={3} /> 6 Bab Terstruktur
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                
                {/* Kartu 1: Cover */}
                <FolderCard
                  tabLabel="COVER"
                  tabColor="bg-gray-300"
                  icon={FileText}
                  iconBg="bg-gray-200"
                  badgeText="Halaman 1"
                  badgeBg="bg-gray-100"
                  title="Halaman Sampul"
                  description={studentInfo.name ? `${studentInfo.name} • ${studentInfo.nim || '-'} • ${studentInfo.class || '-'}` : 'Isi nama dan NIM pada formulir di atas'}
                  onClick={() => openEditorTab('cover')}
                />

                {/* Kartu 2: Bab II Landasan Teori */}
                <FolderCard
                  tabLabel={`2.1.${reportData.module_number || 1}`}
                  tabColor="bg-[#38EF7D]"
                  icon={BookOpen}
                  iconBg="bg-[#38EF7D]"
                  badgeText="FULL PAGE PASS"
                  badgeBg="bg-[#38EF7D]"
                  badgeColor="text-black"
                  title="Bab II: Teori Dasar"
                  description="Teks asdos verbatim + sitasi jurnal ilmiah Open-Access terverifikasi (>= 2020)."
                  onClick={() => openEditorTab('bab2')}
                />

                {/* Kartu 3: Bab III Langkah Kerja */}
                <FolderCard
                  tabLabel={`3.1.${reportData.module_number || 1}`}
                  tabColor="bg-[#FFE600]"
                  icon={Layers}
                  iconBg="bg-[#FFE600]"
                  badgeText={`${reportData.bab3?.content?.filter(x => x.type === 'placeholder').length || 0} Slot Foto`}
                  badgeBg="bg-white"
                  title="Bab III: Langkah Kerja"
                  description="Langkah kerja verbatim asdos. Siap upload screenshot praktikum per placeholder."
                  onClick={() => openEditorTab('bab3')}
                />

                {/* Kartu 4: Bab IV Hasil dan Pembahasan */}
                <FolderCard
                  tabLabel={`4.1.${reportData.module_number || 1}`}
                  tabColor="bg-[#FF5B99]"
                  icon={BarChart3}
                  iconBg="bg-[#FF5B99]"
                  iconColor="text-white"
                  badgeText={`${reportData.bab4?.content?.filter(x => x.type === 'list').length || 2} Butir Luaran`}
                  badgeBg="bg-[#FF5B99]"
                  badgeColor="text-white"
                  title="Bab IV: Hasil & Ulasan"
                  description="Dinamis mengikuti modul asdos, dilengkapi slot luaran dan pembahasan teknis."
                  onClick={() => openEditorTab('bab4')}
                />

                {/* Kartu 5: Bab V Penutup */}
                <FolderCard
                  tabLabel={`5.1.${reportData.module_number || 1}`}
                  tabColor="bg-[#9D71FD]"
                  icon={Flag}
                  iconBg="bg-[#9D71FD]"
                  iconColor="text-white"
                  badgeText="Kesimpulan Modul"
                  badgeBg="bg-white"
                  title="Bab V: Penutup"
                  description="Heading 3 standar 5.1.N khusus untuk kesimpulan modul praktikum terkait."
                  onClick={() => openEditorTab('bab5')}
                />

                {/* Kartu 6: Daftar Pustaka */}
                <FolderCard
                  tabLabel="APA 7TH"
                  tabColor="bg-[#FF8A65]"
                  icon={Bookmark}
                  iconBg="bg-[#FF8A65]"
                  badgeText={`${reportData.daftar_pustaka?.length || 2} Referensi`}
                  badgeBg="bg-white"
                  title="Daftar Pustaka"
                  description="Halaman baru mandiri, hanging indent 1,27 cm, judul jurnal otomatis cetak miring."
                  onClick={() => openEditorTab('pustaka')}
                />

              </div>
            </div>

            {/* Sticky Action Bar */}
            <StickyActionBar
              onPreview={() => setIsPreviewOpen(true)}
              onDownload={handleDownload}
              isDownloading={isDownloading}
              hasData={!!reportData}
            />
          </>
        ) : (
          <BookCompiler initialStudentInfo={studentInfo} />
        )}

      </div>

      {/* Modals */}
      <ApiKeyModal
        isOpen={isApiKeyOpen}
        onClose={() => setIsApiKeyOpen(false)}
        onSave={handleSaveApiKey}
        currentKey={apiKey}
        serverHasQuota={backendStatus?.has_env_key}
      />

      <AdminModal
        isOpen={isAdminOpen}
        onClose={() => setIsAdminOpen(false)}
      />

      <FormatGuideModal
        isOpen={isGuideOpen}
        onClose={() => setIsGuideOpen(false)}
      />

      <PreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        reportData={{
          ...reportData,
          student_name: studentInfo.name || reportData.student_name,
          student_nim: studentInfo.nim || reportData.student_nim,
          student_class: studentInfo.class || reportData.student_class,
          course_name: studentInfo.course || reportData.course_name
        }}
      />

      <EditorModal
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        activeTab={editorActiveTab}
        setActiveTab={setEditorActiveTab}
        reportData={reportData}
        setReportData={setReportData}
        imagesMap={imagesMap}
        setImagesMap={setImagesMap}
        onResetVerbatim={handleResetVerbatim}
        onError={(msg) => showToast(msg, 'error')}
      />

    </div>
  );
}
