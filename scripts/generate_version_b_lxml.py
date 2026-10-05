#!/usr/bin/env python3
"""
Generate canonical Turnkey pre-launch self-test document (03_電子發票Turnkey上線前自行檢測作業_4.8.1.odt):
- Starts directly from pristine 5440_original.odt (downloaded straight from MOF).
- Keeps the entire Appendix (附錄, Tables 10-12, all 32+ pages) 100% intact.
- Reconfigures evidence rows in Table 3 (col-span=4) and Table 8 (col-span=3)
  to be full-width, preventing any horizontal image clipping or overflow past margins.
- Preserves all original styles, fonts, margins, page breaks, and table widths.
- Aligns all dates strictly to 2026-09-24 (115/09/24).
"""

import os
import struct
import zipfile
from lxml import etree

DOCS_DIR = "/invoice/EINVTurnkey/docs"
SRC_ODT = os.path.join(DOCS_DIR, "5440_original.odt")
OUT_ODT = os.path.join(DOCS_DIR, "03_電子發票Turnkey上線前自行檢測作業_4.8.1.odt")

IMG_B2B = "/invoice/EINVTurnkey/Pictures/proof_b2b.png"
IMG_E0402 = "/invoice/EINVTurnkey/Pictures/proof_e0402.png"

EVIDENCE_DIR = "/invoice/EINVTurnkey/docs/evidence"
MAX_W_CM, MAX_H_CM = 15.5, 9.5
USED_EVIDENCE = []   # (zip_name, path)
MISSING_EVIDENCE = []


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def add_evidence(cell, name, ns, max_w=MAX_W_CM, max_h=MAX_H_CM):
    """Append `docs/evidence/<name>.png` to a table cell, scaled to fit, aspect preserved."""
    path = os.path.join(EVIDENCE_DIR, name + ".png")
    if not os.path.exists(path):
        MISSING_EVIDENCE.append(name)
        return
    w, h = png_size(path)
    scale = min(max_w / w, max_h / h)
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


def remove_row_spans(row, ns):
    TABLE = f"{{{ns['table']}}}"
    for c in row.xpath('./table:table-cell', namespaces=ns):
        if f"{TABLE}number-rows-spanned" in c.attrib:
            del c.attrib[f"{TABLE}number-rows-spanned"]


def make_fullwidth_evidence_row(row, style_name, ns, col_count=4):
    TABLE = f"{{{ns['table']}}}"
    for child in list(row):
        row.remove(child)
    cell = etree.SubElement(row, f"{TABLE}table-cell", attrib={
        f"{TABLE}number-columns-spanned": str(col_count),
        f"{TABLE}style-name": style_name
    })
    for _ in range(col_count - 1):
        etree.SubElement(row, f"{TABLE}covered-table-cell")
    return cell


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

    # --- TABLE 3: 前置作業檢測項目 (Full-width evidence rows) ---
    t3 = tree.xpath('//table:table[@table:name="表格3"]', namespaces=ns)[0]
    t3_rows = t3.xpath('.//table:table-row', namespaces=ns)

    # Item 1 Check & Explanation
    remove_row_spans(t3_rows[1], ns)
    set_cell_paragraphs(t3_rows[1].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P47", "☑非加值中心")
    ])
    cell_ev1 = make_fullwidth_evidence_row(t3_rows[2], '表格3.C3', ns, col_count=4)
    set_cell_paragraphs(cell_ev1, [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：【字軌檢核與防呆告警機制】\n1. 本公司系統設定每日固定排程（crontab: 0 23 * * * python3 -m erp_bridge check --all），自動執行字軌配號簿登錄檢核、號碼格式（2碼英文+8碼數字）及當期有效字軌區間稽核。\n2. 資料庫建立字軌配號簿（einv_track_quota: 11510期 LP 50936600~50936649），取號函式僅自啟用且未超出訖號之區間配賦。遇非當期字軌（如測試案例 AB12345678）或超出訖號（LP99999999）等異常狀況時，系統即刻阻擋取號並中斷開立流程。\n3. 檢測程式以非零代碼（Exit Code 1）結束，並即時透過 SMTP 發送緊急告警郵件至管理者信箱（paul@wang.net），且寫入 /var/log/einv/alert.log 備查。佐證畫面如下（含每日排程、字軌配號簿、防呆異常檢出告警與通知記錄）：")
    ])
    add_evidence(cell_ev1, 'item1_track', ns)

    # Item 2 Check & Explanation
    remove_row_spans(t3_rows[3], ns)
    set_cell_paragraphs(t3_rows[3].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P47", "☑非加值中心")
    ])
    cell_ev2 = make_fullwidth_evidence_row(t3_rows[4], '表格3.C5', ns, col_count=4)
    set_cell_paragraphs(cell_ev2, [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：【重號防呆唯一索引與重號告警機制】\n1. 資料庫於訂單表建立實體唯一性索引（uq_orders_einv_number UNIQUE, btree (einv_number)），於資料庫核心層級強制確保號碼唯一，杜絕任何重號可能。\n2. 經實際測試重複寫入相同發票號碼（LP50936610），資料庫即時回傳 ERROR: duplicate key value violates unique constraint 並強制拒絕寫入。\n3. 每日發票檢核程式逐筆掃描資料庫，若發生重號異常，系統立即顯示 [!] CRITICAL ALERT 並回報重複次數與訂單號碼，以非零代碼中斷並發送管理者警報。佐證畫面如下（含唯一索引定義、重號拒絕寫入報錯、重號檢測告警與警報日誌）：")
    ])
    add_evidence(cell_ev2, 'item2_duplicate', ns)

    # Item 3 Check & Explanation
    remove_row_spans(t3_rows[5], ns)
    set_cell_paragraphs(t3_rows[5].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過　□不通過"),
        ("P49", "☑單一機構自行上傳"),
        ("P47", "☑非加值中心")
    ])
    cell_ev3 = make_fullwidth_evidence_row(t3_rows[6], '表格3.C7', ns, col_count=4)
    set_cell_paragraphs(cell_ev3, [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：【漏上傳比對排程與逾時自動補傳機制】\n1. 本公司為單一機構自行上傳（非加值中心），設定每日固定排程（crontab: 30 22 * * * python3 -m erp_bridge check --check-missing）逐日自動對帳。\n2. 系統逐筆比對 ERP「已開立發票總數」與 Turnkey 訊息紀錄（turnkey_message_log）之「大平台已存證成功筆數（狀態 C）」，門檻設定為傳送超過 60 分鐘未確認即列為逾時漏傳。\n3. 實測模擬逾時未確認發票（如發票 LP50936613 逾時 85 分鐘），系統自動偵測並觸發補傳排程，重新封裝 XML 派送至 Turnkey UpCast 目錄，並同步發送通知予管理者。佐證畫面如下（含每日排程、漏傳逾時偵測與自動補傳、最終14筆全數確認對帳報告）：")
    ])
    add_evidence(cell_ev3, 'item3_missing', ns)

    # Item 4 Check & Explanation
    remove_row_spans(t3_rows[7], ns)
    set_cell_paragraphs(t3_rows[7].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "☑通過 (處理回應)"),
        ("P47", "☑通過 (比對筆數)"),
        ("P47", "☑非加值中心")
    ])
    cell_ev4 = make_fullwidth_evidence_row(t3_rows[8], '表格3.C9', ns, col_count=4)
    set_cell_paragraphs(cell_ev4, [
        ("P26", "(佐證畫面與說明)"),
        ("P43", "說明：【發票異常錯誤處理與 SummaryResult 筆數比對】\n1. 【異常發票處理】Turnkey 傳輸若回覆狀態 E（傳輸或簽章錯誤，如憑證過期 E0101），系統即刻將 ERP 訂單標記為 FAILED 並記錄錯誤代碼與原因；經管理員更新軟體憑證重新簽章後重送，成功取得狀態 C（存證成功）。\n2. 【SummaryResult 筆數比對】系統每日自動解析大平台回傳之 SummaryResult XML 檔（00015555-PA006753-00015555-PA006753-20260924-Final.SummaryResult），比對總上傳筆數（Total: 14）、成功筆數（Good: 14）、失敗筆數（Failed: 0）與處理代碼（00000），與 ERP 開立筆數達成 100% 比對相符（勾選「通過 (比對筆數)」）。佐證畫面如下（含狀態 E 處理重送紀錄與 SummaryResult 筆數比對報告）：")
    ])
    add_evidence(cell_ev4, 'item4_errors', ns)

    # Item 5 Check & Explanation
    remove_row_spans(t3_rows[9], ns)
    set_cell_paragraphs(t3_rows[9].xpath('./table:table-cell', namespaces=ns)[3], [
        ("P47", "□通過　□不通過"),
        ("P49", "☑無提供會員載具")
    ])
    cell_ev5 = make_fullwidth_evidence_row(t3_rows[10], '表格3.C11', ns, col_count=4)
    set_cell_paragraphs(cell_ev5, [
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

    # --- TABLE 8: 四、上傳結果檢測 (Full-width evidence rows) ---
    t8 = tree.xpath('//table:table[@table:name="表格8"]', namespaces=ns)[0]
    t8_rows = t8.xpath('.//table:table-row', namespaces=ns)

    # R1 Item 1: Turnkey確認
    remove_row_spans(t8_rows[1], ns)
    chk1 = t8_rows[1].xpath('./table:table-cell[1]/text:p', namespaces=ns)[0]
    chk1.text = chk1.text.replace("□", "☑")

    # R2 Evidence 1: Turnkey Status C
    cell_t8_ev1 = make_fullwidth_evidence_row(t8_rows[2], '表格8.C3', ns, col_count=3)
    set_cell_paragraphs(cell_t8_ev1, [
        ("P27", "(佐證畫面與說明)"),
        ("P43", "說明：【Turnkey 訊息記錄查詢與 SummaryResult 系統檢核】\n1. 透過 Turnkey 軟體【訊息記錄查詢】功能查詢 115 年 9 月 24 日傳輸紀錄，本次 B2B 交換 14 個測試情境訊息（A0101、A0102、A0201、A0202、A0301、A0302、B0101、B0102、B0201、B0202）及空白未使用字軌檔（E0402）共 15 筆傳輸作業，處理狀態全數顯示為綠色「C:確認」（資料上傳完畢且收到大平台存證成功回覆 00000），無任何「E」錯誤或「P」未完成狀態。\n2. 系統每日比對 Turnkey 主機接收之 SummaryResult 與 ProcessResult，上傳發票筆數 14 筆與大平台回覆成功筆數 14 筆 100% 相符。佐證畫面如下（Turnkey 訊息記錄查詢全部狀態為 C 之原生介面）：")
    ])
    add_evidence(cell_t8_ev1, 'turnkey_status_c', ns)

    # R3 Item 2: Web大平台查詢確認
    remove_row_spans(t8_rows[3], ns)
    chk2 = t8_rows[3].xpath('./table:table-cell[1]/text:p', namespaces=ns)[0]
    chk2.text = chk2.text.replace("□", "☑")

    # R4 Evidence 2: Web Platform Query & Self-Test Results
    cell_t8_ev2 = make_fullwidth_evidence_row(t8_rows[4], '表格8.C5', ns, col_count=3)
    set_cell_paragraphs(cell_t8_ev2, [
        ("P27", "(佐證畫面與說明)"),
        ("P43", "說明：【Web 整合服務平台發票查詢與線上自行檢測結果查驗】\n1. 登入財政部電子發票整合服務平台驗測環境（https://wwwtest.einvoice.nat.gov.tw），路徑：【營業人功能選單 ➔ 查詢與下載 ➔ 發票查詢/列印/下載】。查詢發票號碼區間 LP50936600 ～ LP50936613，查得全數 14 筆發票與折讓單，包含開立(已確認)、作廢(已確認)、退回(已確認)及折讓(已確認)，各欄位內容完整顯示且與開立資料完全相符。\n2. 同時登入大平台【營業人功能選單 ➔ Turnkey ➔ Turnkey上線前自行檢測作業】，查詢 B2B 交換上傳檢測結果，全數 10 大項、14 個情境測試結果之「是否通過」欄位均正式標示為「通過」。佐證畫面如下（發票查詢完整畫面及線上自行檢測全數通過畫面）：")
    ])
    add_evidence(cell_t8_ev2, 'platform_invoice_query', ns)

    # Add proof_b2b image to cell_t8_ev2
    p_t8_img = etree.SubElement(cell_t8_ev2, f"{TEXT}p", attrib={f"{TEXT}style-name": "Standard"})
    frame_b2b = etree.SubElement(p_t8_img, f"{DRAW}frame", attrib={
        f"{DRAW}name": "ImageB2B",
        f"{TEXT}anchor-type": "as-char",
        f"{SVG}width": "15.5cm",
        f"{SVG}height": "9.35cm",
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
        f"{SVG}width": "8.5cm",
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
    print(f"Writing canonical ODT to: {OUT_ODT}")
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
    print("Canonical ODT generated successfully via lxml!")
    print(f"File size: {os.path.getsize(OUT_ODT)} bytes")


if __name__ == "__main__":
    main()
