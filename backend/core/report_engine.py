"""
report_engine.py
Mesin kompilasi Laporan Praktikum (.docx) berstandar akademik tinggi,
patuh 100% pada aturan d:\\WEB LAPRAK\\format.md:
- Kertas A4, Margin 4-4-3-3 cm, Times New Roman 12 pt, 1.5 Line Spacing
- Page Break mutlak antar-bab (Halaman 1: Cover, Halaman 2: Bab II, Bab III, Bab IV, Bab V, Daftar Pustaka)
- Penomoran sub-bab dinamis mengikuti nomor modul (2.1.N, 3.1.N, 4.1.N, 5.1.N)
- Aturan Bab V modul terusan (N > 1): langsung mulai dengan Heading 3 tanpa parent heading
- Bab IV dinamis mengikuti jumlah poin luaran di data
- Dukungan gambar asli (screenshot praktikan) atau fallback ke placeholder abu-abu
- Otomatis cetak miring istilah non-KBBI / bahasa asing
"""

import os
import sys
import re

# Tambahkan direktori core ke sys.path jika belum ada
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import docx_styler

def int_to_roman(num: int) -> str:
    """Mengubah angka bulat menjadi angka romawi."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    try:
        n = int(num)
    except (ValueError, TypeError):
        return str(num)
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num or str(num)

def build_report_document(data: dict, output_path: str = None, template_path: str = None, images_map: dict = None):
    """
    Membangun dokumen Word (.docx) lengkap dari data JSON laporan praktikum.
    
    :param data: Dictionary berisi struktur laporan (sesuai format.md)
    :param output_path: Path tujuan berkas .docx yang dihasilkan
    :param template_path: Path ke file template Word dasar (default: backend/templates/base_template.docx)
    :param images_map: Dictionary pemetaan ID placeholder ke path/bytes gambar yang diunggah
    :return: Instance Document (python-docx)
    """
    images_map = images_map or {}

    # 1. Inisialisasi dokumen dari template
    if not template_path:
        default_tpl = os.path.join(os.path.dirname(current_dir), "templates", "base_template.docx")
        if os.path.exists(default_tpl):
            template_path = default_tpl

    doc = docx_styler.create_document(template_path)

    # 2. Ekstraksi Metadata Laporan
    module_num = data.get("module_number", 1)
    try:
        module_num_int = int(module_num)
    except (ValueError, TypeError):
        module_num_int = 1

    module_title = data.get("module_title", "Laporan Praktikum")
    nama = data.get("student_name", "MOH. YUSFI LAKHAFIDUN")
    nim = data.get("student_nim", "F5512520089")
    kelas = data.get("student_class", "Informatika C")
    
    # Format judul Halaman Sampul (Cover)
    roman_num = int_to_roman(module_num_int)
    header_title = data.get("header_title")
    if not header_title:
        header_title = f"MODUL PRAKTIKUM {roman_num}\n({module_title.upper()})"

    # Cek apakah modul merupakan modul mandiri atau modul 1
    has_parent_headings = data.get("has_parent_headings", (module_num_int == 1))

    # ==========================================================
    # HALAMAN 1: HALAMAN SAMPUL (IDENTITAS)
    # ==========================================================
    docx_styler.add_identity_header(doc, header_title, nama, nim, kelas, standalone_cover=True)
    docx_styler.add_page_break(doc)

    # ==========================================================
    # BAB II: LANDASAN TEORI (HALAMAN 2 BARU)
    # ==========================================================
    bab2 = data.get("bab2", {})
    bab2_has_parent = bab2.get("has_parent_headings", has_parent_headings)
    bab2_chapter_title = bab2.get("chapter_title", "BAB II \nLANDASAN TEORI")
    bab2_parent_title = bab2.get("parent_title", "Landasan Teori")
    bab2_title = bab2.get("subbab_title", module_title)

    if bab2_has_parent:
        docx_styler.add_heading_1(doc, bab2_chapter_title)
        docx_styler.add_heading_2(doc, f"2.1\t{bab2_parent_title}")

    docx_styler.add_heading_3(doc, f"\t2.1.{module_num_int}\t{bab2_title}")

    bab2_num_id = None
    in_list_block = False
    base_level_is_shifted = False
    has_l1 = False
    has_l2 = False
    current_content_indent_cm = 3.29

    for item in bab2.get("content", []):
        if isinstance(item, str):
            in_list_block = False
            base_level_is_shifted = False
            has_l1 = False
            has_l2 = False
            docx_styler.add_body_paragraph(doc, item, first_line_indent_cm=1.27, left_indent_cm=1.27)
        elif isinstance(item, dict):
            item_type = item.get("type", "paragraph")
            text = item.get("text", "")
            raw_level = item.get("level", 1)
            
            if item_type == "list":
                prefix = item.get("prefix", "1.").strip()
                list_type = item.get("list_type", "number")
                base_indent_cm = item.get("base_indent_cm", 1.27)
                text_indent_cm = item.get("text_indent_cm", 0.75)
                
                # Auto-reset jika diselingi teks narasi / subjudul
                if not in_list_block or item.get("restart"):
                    bab2_num_id = docx_styler.create_numbered_list_id(doc, pattern=2)
                    in_list_block = True
                    has_l1 = False
                    has_l2 = False
                    # Jika list baru dimulai langsung dengan huruf (a., b., c.), maka seluruh list utama ini tergeser
                    import re
                    if re.match(r'^[a-zA-Z]\.', prefix) or raw_level == 2:
                        base_level_is_shifted = True
                    else:
                        base_level_is_shifted = False
                
                # Normalisasi Level
                effective_level = raw_level
                if list_type != "bullet":
                    if base_level_is_shifted:
                        # Jika list utama aslinya huruf, seluruh huruf sejajar menjadi Level 1 (1., 2., dst)
                        if re.match(r'^[a-zA-Z]\.', prefix) or effective_level == 2:
                            effective_level = 1
                        elif effective_level >= 3 or re.match(r'^[0-9]+\)', prefix):
                            effective_level = 2
                    else:
                        # List normal diawali angka 1.
                        if not has_l1:
                            effective_level = 1
                        elif effective_level == 2 and not has_l1:
                            effective_level = 1
                        elif effective_level >= 3 and not has_l2:
                            effective_level = 2 if has_l1 else 1

                if raw_level == 1 or (prefix and prefix[0].isdigit()):
                    base_level_is_shifted = False
                if effective_level == 1:
                    has_l1 = True
                    has_l2 = False
                elif effective_level == 2:
                    has_l2 = True

                current_content_indent_cm = base_indent_cm + (effective_level - 1) * text_indent_cm + text_indent_cm
                docx_styler.add_list_item(
                    doc, text, prefix=prefix, level=effective_level, num_id=bab2_num_id,
                    list_type=list_type, base_indent_cm=base_indent_cm, text_indent_cm=text_indent_cm
                )
            elif item_type == "list_body":
                base_ind = item.get("base_indent_cm", 1.27)
                txt_ind = item.get("text_indent_cm", 0.75)
                first_ind = item.get("first_line_indent_cm", 0)
                docx_styler.add_list_body_paragraph(
                    doc, text, level=raw_level, base_indent_cm=base_ind,
                    text_indent_cm=txt_ind, first_line_indent_cm=first_ind
                )
            elif item_type == "subheading":
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                docx_styler.add_body_paragraph(doc, f"**{text}**", first_line_indent_cm=0, left_indent_cm=2.54)
            elif item_type == "page_break":
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                docx_styler.add_page_break(doc)
            else:
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                first_ind = item.get("first_line_indent_cm", 1.27)
                left_ind = item.get("left_indent_cm", 1.27)
                docx_styler.add_body_paragraph(doc, text, first_line_indent_cm=first_ind, left_indent_cm=left_ind)

    # ==========================================================
    # BAB III: LANGKAH KERJA (HALAMAN BARU)
    # ==========================================================
    docx_styler.add_page_break(doc)
    bab3 = data.get("bab3", {})
    bab3_has_parent = bab3.get("has_parent_headings", has_parent_headings)
    bab3_chapter_title = bab3.get("chapter_title", "BAB III \nLANGKAH KERJA")
    bab3_parent_title = bab3.get("parent_title", "Langkah Kerja")
    bab3_title = bab3.get("subbab_title", module_title)

    if bab3_has_parent:
        docx_styler.add_heading_1(doc, bab3_chapter_title)
        docx_styler.add_heading_2(doc, f"3.1\t{bab3_parent_title}")

    docx_styler.add_heading_3(doc, f"\t3.1.{module_num_int}\t{bab3_title}")

    bab3_num_id = docx_styler.create_numbered_list_id(doc, pattern=1)
    in_list_block = True
    base_level_is_shifted = False
    has_l1 = False
    has_l2 = False
    current_content_indent_cm = 3.29

    for idx, item in enumerate(bab3.get("content", [])):
        if isinstance(item, str):
            in_list_block = False
            base_level_is_shifted = False
            has_l1 = False
            has_l2 = False
            docx_styler.add_body_paragraph(doc, item, first_line_indent_cm=0, left_indent_cm=current_content_indent_cm)
        elif isinstance(item, dict):
            item_type = item.get("type", "paragraph")
            text = item.get("text", "")
            raw_level = item.get("level", 1)
            img_id = item.get("id", f"bab3_img_{idx}")
            
            if item_type == "heading_step":
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                docx_styler.add_body_paragraph(doc, f"**{text}**", first_line_indent_cm=0, left_indent_cm=2.54)
            elif item_type == "list":
                prefix = item.get("prefix", "1.").strip()
                list_type = item.get("list_type", "number")
                base_indent_cm = item.get("base_indent_cm", 2.54)
                text_indent_cm = item.get("text_indent_cm", 0.75)
                
                # Auto-reset jika diselingi teks narasi / heading step
                if not in_list_block or item.get("restart"):
                    bab3_num_id = docx_styler.create_numbered_list_id(doc, pattern=1)
                    in_list_block = True
                    has_l1 = False
                    has_l2 = False
                    import re
                    if re.match(r'^[a-zA-Z]\.', prefix) or raw_level == 2:
                        base_level_is_shifted = True
                    else:
                        base_level_is_shifted = False
                elif not has_l1 and (raw_level == 2 or (prefix and prefix[0].isalpha())):
                    base_level_is_shifted = True
                
                # Aturan Hierarki Mutlak: 1. > a. > 1) (dilarang skip langsung ke a.)
                effective_level = raw_level
                if list_type != "bullet":
                    import re
                    if base_level_is_shifted:
                        # Jika list utama asdos memakai a., b., c., maka seluruh butir utama sejajar menjadi Level 1 (1., 2., dst)
                        if re.match(r'^[a-zA-Z]\.', prefix) or effective_level == 2:
                            effective_level = 1
                        elif effective_level >= 3 or re.match(r'^[0-9]+\)', prefix):
                            effective_level = 2
                    else:
                        if not has_l1:
                            effective_level = 1
                        elif effective_level == 2 and not has_l1:
                            effective_level = 1
                        elif effective_level >= 3 and not has_l2:
                            effective_level = 2 if has_l1 else 1

                if raw_level == 1 or (prefix and prefix[0].isdigit()):
                    base_level_is_shifted = False
                if effective_level == 1:
                    has_l1 = True
                    has_l2 = False
                elif effective_level == 2:
                    has_l2 = True

                current_content_indent_cm = base_indent_cm + (effective_level - 1) * text_indent_cm + text_indent_cm
                docx_styler.add_list_item(
                    doc, text, prefix=prefix, level=effective_level, num_id=bab3_num_id,
                    list_type=list_type, base_indent_cm=base_indent_cm, text_indent_cm=text_indent_cm
                )
            elif item_type == "list_body":
                base_ind = item.get("base_indent_cm", 2.54)
                txt_ind = item.get("text_indent_cm", 0.75)
                first_ind = item.get("first_line_indent_cm", 0)
                docx_styler.add_list_body_paragraph(
                    doc, text, level=raw_level, base_indent_cm=base_ind,
                    text_indent_cm=txt_ind, first_line_indent_cm=first_ind
                )
            elif item_type == "placeholder":
                indent = item.get("left_indent_cm", current_content_indent_cm)
                img_data = images_map.get(img_id) or images_map.get(text)
                docx_styler.add_image_or_placeholder(
                    doc, description=text,
                    image_path=img_data if isinstance(img_data, str) else None,
                    image_bytes=img_data if isinstance(img_data, bytes) else None,
                    left_indent_cm=indent
                )
            elif item_type == "page_break":
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                docx_styler.add_page_break(doc)
            else:
                in_list_block = False
                base_level_is_shifted = False
                has_l1 = False
                has_l2 = False
                indent = item.get("left_indent_cm", current_content_indent_cm)
                docx_styler.add_body_paragraph(doc, text, first_line_indent_cm=0, left_indent_cm=indent)

    # ==========================================================
    # BAB IV: HASIL DAN PEMBAHASAN (HALAMAN BARU)
    # ==========================================================
    docx_styler.add_page_break(doc)
    bab4 = data.get("bab4", {})
    bab4_has_parent = bab4.get("has_parent_headings", has_parent_headings)
    bab4_chapter_title = bab4.get("chapter_title", "BAB IV \nHASIL DAN PEMBAHASAN")
    bab4_parent_title = bab4.get("parent_title", "Hasil dan Pembahasan")
    bab4_title = bab4.get("subbab_title", module_title)

    if bab4_has_parent:
        docx_styler.add_heading_1(doc, bab4_chapter_title)
        docx_styler.add_heading_2(doc, f"4.1\t{bab4_parent_title}")

    docx_styler.add_heading_3(doc, f"\t4.1.{module_num_int}\t{bab4_title}")

    bab4_num_id = docx_styler.create_numbered_list_id(doc)
    current_content_indent_cm = 3.29

    for idx, item in enumerate(bab4.get("content", [])):
        if isinstance(item, str):
            docx_styler.add_body_paragraph(doc, item, first_line_indent_cm=0, left_indent_cm=current_content_indent_cm)
        elif isinstance(item, dict):
            item_type = item.get("type", "paragraph")
            text = item.get("text", "")
            level = item.get("level", 1)
            img_id = item.get("id", f"bab4_img_{idx}")
            if item.get("restart"):
                bab4_num_id = docx_styler.create_numbered_list_id(doc)
            
            if item_type == "list":
                prefix = item.get("prefix", f"{idx + 1}.")
                list_type = item.get("list_type", "number")
                base_indent_cm = item.get("base_indent_cm", 2.54)
                text_indent_cm = item.get("text_indent_cm", 0.75)
                current_content_indent_cm = base_indent_cm + (level - 1) * text_indent_cm + text_indent_cm
                docx_styler.add_list_item(
                    doc, text, prefix=prefix, level=level, num_id=bab4_num_id,
                    list_type=list_type, base_indent_cm=base_indent_cm, text_indent_cm=text_indent_cm
                )
            elif item_type == "list_body":
                base_ind = item.get("base_indent_cm", 2.54)
                txt_ind = item.get("text_indent_cm", 0.75)
                first_ind = item.get("first_line_indent_cm", 0)
                docx_styler.add_list_body_paragraph(
                    doc, text, level=level, base_indent_cm=base_ind,
                    text_indent_cm=txt_ind, first_line_indent_cm=first_ind
                )
            elif item_type == "placeholder":
                indent = item.get("left_indent_cm", current_content_indent_cm)
                img_data = images_map.get(img_id) or images_map.get(text)
                docx_styler.add_image_or_placeholder(
                    doc, description=text,
                    image_path=img_data if isinstance(img_data, str) else None,
                    image_bytes=img_data if isinstance(img_data, bytes) else None,
                    left_indent_cm=indent
                )
            elif item_type == "page_break":
                docx_styler.add_page_break(doc)
            else:
                indent = item.get("left_indent_cm", current_content_indent_cm)
                docx_styler.add_body_paragraph(doc, text, first_line_indent_cm=0, left_indent_cm=indent)

    # ==========================================================
    # BAB V: PENUTUP (HALAMAN BARU)
    # ==========================================================
    docx_styler.add_page_break(doc)
    bab5 = data.get("bab5", {})
    current_num = bab5.get("current_number", f"5.1.{module_num_int}").strip()
    
    # Aturan Terusan: Jika sub-bab > 5.1.1 (N > 1), TIDAK USAH memakai header BAB V PENUTUP dan 5.1 Kesimpulan
    has_bab5_parent = bab5.get("has_parent_headings", (current_num == "5.1.1"))
    if has_bab5_parent:
        docx_styler.add_heading_1(doc, "BAB V \nPENUTUP")
        docx_styler.add_heading_2(doc, "5.1\tKesimpulan")

    current_conclusion = bab5.get("current_conclusion", "").strip()
    current_title = bab5.get("current_title", module_title).strip()
    docx_styler.add_heading_3(doc, f"\t{current_num}\t{current_title}")
    docx_styler.add_conclusion_paragraph(doc, current_conclusion)

    # ==========================================================
    # DAFTAR PUSTAKA (HALAMAN BARU)
    # ==========================================================
    daftar_pustaka = data.get("daftar_pustaka", [])
    if daftar_pustaka:
        docx_styler.add_page_break(doc)
        docx_styler.add_heading_1(doc, "DAFTAR PUSTAKA")
        for ref in daftar_pustaka:
            if isinstance(ref, str):
                docx_styler.add_bibliography_entry(doc, ref)
            elif isinstance(ref, dict):
                auth = ref.get("author", "")
                yr = ref.get("year", "")
                ttl = ref.get("title", "")
                src = ref.get("source", "")
                url = ref.get("url", "")
                formatted_ref = f"{auth} ({yr}). {ttl}. *{src}*. {url}".strip()
                docx_styler.add_bibliography_entry(doc, formatted_ref)

    # Simpan ke file output jika path diberikan
    if output_path:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        try:
            doc.save(output_path)
            print(f"[Sukses] Dokumen laporan praktikum berhasil disimpan di: {output_path}")
        except PermissionError:
            fallback = output_path.replace(".docx", "_revisi.docx")
            doc.save(fallback)
            print(f"[Peringatan File Terkunci] Disimpan ke fallback: {fallback}")
            output_path = fallback

    return doc
