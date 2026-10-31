"""
book_compiler.py
Mesin kompilasi Pembukuan Laporan Akhir Praktikum (Model 1 - Struktur Bab Terpadu).
Menggabungkan beberapa berkas modul praktikum (.docx) menjadi 1 dokumen pembukuan utuh
dengan prinsip: MENJAGA 100% ISI LAPORAN ASLI SECARA VERBATIM TANPA PERUBAHAN SEDIKIT PUN:
- Halaman Sampul Pembukuan Utama
- Kata Pengantar & Daftar Isi Otomatis (dengan w:updateFields untuk MS Word)
- BAB II LANDASAN TEORI (Memuat 2.1.1, 2.1.2, ..., 2.1.N dari tiap modul secara verbatim)
- BAB III LANGKAH KERJA (Memuat 3.1.1, 3.1.2, ..., 3.1.N beserta gambar/screenshot asli secara verbatim)
- BAB IV HASIL DAN PEMBAHASAN (Memuat 4.1.1, 4.1.2, ..., 4.1.N beserta hasil & screenshot secara verbatim)
- BAB V PENUTUP (Memuat kesimpulan kumulatif 5.1.1, 5.1.2, ..., 5.1.N secara verbatim)
- DAFTAR PUSTAKA GABUNGAN (Deduplikasi unik, urut abjad APA 7th Edition)
"""

import os
import sys
import io
import re
import copy
import docx
import docxcompose.composer

core_dir = os.path.dirname(os.path.abspath(__file__))
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

import docx_styler
from report_engine import int_to_roman

def is_parent_chapter_heading(txt: str) -> bool:
    """
    Mendeteksi apakah suatu teks adalah judul utama bab (Heading 1)
    seperti 'BAB II LANDASAN TEORI', 'BAB III LANGKAH KERJA', dsb.
    """
    t = txt.strip().lower()
    return bool(re.match(r'^(?:bab\s+(?:[ivxlcdm]+|\d+)|daftar\s+pustaka)\b', t))

def is_parent_subheading(txt: str) -> bool:
    """
    Mendeteksi apakah suatu teks adalah Heading 2 tingkat atas (contoh: 2.1, 3.1, 4.1, 5.1)
    dan BUKAN sub-bab modul (seperti 2.1.1, 3.1.5, dst).
    """
    t = txt.strip()
    return bool(re.match(r'^(?:[2345])\.1(?:\s+|\t+)(?!\d)', t))

def remove_page_breaks_from_element(elem):
    """Menghapus elemen <w:br w:type='page'/> dari suatu elemen paragraph OpenXML."""
    for br in elem.xpath('.//w:br[@w:type="page"]'):
        parent = br.getparent()
        if parent is not None:
            parent.remove(br)

def clean_section_elements(elements):
    """
    Membersihkan elemen sebelum digabungkan:
    1. Membuang paragraf kosong di akhir seksi
    2. Menghapus page break di akhir elemen seksi agar tidak menimbulkan double page break
    """
    cleaned = list(elements)
    while cleaned:
        last = cleaned[-1]
        if last.tag.endswith('p'):
            txt = "".join(last.itertext()).strip()
            drawings = last.xpath('.//w:drawing | .//w:pict')
            if not txt and not drawings:
                cleaned.pop()
                continue
        break
        
    if cleaned and cleaned[-1].tag.endswith('p'):
        last_copy = copy.deepcopy(cleaned[-1])
        remove_page_breaks_from_element(last_copy)
        cleaned[-1] = last_copy
        
    return cleaned

def set_heading_page_break_before(p):
    """Menambahkan w:pageBreakBefore pada paragraph Heading 1 agar selalu mulai di halaman baru secara rapi."""
    pPr = p._p.get_or_add_pPr()
    if not pPr.xpath('./w:pageBreakBefore'):
        pPr.append(parse_xml(r'<w:pageBreakBefore %s/>' % nsdecls('w')))

def is_same_title(txt1: str, txt2: str) -> bool:
    """
    Membandingkan kesamaan judul modul dengan teks heading,
    mengabaikan prefix penomoran (2.1.X, BAB II, dsb) dan karakter non-alfanumerik.
    """
    if not txt1 or not txt2:
        return False
    c1 = re.sub(r'^(?:bab\s+[ivx]+\s*[\n\r]*)?(?:[2345]\.1(?:\.\d+)?\s*)?', '', txt1, flags=re.I).strip()
    c2 = re.sub(r'^(?:bab\s+[ivx]+\s*[\n\r]*)?(?:[2345]\.1(?:\.\d+)?\s*)?', '', txt2, flags=re.I).strip()
    
    # Abaikan kalimat narasi panjang
    if any(c1.lower().startswith(k) for k in ["berdasarkan", "dalam", "pada", "dengan", "melalui", "hasil"]):
        return False

    n1 = re.sub(r'[^a-zA-Z0-9]', '', c1).lower()
    n2 = re.sub(r'[^a-zA-Z0-9]', '', c2).lower()
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    if len(n1) >= 15 and len(n2) >= 15 and (n1 in n2 or n2 in n1):
        return True
    return False

def parse_module_docx(docx_path: str) -> dict:
    """
    Menganalisis dan membedah dokumen .docx modul praktikum menjadi komponen bab terpisah.
    Mendukung format standar dengan Heading BAB maupun format Modul Terusan (berulang judul modul).
    Menjaga setiap elemen (paragraf & tabel) 100% utuh tanpa terpotong.
    """
    filename = os.path.basename(docx_path)
    if filename.startswith('~$'):
        return None

    doc = docx.Document(docx_path)
    
    module_data = {
        "file_path": docx_path,
        "filename": filename,
        "module_number": None,
        "module_title": "",
        "student_name": "",
        "student_nim": "",
        "student_class": "",
        "course_name": "",
        "bab2_elements": [],
        "bab3_elements": [],
        "bab4_elements": [],
        "bab5_elements": [],
        "daftar_pustaka_entries": [],
        "doc_ref": doc
    }

    # 1. Ekstrak nomor modul dari nama berkas sebagai fallback awal
    m_fn = re.search(r'modul\s*([0-9]+|[ivxlcdm]+)', filename, re.IGNORECASE)
    if m_fn:
        val = m_fn.group(1).upper()
        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}
        if val in roman_map:
            module_data["module_number"] = roman_map[val]
        elif val.isdigit():
            module_data["module_number"] = int(val)

    body_elements = [el for el in doc.element.body if not el.tag.endswith('sectPr')]

    # 2. Cek apakah ada cover di awal dokumen (memuat "Nama :", "NIM :", atau "MODUL PRAKTIKUM")
    has_cover = False
    cover_end_idx = 0
    for i, el in enumerate(body_elements[:25]):
        if el.tag.endswith('p'):
            txt = docx.text.paragraph.Paragraph(el, doc).text.strip().lower()
            if any(k in txt for k in ["nama :", "nama:", "nim :", "nim:", "modul praktikum"]):
                has_cover = True
                cover_end_idx = i + 1

    # Ekstrak identitas mahasiswa jika ada cover
    if has_cover:
        for el in body_elements[:cover_end_idx]:
            if el.tag.endswith('p'):
                txt = docx.text.paragraph.Paragraph(el, doc).text.strip()
                t_low = txt.lower()
                if "nama" in t_low and ":" in txt:
                    module_data["student_name"] = txt.split(":", 1)[1].strip()
                elif "nim" in t_low and ":" in txt:
                    module_data["student_nim"] = txt.split(":", 1)[1].strip()
                elif "kelas" in t_low and ":" in txt:
                    module_data["student_class"] = txt.split(":", 1)[1].strip()
                if "modul praktikum" in t_low:
                    rom_match = re.search(r'modul praktikum\s+([ivxlcdm]+|[0-9]+)', txt, re.I)
                    if rom_match:
                        val = rom_match.group(1).upper()
                        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}
                        if val in roman_map:
                            module_data["module_number"] = roman_map[val]
                        elif val.isdigit():
                            module_data["module_number"] = int(val)
                if txt.startswith("(") and txt.endswith(")") and not module_data["module_title"]:
                    module_data["module_title"] = txt[1:-1].strip()

    # 3. Cari Judul Modul jika belum ditemukan dari cover
    if not module_data["module_title"]:
        start_search = cover_end_idx if has_cover else 0
        for el in body_elements[start_search:start_search+10]:
            if el.tag.endswith('p'):
                txt = docx.text.paragraph.Paragraph(el, doc).text.strip()
                m_clean = re.sub(r'^(?:bab\s+[ivx]+\s*[\n\r]*)?(?:2\.1(?:\.\d+)?\s*)?', '', txt, flags=re.I).strip()
                if m_clean and len(m_clean) >= 4 and len(m_clean) <= 120:
                    t_low = m_clean.lower()
                    if not any(k in t_low for k in ["nama", "nim", "kelas", "disusun", "landasan teori", "teori dasar"]):
                        module_data["module_title"] = m_clean
                        break

    mod_title = module_data["module_title"]

    # 4. Parsing elemen per seksi (Bab II, Bab III, Bab IV, Bab V, Daftar Pustaka)
    current_section = "cover" if has_cover else "bab2"
    seen_sections = set()
    if current_section == "bab2":
        seen_sections.add("bab2")

    for idx, el in enumerate(body_elements):
        if has_cover and idx < cover_end_idx:
            continue

        if not el.tag.endswith('p'):
            if current_section.startswith("bab"):
                module_data[f"{current_section}_elements"].append(el)
            continue

        p = docx.text.paragraph.Paragraph(el, doc)
        txt = p.text.strip()
        t_low = txt.lower()

        # Deteksi DAFTAR PUSTAKA
        if "daftar pustaka" in t_low and len(txt) <= 30:
            current_section = "daftar_pustaka"
            seen_sections.add("daftar_pustaka")
            continue

        # Indikator bab eksplisit
        is_bab2_explicit = bool(
            re.search(r'\bbab\s+ii\b', t_low) or 
            re.search(r'\b2\.1\b|\b2\.1\.', txt) or 
            ("landasan teori" in t_low and len(txt) <= 35) or
            ("teori dasar" in t_low and len(txt) <= 35)
        )
        is_bab3_explicit = bool(
            re.search(r'\bbab\s+iii\b', t_low) or 
            re.search(r'\b3\.1\b|\b3\.1\.', txt) or 
            ("langkah kerja" in t_low and len(txt) <= 35) or
            ("prosedur kerja" in t_low and len(txt) <= 35)
        )
        is_bab4_explicit = bool(
            re.search(r'\bbab\s+iv\b', t_low) or 
            re.search(r'\b4\.1\b|\b4\.1\.', txt) or 
            ("hasil dan pembahasan" in t_low and len(txt) <= 35)
        )
        is_bab5_explicit = bool(
            re.search(r'\bbab\s+v\b', t_low) or 
            re.search(r'\b5\.1\b|\b5\.1\.', txt) or 
            (t_low.startswith("kesimpulan") and len(txt) <= 30) or
            (t_low == "penutup")
        )

        is_title_match = is_same_title(txt, mod_title) if len(txt) <= 120 else False

        # Transisi ke Bab II
        if "bab2" not in seen_sections:
            if is_bab2_explicit or is_title_match or not has_cover:
                current_section = "bab2"
                seen_sections.add("bab2")
                m2 = re.search(r'2\.1\.([0-9]+)', txt)
                if m2 and not module_data["module_number"]:
                    module_data["module_number"] = int(m2.group(1))
                if is_parent_chapter_heading(txt) or is_parent_subheading(txt):
                    continue

        # Transisi ke Bab III
        if "bab2" in seen_sections and "bab3" not in seen_sections:
            if is_bab3_explicit or (is_title_match and len(module_data["bab2_elements"]) >= 3):
                current_section = "bab3"
                seen_sections.add("bab3")
                m3 = re.search(r'3\.1\.([0-9]+)', txt)
                if m3 and not module_data["module_number"]:
                    module_data["module_number"] = int(m3.group(1))
                if is_parent_chapter_heading(txt) or is_parent_subheading(txt):
                    continue
                if is_title_match and not is_bab3_explicit:
                    continue

        # Transisi ke Bab IV
        if "bab3" in seen_sections and "bab4" not in seen_sections:
            if is_bab4_explicit or (is_title_match and len(module_data["bab3_elements"]) >= 3):
                current_section = "bab4"
                seen_sections.add("bab4")
                m4 = re.search(r'4\.1\.([0-9]+)', txt)
                if m4 and not module_data["module_number"]:
                    module_data["module_number"] = int(m4.group(1))
                if is_parent_chapter_heading(txt) or is_parent_subheading(txt):
                    continue
                if is_title_match and not is_bab4_explicit:
                    continue

        # Transisi ke Bab V
        if "bab4" in seen_sections and "bab5" not in seen_sections:
            if is_bab5_explicit or (is_title_match and len(module_data["bab4_elements"]) >= 2):
                current_section = "bab5"
                seen_sections.add("bab5")
                m5 = re.search(r'5\.1\.([0-9]+)', txt)
                if m5 and not module_data["module_number"]:
                    module_data["module_number"] = int(m5.group(1))
                if is_parent_chapter_heading(txt) or is_parent_subheading(txt) or "kesimpulan" in t_low:
                    continue
                if is_title_match and not is_bab5_explicit:
                    continue

        # Lewati heading parent agar tidak ganda di dokumen pembukuan terpadu
        if is_parent_chapter_heading(txt) or is_parent_subheading(txt):
            continue

        # Masukkan ke seksi aktif
        if current_section == "bab2":
            module_data["bab2_elements"].append(el)
        elif current_section == "bab3":
            module_data["bab3_elements"].append(el)
        elif current_section == "bab4":
            module_data["bab4_elements"].append(el)
        elif current_section == "bab5":
            module_data["bab5_elements"].append(el)
        elif current_section == "daftar_pustaka":
            if txt and not is_parent_chapter_heading(txt):
                module_data["daftar_pustaka_entries"].append(txt)

    # Alias kompatibilitas inspect API
    module_data["bab2_paragraphs"] = module_data["bab2_elements"]
    module_data["bab3_paragraphs"] = module_data["bab3_elements"]
    module_data["bab4_paragraphs"] = module_data["bab4_elements"]
    module_data["bab5_paragraphs"] = module_data["bab5_elements"]

    return module_data

def append_element_verbatim(doc_dst, elem, doc_src, composer):
    """
    Menyalin satu elemen OpenXML (paragraf atau tabel) secara 100% presisi dan verbatim:
    - Tidak mengubah satu huruf, kata, atau tanda baca pun dari dokumen asli
    - Menyisipkan tepat sebelum sectPr agar urutan halaman dan bab selalu linear
    - Mendaftarkan penomoran list (<w:numPr>) ke numbering.xml master tanpa tabrakan numId
    - Menjaga relasi gambar/screenshot (<a:blip r:embed>) tetap utuh di rels master
    - Menyalin styles, shapes, dan diagrams bawaan
    - Memastikan perataan teks tubuh paragraf adalah Justified
    """
    new_elem = copy.deepcopy(elem)
    
    # Cari elemen sectPr terakhir di body agar disisipkan tepat sebelumnya
    sectPrs = doc_dst.element.body.xpath('./w:sectPr')
    if sectPrs:
        sectPrs[-1].addprevious(new_elem)
    else:
        doc_dst.element.body.append(new_elem)
        
    composer.add_numberings(doc_src, new_elem)
    composer.add_images(doc_src, new_elem)
    composer.add_styles(doc_src, new_elem)
    composer.add_referenced_parts(doc_src.part, doc_dst.part, new_elem)
    composer.add_shapes(doc_src, new_elem)
    composer.add_diagrams(doc_src, new_elem)

    # Normalisasi perataan paragraf tubuh teks agar rapi (Justified)
    if new_elem.tag.endswith('p'):
        p_obj = docx.text.paragraph.Paragraph(new_elem, doc_dst)
        style_name = p_obj.style.name if p_obj.style else ""
        txt = p_obj.text.strip()
        has_drawings = bool(new_elem.xpath('.//w:drawing | .//w:pict'))
        if not style_name.startswith("Heading") and not has_drawings and len(txt) > 60:
            if p_obj.alignment is None or p_obj.alignment == WD_ALIGN_PARAGRAPH.LEFT:
                p_obj.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def renumber_lists_in_doc(doc):
    """
    Memastikan setiap kelompok list yang terpisah oleh paragraf biasa atau heading
    mendapatkan clone <w:abstractNum> dan <w:num> baru yang unik di numbering.xml, dengan:
    1. abstractNumId mandiri (tidak berbagi dengan kelompok list lain di modul/seksi lain).
    2. lvlOverride startOverride=1 untuk semua level (0 s/d 8).
    Sehingga Microsoft Word SECARA MUTLAK me-restart penomoran di 1 untuk setiap kelompok list baru,
    dan TIDAK PERNAH meneruskan angka (misal 6, 7, 8 atau 5, 6) dari kelompok sebelumnya.
    3. Heading dibersihkan dari w:numPr agar bebas dari nomor angka list biasa.
    """
    num_part = doc.part.numbering_part
    if not num_part:
        return

    w_ns = nsdecls("w").split("=")[1].strip('"\'')
    existing_anum_ids = [int(a.get(f'{{{w_ns}}}abstractNumId')) 
                         for a in num_part.element.xpath('//w:abstractNum')
                         if a.get(f'{{{w_ns}}}abstractNumId') and a.get(f'{{{w_ns}}}abstractNumId').isdigit()]
    max_anum_id = max(existing_anum_ids) if existing_anum_ids else 500

    existing_num_ids = [int(n.get(f'{{{w_ns}}}numId')) 
                        for n in num_part.element.xpath('//w:num')
                        if n.get(f'{{{w_ns}}}numId') and n.get(f'{{{w_ns}}}numId').isdigit()]
    max_num_id = max(existing_num_ids) if existing_num_ids else 500

    current_group_id = None
    prev_was_list = False

    for child in doc.element.body:
        if child.tag.endswith('tbl'):
            prev_was_list = False
            current_group_id = None
            continue

        if not child.tag.endswith('p'):
            continue

        p = docx.text.paragraph.Paragraph(child, doc)
        
        # 1. Jika ini adalah Heading, hapus numPr agar bebas dari penomoran list bawaan
        if p.style and p.style.name.startswith("Heading"):
            for numPr_h in child.xpath('.//w:numPr'):
                numPr_h.getparent().remove(numPr_h)
            prev_was_list = False
            current_group_id = None
            continue

        numPr = child.xpath('.//w:numPr')
        txt = p.text.strip()
        
        # Paragraf kosong tanpa teks dan tanpa drawing tidak memutus grup list
        if not txt and not child.xpath('.//w:drawing | .//w:pict'):
            continue

        if numPr:
            num_elem = numPr[0]
            numId_elem = num_elem.find(f'{{{w_ns}}}numId')

            # Jika paragraf sebelumnya BUKAN list (misal teks narasi, gambar, heading):
            # INI ADALAH KELOMPOK LIST BARU -> Buat clone abstractNum + num baru yang unik!
            if not prev_was_list:
                max_num_id += 1
                max_anum_id += 1
                current_group_id = max_num_id

                orig_num_id = numId_elem.get(f'{{{w_ns}}}val') if numId_elem is not None else '1'
                matched_num = num_part.element.xpath(f'//w:num[@w:numId="{orig_num_id}"]')
                if matched_num:
                    orig_anum_id = matched_num[0].xpath('./w:abstractNumId/@w:val')[0]
                else:
                    orig_anum_id = '0'

                matched_anum = num_part.element.xpath(f'//w:abstractNum[@w:abstractNumId="{orig_anum_id}"]')
                if matched_anum:
                    new_anum = copy.deepcopy(matched_anum[0])
                    new_anum.set(f'{{{w_ns}}}abstractNumId', str(max_anum_id))
                    nsid_elem = new_anum.find(f'{{{w_ns}}}nsid')
                    if nsid_elem is not None:
                        nsid_elem.set(f'{{{w_ns}}}val', f'{max_anum_id:08X}')
                    
                    # OpenXML schema: abstractNum harus diletakkan sebelum w:num pertama
                    num_elems = num_part.element.xpath('//w:num')
                    if num_elems:
                        num_elems[0].addprevious(new_anum)
                    else:
                        num_part.element.append(new_anum)
                    target_anum_id = max_anum_id
                else:
                    target_anum_id = orig_anum_id

                # Buat w:num baru dengan lvlOverride eksplisit untuk setiap level (0 s/d 8)
                lvl_overrides = "".join([
                    f'<w:lvlOverride w:ilvl="{lvl}"><w:startOverride w:val="1"/></w:lvlOverride>'
                    for lvl in range(9)
                ])
                new_num_xml = f'''<w:num {nsdecls("w")} w:numId="{current_group_id}">
                    <w:abstractNumId w:val="{target_anum_id}"/>
                    {lvl_overrides}
                </w:num>'''
                num_part.element.append(parse_xml(new_num_xml))

            if numId_elem is not None:
                numId_elem.set(f'{{{w_ns}}}val', str(current_group_id))

            prev_was_list = True
        else:
            prev_was_list = False
            current_group_id = None

def add_master_cover_page(doc, metadata: dict, min_mod: int, max_mod: int):
    """Membuat Halaman Sampul Utama Pembukuan Akademik."""
    course = metadata.get("course_name", "SISTEM INFORMASI GEOGRAFIS").upper()
    title = metadata.get("title", f"LAPORAN AKHIR PRAKTIKUM\n{course}").upper()
    name = metadata.get("student_name", "").upper()
    nim = metadata.get("student_nim", "")
    kelas = metadata.get("student_class", "INFORMATIKA C").upper()
    institution = metadata.get("institution", "PROGRAM STUDI S1 TEKNIK INFORMATIKA\nJURUSAN TEKNOLOGI INFORMASI\nFAKULTAS TEKNIK\nUNIVERSITAS TADULAKO").upper()
    year = metadata.get("academic_year", "2026")
    
    rom_range = f"(MODUL {int_to_roman(min_mod)} - {int_to_roman(max_mod)})" if min_mod != max_mod else f"(MODUL {int_to_roman(min_mod)})"

    # Spasi vertikal atas
    for _ in range(2):
        doc.add_paragraph()

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    docx_styler.set_paragraph_spacing(p_title, line_spacing=1.5, space_before_pt=0, space_after_pt=6)
    r_t1 = p_title.add_run("LAPORAN AKHIR PRAKTIKUM\n")
    r_t1.bold = True
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(14)
    r_t1.font.color.rgb = RGBColor(0, 0, 0)
    
    r_t2 = p_title.add_run(f"{course}\n")
    r_t2.bold = True
    r_t2.font.name = "Times New Roman"
    r_t2.font.size = Pt(14)
    r_t2.font.color.rgb = RGBColor(0, 0, 0)
    
    r_t3 = p_title.add_run(rom_range)
    r_t3.bold = True
    r_t3.font.name = "Times New Roman"
    r_t3.font.size = Pt(12)
    r_t3.font.color.rgb = RGBColor(0, 0, 0)

    for _ in range(4):
        doc.add_paragraph()

    # Identitas Mahasiswa
    p_id = doc.add_paragraph()
    p_id.alignment = WD_ALIGN_PARAGRAPH.CENTER
    docx_styler.set_paragraph_spacing(p_id, line_spacing=1.5, space_before_pt=0, space_after_pt=6)
    r_id_lbl = p_id.add_run("Disusun Oleh:\n")
    r_id_lbl.font.name = "Times New Roman"
    r_id_lbl.font.size = Pt(12)
    r_id_lbl.font.color.rgb = RGBColor(0, 0, 0)
    
    r_name = p_id.add_run(f"{name}\n")
    r_name.bold = True
    r_name.font.name = "Times New Roman"
    r_name.font.size = Pt(12)
    r_name.font.color.rgb = RGBColor(0, 0, 0)
    
    r_nim = p_id.add_run(f"{nim}\n")
    r_nim.bold = True
    r_nim.font.name = "Times New Roman"
    r_nim.font.size = Pt(12)
    r_nim.font.color.rgb = RGBColor(0, 0, 0)
    
    r_class = p_id.add_run(f"Kelas : {kelas}")
    r_class.font.name = "Times New Roman"
    r_class.font.size = Pt(12)
    r_class.font.color.rgb = RGBColor(0, 0, 0)

    for _ in range(5):
        doc.add_paragraph()

    # Institusi Bawah
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    docx_styler.set_paragraph_spacing(p_inst, line_spacing=1.5, space_before_pt=0, space_after_pt=4)
    r_inst = p_inst.add_run(f"{institution}\n{year}")
    r_inst.bold = True
    r_inst.font.name = "Times New Roman"
    r_inst.font.size = Pt(12)
    r_inst.font.color.rgb = RGBColor(0, 0, 0)
    
    docx_styler.add_page_break(doc)

def add_kata_pengantar_page(doc, metadata: dict):
    """Menambahkan Halaman Kata Pengantar Terstandar Akademik."""
    course = metadata.get("course_name", "Sistem Informasi Geografis")
    name = metadata.get("student_name", "Praktikan")
    
    p_head = docx_styler.add_heading_1(doc, "KATA PENGANTAR")
    set_heading_page_break_before(p_head)
    
    p1 = ("Puji dan syukur penulis panjatkan ke hadirat Tuhan Yang Maha Esa atas limpahan rahmat, petunjuk, "
          f"serta karunia-Nya sehingga pembukuan Laporan Akhir Praktikum mata kuliah {course} ini dapat diselesaikan "
          "dengan baik dan tepat pada waktunya.")
    docx_styler.add_body_paragraph(doc, p1, first_line_indent_cm=1.27)
    
    p2 = ("Penyusunan laporan akhir pembukuan ini merupakan salah satu syarat kelulusan dan evaluasi praktikum "
          f"pada mata kuliah {course}. Melalui kegiatan praktikum yang telah dilaksanakan, praktikan telah mempelajari, "
          "mempraktikkan, serta menganalisis materi teknis dari modul-modul yang telah diberikan secara komprehensif.")
    docx_styler.add_body_paragraph(doc, p2, first_line_indent_cm=1.27)
    
    p3 = ("Penulis mengucapkan terima kasih yang sebesar-besarnya kepada Dosen Pengampu mata kuliah, segenap Asisten Laboratorium "
          "yang telah sabar mendampingi dan memberikan arahan selama sesi praktikum berlangsung, serta rekan-rekan mahasiswa "
          "atas kerja sama dan diskusinya. Penulis menyadari masih terdapat keterbatasan dalam laporan ini, sehingga kritik dan saran "
          "konstruktif senantiasa diharapkan demi penyempurnaan di masa yang akan datang.")
    docx_styler.add_body_paragraph(doc, p3, first_line_indent_cm=1.27)
    
    for _ in range(2):
        doc.add_paragraph()
        
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    docx_styler.set_paragraph_spacing(p_sig, line_spacing=1.5, space_before_pt=0, space_after_pt=4)
    r1 = p_sig.add_run("Palu, 2026\n\n\n\n")
    r2 = p_sig.add_run(f"({name})")
    r2.bold = True
    r1.font.name = "Times New Roman"
    r2.font.name = "Times New Roman"
    
    docx_styler.add_page_break(doc)

def add_daftar_isi_page(doc):
    """Menambahkan Halaman Daftar Isi Otomatis Terintegrasi MS Word TOC."""
    p_head = docx_styler.add_heading_1(doc, "DAFTAR ISI")
    set_heading_page_break_before(p_head)
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    docx_styler.set_paragraph_spacing(p, line_spacing=1.0, space_before_pt=0, space_after_pt=0)
    pPr = p._p.get_or_add_pPr()
    sp = pPr.xpath('./w:spacing')
    if sp:
        pPr.remove(sp[0])
    pPr.append(parse_xml(r'<w:spacing %s w:line="1" w:lineRule="exact" w:before="0" w:after="0"/>' % nsdecls('w')))
    
    run = p.add_run()
    fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText>' % nsdecls('w'))
    fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fld3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run._r.append(fld3)

def compile_master_book(
    docx_paths: list,
    metadata: dict = None,
    template_path: str = None,
    output_path: str = None,
    modules_metadata: list = None
) -> str:
    """
    Menggabungkan beberapa dokumen .docx modul menjadi 1 berkas Pembukuan Akhir.
    Mengikuti Model 1: Bab Terpadu sesuai format.md, dengan jaminan 100% konten
    asli laporan dipertahankan secara verbatim tanpa mengubah satu kata pun.
    """
    metadata = metadata or {}
    modules_metadata = modules_metadata or []
    
    # 1. Parse seluruh file modul docx
    parsed_modules = []
    
    # Peta metadata yang dikirim langsung dari UI (nomor dan judul modul yang disesuaikan pengguna)
    meta_by_filename = {}
    for m in modules_metadata:
        fn = m.get("filename", "")
        if fn:
            meta_by_filename[fn.lower()] = m

    for idx, path in enumerate(docx_paths):
        if not os.path.exists(path):
            continue
        try:
            m_data = parse_module_docx(path)
            
            # Cek apakah ada penyesuaian dari pengguna di frontend UI
            orig_fn = os.path.basename(path)
            clean_fn = orig_fn.split("_", 1)[-1] if "_" in orig_fn else orig_fn
            user_override = meta_by_filename.get(clean_fn.lower()) or meta_by_filename.get(orig_fn.lower())
            
            if user_override:
                if user_override.get("module_number") is not None:
                    try:
                        m_data["module_number"] = int(user_override["module_number"])
                    except (ValueError, TypeError):
                        pass
                if user_override.get("module_title"):
                    m_data["module_title"] = user_override["module_title"].strip()

            if m_data["module_number"] is None:
                m_data["module_number"] = idx + 1

            parsed_modules.append(m_data)
        except Exception as e:
            print(f"[Compiler] Error membaca berkas {path}: {e}")
            
    if not parsed_modules:
        raise ValueError("Tidak ada berkas modul .docx valid yang dapat dikompilasi.")
        
    # 2. Urutkan modul berdasarkan nomor modul (1, 2, ..., N)
    parsed_modules.sort(key=lambda x: x["module_number"] if isinstance(x["module_number"], int) else 999)
    
    min_mod = parsed_modules[0]["module_number"]
    max_mod = parsed_modules[-1]["module_number"]
    
    # Ambil identitas mahasiswa dari modul pertama jika form tidak mengisi
    first_m = parsed_modules[0]
    if not metadata.get("student_name") and first_m.get("student_name"):
        metadata["student_name"] = first_m["student_name"]
    if not metadata.get("student_nim") and first_m.get("student_nim"):
        metadata["student_nim"] = first_m["student_nim"]
    if not metadata.get("student_class") and first_m.get("student_class"):
        metadata["student_class"] = first_m["student_class"]
    if not metadata.get("course_name") and first_m.get("course_name"):
        metadata["course_name"] = first_m["course_name"]

    # 3. Inisialisasi dokumen master dari base_template.docx
    base_tpl = template_path
    if not base_tpl or not os.path.exists(base_tpl):
        base_tpl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "base_template.docx")
        if not os.path.exists(base_tpl):
            base_tpl = r"C:\Users\tedon\.gemini\config\skills\yuss-males-laprak\templates\base_template.docx"

    if os.path.exists(base_tpl):
        doc = docx.Document(base_tpl)
        for p in list(doc.paragraphs):
            p._p.getparent().remove(p._p)
    else:
        doc = docx.Document()
        docx_styler.set_document_margins(doc, 4.0, 4.0, 3.0, 3.0)
        docx_styler.setup_academic_styles(doc)

    docx_styler.setup_academic_numbering(doc)
    composer = docxcompose.composer.Composer(doc)
    composer.reset_reference_mapping()

    # ==========================================================
    # HALAMAN 1: SAMPUL UTAMA PEMBUKUAN
    # ==========================================================
    add_master_cover_page(doc, metadata, min_mod, max_mod)

    # ==========================================================
    # HALAMAN 2: KATA PENGANTAR (OPSIONAL, DEFAULT AKTIF)
    # ==========================================================
    if metadata.get("include_kata_pengantar", True):
        add_kata_pengantar_page(doc, metadata)

    # ==========================================================
    # HALAMAN 3: DAFTAR ISI (OPSIONAL, DEFAULT AKTIF)
    # ==========================================================
    if metadata.get("include_daftar_isi", True):
        add_daftar_isi_page(doc)

    # ==========================================================
    # BAB II: LANDASAN TEORI (HALAMAN BARU)
    # ==========================================================
    p_b2 = docx_styler.add_heading_1(doc, "BAB II \nLANDASAN TEORI")
    set_heading_page_break_before(p_b2)
    docx_styler.add_heading_2(doc, "2.1\tLandasan Teori")
    
    for mod in parsed_modules:
        m_num = mod["module_number"]
        m_title = mod["module_title"] or f"Modul {m_num}"
        elems = clean_section_elements(mod["bab2_elements"])
        if not elems:
            continue
            
        composer._create_style_id_mapping(mod["doc_ref"])
        
        # Cek apakah elemen pertama adalah heading sub-bab modul (2.1.X)
        first_el = elems[0]
        has_h3 = False
        sub_title = m_title
        if first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            m_h3 = re.search(r'2\.1\.' + str(m_num) + r'[\s\t]*(.*)', p_obj.text.strip())
            if m_h3:
                has_h3 = True
                if m_h3.group(1).strip():
                    sub_title = m_h3.group(1).strip()
            elif p_obj.style and p_obj.style.name.startswith("Heading"):
                has_h3 = True
                sub_title = p_obj.text.strip()
                
        # Selalu tambahkan Heading 3 standar akademik format.md
        docx_styler.add_heading_3(doc, f"\t2.1.{m_num}\t{sub_title}")
        
        # Lewati heading lama jika sudah diganti agar tidak dobel
        content_elems = elems[1:] if has_h3 else elems
        if not has_h3 and first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            if is_same_title(p_obj.text.strip(), m_title):
                content_elems = elems[1:]
        for el in content_elems:
            append_element_verbatim(doc, el, mod["doc_ref"], composer)

    # ==========================================================
    # BAB III: LANGKAH KERJA (HALAMAN BARU)
    # ==========================================================
    p_b3 = docx_styler.add_heading_1(doc, "BAB III \nLANGKAH KERJA")
    set_heading_page_break_before(p_b3)
    docx_styler.add_heading_2(doc, "3.1\tLangkah Kerja")
    
    for mod in parsed_modules:
        m_num = mod["module_number"]
        m_title = mod["module_title"] or f"Modul {m_num}"
        elems = clean_section_elements(mod["bab3_elements"])
        if not elems:
            continue
            
        composer._create_style_id_mapping(mod["doc_ref"])
        
        first_el = elems[0]
        has_h3 = False
        sub_title = m_title
        if first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            m_h3 = re.search(r'3\.1\.' + str(m_num) + r'[\s\t]*(.*)', p_obj.text.strip())
            if m_h3:
                has_h3 = True
                if m_h3.group(1).strip():
                    sub_title = m_h3.group(1).strip()
            elif p_obj.style and p_obj.style.name.startswith("Heading"):
                has_h3 = True
                sub_title = p_obj.text.strip()
                
        docx_styler.add_heading_3(doc, f"\t3.1.{m_num}\t{sub_title}")
        
        content_elems = elems[1:] if has_h3 else elems
        if not has_h3 and first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            if is_same_title(p_obj.text.strip(), m_title):
                content_elems = elems[1:]
        for el in content_elems:
            append_element_verbatim(doc, el, mod["doc_ref"], composer)

    # ==========================================================
    # BAB IV: HASIL DAN PEMBAHASAN (HALAMAN BARU)
    # ==========================================================
    p_b4 = docx_styler.add_heading_1(doc, "BAB IV \nHASIL DAN PEMBAHASAN")
    set_heading_page_break_before(p_b4)
    docx_styler.add_heading_2(doc, "4.1\tHasil dan Pembahasan")
    
    for mod in parsed_modules:
        m_num = mod["module_number"]
        m_title = mod["module_title"] or f"Modul {m_num}"
        elems = clean_section_elements(mod["bab4_elements"])
        if not elems:
            continue
            
        composer._create_style_id_mapping(mod["doc_ref"])
        
        first_el = elems[0]
        has_h3 = False
        sub_title = m_title
        if first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            m_h3 = re.search(r'4\.1\.' + str(m_num) + r'[\s\t]*(.*)', p_obj.text.strip())
            if m_h3:
                has_h3 = True
                if m_h3.group(1).strip():
                    sub_title = m_h3.group(1).strip()
            elif p_obj.style and p_obj.style.name.startswith("Heading"):
                has_h3 = True
                sub_title = p_obj.text.strip()
                
        docx_styler.add_heading_3(doc, f"\t4.1.{m_num}\t{sub_title}")
        
        content_elems = elems[1:] if has_h3 else elems
        if not has_h3 and first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, mod["doc_ref"])
            if is_same_title(p_obj.text.strip(), m_title):
                content_elems = elems[1:]
        for el in content_elems:
            append_element_verbatim(doc, el, mod["doc_ref"], composer)

    # ==========================================================
    # BAB V: PENUTUP (HALAMAN BARU)
    # ==========================================================
    p_b5 = docx_styler.add_heading_1(doc, "BAB V \nPENUTUP")
    set_heading_page_break_before(p_b5)
    docx_styler.add_heading_2(doc, "5.1\tKesimpulan")
    
    # Himpun kesimpulan kumulatif unik (5.1.1, 5.1.2, ..., 5.1.N)
    conclusions_by_num = {}
    for mod in parsed_modules:
        m_num = mod["module_number"]
        elems = clean_section_elements(mod["bab5_elements"])
        if not elems:
            continue
            
        curr_num = None
        curr_elems = []
        for el in elems:
            txt = ""
            if el.tag.endswith('p'):
                txt = docx.text.paragraph.Paragraph(el, mod["doc_ref"]).text.strip()
            m = re.search(r'5\.1\.([0-9]+)', txt)
            if m:
                if curr_num and curr_elems:
                    conclusions_by_num[curr_num] = (curr_elems, mod["doc_ref"])
                curr_num = int(m.group(1))
                curr_elems = [el]
            else:
                curr_elems.append(el)
        if curr_num and curr_elems:
            conclusions_by_num[curr_num] = (curr_elems, mod["doc_ref"])
        elif not curr_num and elems:
            conclusions_by_num[m_num] = (elems, mod["doc_ref"])
            
    for num in sorted(conclusions_by_num.keys()):
        raw_elems, doc_src = conclusions_by_num[num]
        elems = clean_section_elements(raw_elems)
        if not elems:
            continue
        composer._create_style_id_mapping(doc_src)
        
        # Cari judul modul dari parsed_modules jika ada
        mod_match = next((m for m in parsed_modules if m["module_number"] == num), None)
        default_sub_title = mod_match["module_title"] if mod_match and mod_match.get("module_title") else f"Kesimpulan Modul {num}"

        first_el = elems[0]
        has_h3 = False
        sub_title = default_sub_title
        if first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, doc_src)
            txt_p = p_obj.text.strip()
            m_h3 = re.search(r'5\.1\.' + str(num) + r'[\s\t]*(.*)', txt_p)
            if m_h3:
                has_h3 = True
                if m_h3.group(1).strip():
                    sub_title = m_h3.group(1).strip()
            elif p_obj.style and p_obj.style.name.startswith("Heading"):
                has_h3 = True
                sub_title = txt_p
                
        docx_styler.add_heading_3(doc, f"\t5.1.{num}\t{sub_title}")
        
        content_elems = elems[1:] if has_h3 else elems
        if not has_h3 and first_el.tag.endswith('p'):
            p_obj = docx.text.paragraph.Paragraph(first_el, doc_src)
            txt_p = p_obj.text.strip()
            if is_same_title(txt_p, sub_title) or (len(txt_p) < 40 and "kesimpulan" in txt_p.lower()):
                content_elems = elems[1:]
        for el in content_elems:
            append_element_verbatim(doc, el, doc_src, composer)

    # ==========================================================
    # DAFTAR PUSTAKA GABUNGAN (HALAMAN BARU)
    # ==========================================================
    p_dp = docx_styler.add_heading_1(doc, "DAFTAR PUSTAKA")
    set_heading_page_break_before(p_dp)
    
    all_bib_entries = []
    seen = set()
    
    for mod in parsed_modules:
        for entry in mod["daftar_pustaka_entries"]:
            clean_entry = entry.strip()
            if not clean_entry or is_parent_chapter_heading(clean_entry):
                continue
            # Normalisasi untuk deduplikasi unik
            norm_key = re.sub(r'[^a-zA-Z0-9]', '', clean_entry.lower())
            if norm_key not in seen:
                seen.add(norm_key)
                all_bib_entries.append(clean_entry)
                
    # Urutkan secara alfabetis sesuai aturan APA 7th Edition
    all_bib_entries.sort()
    
    for bib in all_bib_entries:
        docx_styler.add_bibliography_entry(doc, bib)
        
    # Aktifkan updateFields otomatis pada Word settings agar Daftar Isi (TOC) otomatis ter-render saat dibuka
    try:
        uf = OxmlElement('w:updateFields')
        uf.set(qn('w:val'), 'true')
        doc.settings.element.append(uf)
    except Exception as e:
        print(f"[Compiler] Warning: Gagal menambahkan updateFields: {e}")

    # 4. Normalisasi penomoran list agar selalu restart di 1 saat ganti paragraf narasi
    renumber_lists_in_doc(doc)

    # 5. Simpan dokumen output
    if not output_path:
        nim = metadata.get("student_nim", "laprak").lower().replace(" ", "_")
        course_clean = metadata.get("course_name", "prak").lower().replace(" ", "_")
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "generated_docs")
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, f"pembukuan_{nim}_{course_clean}.docx")
        
    doc.save(output_path)
    print(f"[Compiler] Sukses membuat berkas Pembukuan Akhir Verbatim: {output_path}")
    return output_path
