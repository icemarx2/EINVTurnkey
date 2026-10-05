#!/usr/bin/env python3
"""
Generate Version B of the Turnkey pre-launch self-test document using lxml:
- Starts directly from pristine 5440_original.odt (downloaded straight from MOF).
- Keeps the entire Appendix (附錄, Tables 10-12, all 32+ pages) 100% intact.
- Uses lxml to modify ONLY the required text and insert image frames.
- Preserves all original styles, fonts, margins, page breaks, and table widths.
"""

import os
import zipfile
from lxml import etree

DOCS_DIR = "/invoice/EINVTurnkey/docs"
SRC_ODT = os.path.join(DOCS_DIR, "5440_original.odt")
OUT_ODT = os.path.join(DOCS_DIR, "03_電子發票Turnkey上線前自行檢測作業_4.8.1_Full_vB.odt")

IMG_B2B = "/invoice/EINVTurnkey/Pictures/proof_b2b.png"
IMG_E0402 = "/invoice/EINVTurnkey/Pictures/proof_e0402.png"

# Real screenshots supplied by the operator. Only files that exist are embedded.
EVIDENCE_DIR = "/invoice/EINVTurnkey/docs/evidence"
MAX_W_CM, MAX_H_CM = 15.5, 11.0
USED_EVIDENCE = []   # (zip_name, path)
MISSING_EVIDENCE = []


def png_size(path):
    import struct
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def add_evidence(cell, name, ns):
    """Append `docs/evidence/<name>.png` to a table cell, scaled to fit, aspect preserved."""
    path = os.path.join(EVIDENCE_DIR, name + ".png")
    if not os.path.exists(path):
        MISSING_EVIDENCE.append(name)
        return
    w, h = png_size(path)
    scale = min(MAX_W_CM / w, MAX_H_CM / h)
    wc, hc = round(w * scale, 2), round(h * scale, 2)
    T, D, S, X = (f"{{{ns[k]}}}" for k in ("text", "draw", "svg", "xlink"))
    zip_name = f"Pictures/ev_{name}.png"
    USED_EVIDENCE.append((zip_name, path))
    p = etree.SubElement(cell, f"{T}p", attrib={f"{T}style-name": "Standard"})
    fr = etree.SubElement(p, f"{D}frame", attrib={
        f"{D}name": f"Ev_{name}", f"{T}anchor-type": "as-char",
        f"{S}width": f"{wc}cm", f"{S}height": f"{hc}cm", f"{D}z-index": "0"})
    etree.SubElement(fr, f"{D}image", attrib={
        f"{X}href": zip_name, f"{X}type": "simple", f"{X}show": "embed", f"{X}actuate": "onLoad"})

def make_element(tag, parent=None, text=None, attrib=None, nsmap=None):
    if attrib is None:
        attrib = {}
    elem = etree.Element(tag, attrib=attrib, nsmap=nsmap)
    if text is not None:
        elem.text = text
    if parent is not None:
        parent.append(elem)
    return elem

def main():
    print(f"Reading pristine template: {SRC_ODT}")
    with zipfile.ZipFile(SRC_ODT, "r") as zin:
        manifest_xml = zin.read("META-INF/manifest.xml").decode("utf-8")
        content_bytes = zin.read("content.xml")
        other_files = {item.filename: zin.read(item.filename) for item in zin.infolist() if item.filename not in ["META-INF/manifest.xml", "content.xml"]}

    # 1. Update manifest
    manifest_entries = """  <manifest:file-entry manifest:full-path="Pictures/proof_b2b.png" manifest:media-type="image/png"/>
  <manifest:file-entry manifest:full-path="Pictures/proof_e0402.png" manifest:media-type="image/png"/>
</manifest:manifest>"""
    manifest_xml = manifest_xml.replace("</manifest:manifest>", manifest_entries)

    # 2. Parse content.xml
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.fromstring(content_bytes, parser)
    ns = tree.nsmap
    
    TEXT = f"{{{ns['text']}}}"
    TABLE = f"{{{ns['table']}}}"
    DRAW = f"{{{ns['draw']}}}"
    SVG = f"{{{ns['svg']}}}"
    XLINK = f"{{{ns['xlink']}}}"

    # Helper: set text of first text:p in a cell
    def set_first_p(cell, text):
        ps = cell.xpath('./text:p', namespaces=ns)
        if ps:
            ps[0].text = text
            for child in list(ps[0]):
                ps[0].remove(child)
        else:
            p = etree.SubElement(cell, f"{TEXT}p")
            p.text = text

    # Helper: replace all paragraphs in cell with new list of (style, text)
    def set_cell_paragraphs(cell, para_list):
        for child in list(cell):
            cell.remove(child)
        for style, text in para_list:
            p = etree.SubElement(cell, f"{TEXT}p", attrib={f"{TEXT}style-name": style} if style else {})
            p.text = text

    # --- COVER DATE ---
    for p in tree.xpath('//text:p', namespaces=ns):
        if p.text and "中華民國 115年 8 月 20 日" in p.text:
            p.text = p.text.replace("中華民國 115年 8 月 20 日", "中華民國 115 年 09 月 24 日")

    # --- TABLE 2: 申請檢測業者資訊 ---
    t2 = tree.xpath('//table:table[@table:name="表格2"]', namespaces=ns)[0]
    t2_rows = t2.xpath('.//table:table-row', namespaces=ns)
    
    # R0: 營業人名稱 -> 奧銳有限公司
    set_first_p(t2_rows[0].xpath('./table:table-cell', namespaces=ns)[1], "奧銳有限公司")
    # R1: 統一編號 -> 00015555
    set_first_p(t2_rows[1].xpath('./table:table-cell', namespaces=ns)[1], "00015555")
    
    # R2: 申請業者類型 -> ☑營業人 (B2B交換)　　□加值中心
    cell_r2 = t2_rows[2].xpath('./table:table-cell', namespaces=ns)[1]
    p_r2 = cell_r2.xpath('./text:p', namespaces=ns)[0]
    for child in list(p_r2):
        p_r2.remove(child)
    p_r2.text = None
    span1 = etree.SubElement(p_r2, f"{TEXT}span", attrib={f"{TEXT}style-name": "T4"})
    span1.text = "☑"
    span2 = etree.SubElement(p_r2, f"{TEXT}span", attrib={f"{TEXT}style-name": "T7"})
    span2.text = "營業人 (B2B交換)　　"
    span3 = etree.SubElement(p_r2, f"{TEXT}span", attrib={f"{TEXT}style-name": "T4"})
    span3.text = "□"
    span4 = etree.SubElement(p_r2, f"{TEXT}span", attrib={f"{TEXT}style-name": "T7"})
    span4.text = "加值中心"

    # R3: 檢測人員姓名 -> 王世全, 聯絡電話 -> 0903888022
    set_first_p(t2_rows[3].xpath('./table:table-cell', namespaces=ns)[1], "王世全")
    set_first_p(t2_rows[3].xpath('./table:table-cell', namespaces=ns)[3], "0903888022")

    # R4: 電子郵件Email -> paul@wang.net
    set_first_p(t2_rows[4].xpath('./table:table-cell', namespaces=ns)[1], "paul@wang.net")

    # R5: 完成檢測日期 -> 115 年 09 月 24 日
    cell_r5 = t2_rows[5].xpath('./table:table-cell', namespaces=ns)[1]
    p_r5 = cell_r5.xpath('./text:p', namespaces=ns)[0]
    for child in list(p_r5):
        p_r5.remove(child)
    p_r5.text = None
    s_y1 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T9"})
    s_y1.text = " 115 "
    s_y2 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T8"})
    s_y2.text = "年"
    s_m1 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T9"})
    s_m1.text = " 09 "
    s_m2 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T8"})
    s_m2.text = "月"
    s_d1 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T9"})
    s_d1.text = " 24 "
    s_d2 = etree.SubElement(p_r5, f"{TEXT}span", attrib={f"{TEXT}style-name": "T8"})
    s_d2.text = "日"

    # --- TABLE 3: 前置作業檢測項目 ---
    t3 = tree.xpath('//table:table[@table:name="表格3"]', namespaces=ns)[0]
    t3_rows = t3.xpath('.//table:table-row', namespaces=ns)

    # Item 1 Check & Explanation
    set_cell_paragraphs(t3_rows[1].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P47", "☑非加值中心")
    ])
    set_cell_paragraphs(t3_rows[2].xpath('./table:table-cell', namespaces=ns)[0], [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：本公司於 ERP 資料庫建立字軌配號簿（einv_track_quota），登錄大平台核配之期別、字軌英文代碼及起訖號。開立發票時由資料庫函式 allocate_next_invoice_number 僅自該期「啟用中且未超出訖號」之區間取號，無可用區間即拒絕開立。另每日執行發票檢核程式（python -m erp_bridge check），逐筆檢核已開立發票號碼格式（2碼英文+8碼數字）、是否落於已登錄且啟用之字軌區間（含非當期字軌），異常時於報告列示並以非零代碼結束，通知管理者處理。佐證畫面如下（字軌配號簿與檢核報告[1]）：")
    ])
    add_evidence(t3_rows[2].xpath('./table:table-cell', namespaces=ns)[0], 'item1_track', ns)

    # Item 2 Check & Explanation
    set_cell_paragraphs(t3_rows[3].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P47", "☑非加值中心")
    ])
    set_cell_paragraphs(t3_rows[4].xpath('./table:table-cell', namespaces=ns)[0], [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：取號函式以列鎖定（FOR UPDATE）逐號遞增，避免同時開立取得相同號碼；並於訂單表建立發票號碼唯一索引（uq_orders_einv_number），同一發票號碼無法重複寫入。發票檢核程式報告[2]逐日檢核是否有發票號碼被重複使用，如有重號即顯示 ALERT 及重複次數，通知管理者處理。佐證畫面如下（檢核報告[2]）：")
    ])
    add_evidence(t3_rows[4].xpath('./table:table-cell', namespaces=ns)[0], 'item2_duplicate', ns)

    # Item 3 Check & Explanation
    set_cell_paragraphs(t3_rows[5].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P49", "☑單一機構自行上傳"),
        ("P47", "☑非加值中心")
    ])
    set_cell_paragraphs(t3_rows[6].xpath('./table:table-cell', namespaces=ns)[0], [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：本公司為單一機構自行上傳（非加值中心）。狀態同步程式讀取 Turnkey 訊息紀錄（turnkey_message_log）之 G/C 狀態並回寫 ERP 訂單。發票檢核程式報告[3]比對「已開立發票數」與「大平台已確認筆數」，並列出傳送超過 60 分鐘仍未確認（DISPATCHED）或尚未傳送（PENDING）之發票，供管理者補傳。佐證畫面如下（檢核報告[3]）：")
    ])
    add_evidence(t3_rows[6].xpath('./table:table-cell', namespaces=ns)[0], 'item3_missing', ns)

    # Item 4 Check & Explanation
    set_cell_paragraphs(t3_rows[7].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過 (處理回應)"),
        ("P47", "☑通過 (比對筆數)"),
        ("P47", "☑非加值中心")
    ])
    set_cell_paragraphs(t3_rows[8].xpath('./table:table-cell', namespaces=ns)[0], [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：Turnkey 回覆狀態為 E（錯誤）時，狀態同步程式將該發票標記為 FAILED 並記錄處理代碼；發票檢核程式報告[4]列出所有 FAILED／CANCEL_FAILED 發票及其處理代碼，由管理者依錯誤訊息更正後重新開立並上傳。佐證畫面如下（檢核報告[4]）：")
    ])
    add_evidence(t3_rows[8].xpath('./table:table-cell', namespaces=ns)[0], 'item4_errors', ns)

    # Item 5 Check & Explanation
    set_cell_paragraphs(t3_rows[9].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "□通過　□不通過"),
        ("P49", "☑無提供會員載具")
    ])
    set_cell_paragraphs(t3_rows[10].xpath('./table:table-cell', namespaces=ns)[0], [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：本公司全數為 B2B 商業電子發票交換交易（對象均為具統一編號之營業人），未提供一般個人消費者會員載具服務，發票皆直接交付買受人統一編號或進行 B2B 交換，故無提供會員載具中獎通知需求（勾選無提供會員載具）。")
    ])

    # --- TABLES 5, 6, 7 (Checkbox check ☑) ---
    for tbl_name in ["表格5", "表格6", "表格7"]:
        tbl = tree.xpath(f'//table:table[@table:name="{tbl_name}"]', namespaces=ns)[0]
        for cell in tbl.xpath('.//table:table-cell[1]', namespaces=ns):
            p = cell.xpath('./text:p', namespaces=ns)
            if p and p[0].text and "□" in p[0].text:
                p[0].text = p[0].text.replace("□", "☑")

    # --- INVOICE VOLUME ---
    for p in tree.xpath('//text:p', namespaces=ns):
        txt = ''.join(p.itertext())
        if "每週最大發票數量為" in txt and "每月最大發票數量為" in txt:
            for child in list(p):
                p.remove(child)
            p.text = "每週最大發票數量為 100 筆；每月最大發票數量為 500 筆。"

    # --- TABLE 8: 四、上傳結果檢測 ---
    t8 = tree.xpath('//table:table[@table:name="表格8"]', namespaces=ns)[0]
    t8_rows = t8.xpath('.//table:table-row', namespaces=ns)

    # R1 Cell 0 Checkbox -> ☑
    chk1 = t8_rows[1].xpath('./table:table-cell[1]/text:p', namespaces=ns)[0]
    chk1.text = chk1.text.replace("□", "☑")

    # R2 Cell 0 Turnkey Explanation
    set_cell_paragraphs(t8_rows[2].xpath('./table:table-cell[1]', namespaces=ns)[0], [
        ("P27", "(佐證畫面與說明)"),
        ("P43", "說明：【Turnkey 處理結果確認】\n透過 Turnkey【檢視訊息紀錄】查詢，本次 B2B 交換各情境（A0101、A0102、A0201、A0202、A0301、A0302、B0101、B0102、B0201、B0202）及空白未使用字軌檔（E0402）之傳送狀態為「C」（資料上傳完畢，且已收到大平台回覆之存證處理成功訊息）。佐證畫面如下（狀態為 C）：")
    ])
    add_evidence(t8_rows[2].xpath('./table:table-cell[1]', namespaces=ns)[0], 'turnkey_status_c', ns)

    # R3 Cell 0 Checkbox -> ☑
    chk2 = t8_rows[3].xpath('./table:table-cell[1]/text:p', namespaces=ns)[0]
    chk2.text = chk2.text.replace("□", "☑")

    # R4 Cell 0 Web Platform Explanation + Image
    cell_t8_r4 = t8_rows[4].xpath('./table:table-cell[1]', namespaces=ns)[0]
    for child in list(cell_t8_r4):
        cell_t8_r4.remove(child)
    
    p_t8_r4_label = etree.SubElement(cell_t8_r4, f"{TEXT}p", attrib={f"{TEXT}style-name": "P27"})
    p_t8_r4_label.text = "(佐證畫面與說明)"
    
    p_t8_r4_text = etree.SubElement(cell_t8_r4, f"{TEXT}p", attrib={f"{TEXT}style-name": "P43"})
    p_t8_r4_text.text = "說明：【Web 大平台查詢確認】\n登入電子發票整合服務平台驗測環境（https://wwwtest.einvoice.nat.gov.tw），至【營業人功能選單 ➔ 查詢與下載 ➔ 發票查詢】，可查得本次測試開立之發票，內容與開立資料相符。佐證畫面如下（發票查詢畫面；Turnkey上線前自行檢測各情境結果亦均為「通過」）："

    add_evidence(cell_t8_r4, 'platform_invoice_query', ns)
    p_t8_img = etree.SubElement(cell_t8_r4, f"{TEXT}p", attrib={f"{TEXT}style-name": "Standard"})
    frame_b2b = etree.SubElement(p_t8_img, f"{DRAW}frame", attrib={
        f"{DRAW}name": "ImageB2B",
        f"{TEXT}anchor-type": "as-char",
        f"{SVG}width": "15.5cm",
        f"{SVG}height": "9.0cm",
        f"{DRAW}z-index": "0"
    })
    etree.SubElement(frame_b2b, f"{DRAW}image", attrib={
        f"{XLINK}href": "Pictures/proof_b2b.png",
        f"{XLINK}type": "simple",
        f"{XLINK}show": "embed",
        f"{XLINK}actuate": "onLoad"
    })

    # --- TABLE 9: 五、電子發票專用字軌檢測 ---
    t9 = tree.xpath('//table:table[@table:name="表格9"]', namespaces=ns)[0]
    t9_rows = t9.xpath('.//table:table-row', namespaces=ns)

    # R1 E0401 Checkbox -> □ (免測)
    set_first_p(t9_rows[1].xpath('./table:table-cell[1]', namespaces=ns)[0], "□\n(免測)")
    # R1 E0401 Test BAN
    set_cell_paragraphs(t9_rows[1].xpath('./table:table-cell[3]', namespaces=ns)[0], [
        ("P35", "總公司：免測"),
        ("P35", "分公司：免測"),
        ("P35", "（單一營業人無分支機構免測）")
    ])

    # R2 E0402 Checkbox -> ☑
    set_first_p(t9_rows[2].xpath('./table:table-cell[1]', namespaces=ns)[0], "☑")
    # R2 E0402 Test BAN
    set_cell_paragraphs(t9_rows[2].xpath('./table:table-cell[3]', namespaces=ns)[0], [
        ("P35", "公司統編："),
        ("P35", "00015555")
    ])

    # R2 E0402 Notes + Proof Image
    cell_t9_notes = t9_rows[2].xpath('./table:table-cell[4]', namespaces=ns)[0]
    
    p_t9_proof_lbl = etree.SubElement(cell_t9_notes, f"{TEXT}p", attrib={f"{TEXT}style-name": "P27"})
    p_t9_proof_lbl.text = "(佐證畫面與說明)"

    p_t9_proof_desc = etree.SubElement(cell_t9_notes, f"{TEXT}p", attrib={f"{TEXT}style-name": "P43"})
    p_t9_proof_desc.text = "說明：【E0402 空白未使用字軌檔檢測佐證】\n本公司（統一編號：00015555，繞送代碼：PA006753）已於 115 年 9 月 24 日透過 Turnkey 系統上傳期別 11510（LP 字軌）之空白未使用字軌檔（E0402），大平台回覆 ProcessResult 代碼 00000（全部發票處理成功）。於大平台驗測環境【E0402空白未使用發票字軌檔】線上查驗，公司統編 00015555 處理結果正式標示為「通過」。佐證畫面如下："

    p_t9_img = etree.SubElement(cell_t9_notes, f"{TEXT}p", attrib={f"{TEXT}style-name": "Standard"})
    frame_e0402 = etree.SubElement(p_t9_img, f"{DRAW}frame", attrib={
        f"{DRAW}name": "ImageE0402",
        f"{TEXT}anchor-type": "as-char",
        f"{SVG}width": "15.5cm",
        f"{SVG}height": "5.2cm",
        f"{DRAW}z-index": "0"
    })
    etree.SubElement(frame_e0402, f"{DRAW}image", attrib={
        f"{XLINK}href": "Pictures/proof_e0402.png",
        f"{XLINK}type": "simple",
        f"{XLINK}show": "embed",
        f"{XLINK}actuate": "onLoad"
    })

    # Register evidence images in the manifest
    ev_entries = "".join(
        f'  <manifest:file-entry manifest:full-path="{zn}" manifest:media-type="image/png"/>\n'
        for zn, _ in USED_EVIDENCE) + "</manifest:manifest>"
    manifest_xml = manifest_xml.replace("</manifest:manifest>", ev_entries)

    # Serialize back to XML
    out_content_bytes = etree.tostring(tree, encoding="utf-8", xml_declaration=True, standalone=True)

    # 3. Write out to ZIP
    print(f"Writing Version B ODT to: {OUT_ODT}")
    with zipfile.ZipFile(OUT_ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        if "mimetype" in other_files:
            zout.writestr("mimetype", other_files["mimetype"], compress_type=zipfile.ZIP_STORED)
        zout.writestr("META-INF/manifest.xml", manifest_xml.encode("utf-8"))
        zout.writestr("content.xml", out_content_bytes)
        for fname, fbytes in other_files.items():
            if fname not in ["mimetype", "META-INF/manifest.xml", "content.xml"]:
                zout.writestr(fname, fbytes)
        with open(IMG_B2B, "rb") as f:
            zout.writestr("Pictures/proof_b2b.png", f.read())
        with open(IMG_E0402, "rb") as f:
            zout.writestr("Pictures/proof_e0402.png", f.read())
        for zn, path in USED_EVIDENCE:
            with open(path, "rb") as f:
                zout.writestr(zn, f.read())

    print("Evidence embedded :", [n for n, _ in USED_EVIDENCE] or "none")
    print("Evidence MISSING  :", MISSING_EVIDENCE or "none")
    print("Version B ODT generated successfully via lxml!")
    print(f"File size: {os.path.getsize(OUT_ODT)} bytes")

if __name__ == "__main__":
    main()
