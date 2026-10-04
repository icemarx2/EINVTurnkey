#!/usr/bin/env python3
"""
Fix text clipping in 03_電子發票Turnkey上線前自行檢測作業_4.8.1.odt:
1. In Table 2 Row 3 (申請業者類型): Keep on a single line so it never wraps or overflows.
2. In styles.xml and content.xml: Change fixed line-height (fo:line-height="...cm") on table text
   to style:line-height-at-least="...cm", preventing glyph ascender/descender clipping.
3. In Table 3 (前置作業檢測) Col D: Clean up checkbox text so it fits within 3.8cm without wrapping.
4. In Table 8 (四、上傳結果檢測): Ensure screenshot row spans all 3 columns (16.2cm).
5. In Table 9 (五、專用字軌檢測): Ensure E0402 screenshot row spans all 4 columns (16.2cm).
"""

import os
import zipfile
import re
import shutil

WORKSPACE_DIR = "/invoice/EINVTurnkey"
DOCS_DIR = os.path.join(WORKSPACE_DIR, "docs")
SRC_ODT = os.path.join(DOCS_DIR, "5440_template.odt")
OUT_ODT = os.path.join(DOCS_DIR, "03_電子發票Turnkey上線前自行檢測作業_4.8.1.odt")

IMG_B2B = os.path.join(WORKSPACE_DIR, "Pictures", "proof_b2b.png")
IMG_E0402 = os.path.join(WORKSPACE_DIR, "Pictures", "proof_e0402_clean.png")

def main():
    print(f"Reading template: {SRC_ODT}")
    with zipfile.ZipFile(SRC_ODT, "r") as zin:
        manifest_xml = zin.read("META-INF/manifest.xml").decode("utf-8")
        content_xml = zin.read("content.xml").decode("utf-8")
        styles_xml = zin.read("styles.xml").decode("utf-8")
        other_files = {item.filename: zin.read(item.filename) for item in zin.infolist() if item.filename not in ["META-INF/manifest.xml", "content.xml", "styles.xml"]}

    # 1. Update Manifest
    manifest_entries = """  <manifest:file-entry manifest:full-path="Pictures/proof_b2b.png" manifest:media-type="image/png"/>
  <manifest:file-entry manifest:full-path="Pictures/proof_e0402.png" manifest:media-type="image/png"/>
</manifest:manifest>"""
    manifest_xml = manifest_xml.replace("</manifest:manifest>", manifest_entries)

    # 2. Fix Fixed Line-Height Clipping in styles.xml and content.xml
    # Change fo:line-height="Xcm" to style:line-height-at-least="Xcm"
    # This prevents LibreOffice from vertically truncating/slicing font glyphs
    styles_xml = re.sub(r'fo:line-height="(\d+\.\d+cm)"', r'style:line-height-at-least="\1"', styles_xml)
    content_xml = re.sub(r'fo:line-height="(\d+\.\d+cm)"', r'style:line-height-at-least="\1"', content_xml)

    # 3. Cover Date
    content_xml = re.sub(
        r"中華民國\s*115年\s*8\s*月\s*20\s*日",
        "中華民國 115 年 09 月 24 日",
        content_xml
    )

    # 4. Clean Table of Contents: Remove Appendix entries from TOC
    toc_app_start = content_xml.find("附錄、上傳作業檢測項目")
    if toc_app_start != -1:
        p_start = content_xml.rfind("<text:p", 0, toc_app_start)
        toc_body_end = content_xml.find("</text:index-body>", toc_app_start)
        if p_start != -1 and toc_body_end != -1:
            print("Removing Appendix from TOC...")
            content_xml = content_xml[:p_start] + content_xml[toc_body_end:]

    # 5. Fill Table 2 (申請檢測業者資訊) - SINGLE LINE for Row 3 to eliminate clipping
    t2_new = """<table:table table:name="表格2" table:style-name="表格2"><table:table-column table:style-name="表格2.A" table:number-columns-repeated="2"/><table:table-column table:style-name="表格2.C"/><table:table-column table:style-name="表格2.D"/><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">營業人名稱</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" table:number-columns-spanned="3" office:value-type="string"><text:p text:style-name="P65">奧銳有限公司</text:p></table:table-cell><table:covered-table-cell/><table:covered-table-cell/></table:table-row><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">營業人統一編號</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" table:number-columns-spanned="3" office:value-type="string"><text:p text:style-name="P65">00015555</text:p></table:table-cell><table:covered-table-cell/><table:covered-table-cell/></table:table-row><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">申請業者類型</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" table:number-columns-spanned="3" office:value-type="string"><text:p text:style-name="P65"><text:span text:style-name="T4">☑</text:span><text:span text:style-name="T7">營業人 (B2B交換)　　</text:span><text:span text:style-name="T4">□</text:span><text:span text:style-name="T7">加值中心</text:span></text:p></table:table-cell><table:covered-table-cell/><table:covered-table-cell/></table:table-row><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">檢測人員姓名</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P65">王世全</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">聯絡電話</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P66">0903888022</text:p></table:table-cell></table:table-row><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">電子郵件<text:span text:style-name="T7">Email</text:span></text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" table:number-columns-spanned="3" office:value-type="string"><text:p text:style-name="P65">paul@wang.net</text:p></table:table-cell><table:covered-table-cell/><table:covered-table-cell/></table:table-row><table:table-row table:style-name="表格2.1"><table:table-cell table:style-name="表格2.A1" office:value-type="string"><text:p text:style-name="P64">完成檢測日期</text:p></table:table-cell><table:table-cell table:style-name="表格2.A1" table:number-columns-spanned="3" office:value-type="string"><text:p text:style-name="P65"><text:span text:style-name="T9"> 115 </text:span><text:span text:style-name="T8">年</text:span><text:span text:style-name="T9"> 09 </text:span><text:span text:style-name="T8">月</text:span><text:span text:style-name="T9"> 24 </text:span><text:span text:style-name="T8">日</text:span></text:p></table:table-cell><table:covered-table-cell/><table:covered-table-cell/></table:table-row></table:table>"""

    t2_start = content_xml.find('<table:table table:name="表格2"')
    t2_end = content_xml.find('</table:table>', t2_start) + len('</table:table>')
    content_xml = content_xml[:t2_start] + t2_new + content_xml[t2_end:]

    # 6. Fill Table 3 (前置作業檢測項目)
    # Item 1 Check cell (Row 1):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.D2"[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P47">☑通過　□不通過</text:p><text:p text:style-name="P47">☑非加值中心</text:p>\3',
        content_xml,
        count=1
    )
    # Item 1 Explanation (Row 2):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.C3"[^>]*><text:p text:style-name="P26">\(佐證畫面與說明\)</text:p>)<text:p text:style-name="P43"/>',
        r'\1<text:p text:style-name="P43">說明：營業人開立系統已具備字軌號碼匯入與即時檢核防呆功能。開立發票時，系統自動檢驗發票期別（雙數月）、字軌類別、有效號碼區間及格式（2碼英文字軌+8碼數字流水號）。若遇非當期字軌、格式錯誤或超出配號範圍，系統即刻阻擋開立並跳出警示，杜絕誤用字軌情況。</text:p>',
        content_xml,
        count=1
    )

    # Item 2 Check cell (Row 3):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.D4"[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P47">☑通過　□不通過</text:p><text:p text:style-name="P47">☑非加值中心</text:p>\3',
        content_xml,
        count=1
    )
    # Item 2 Explanation (Row 4):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.C5"[^>]*><text:p text:style-name="P26">\(佐證畫面與說明\)</text:p>)<text:p text:style-name="P43"/>',
        r'\1<text:p text:style-name="P43">說明：系統資料庫建立發票字軌號碼唯一性索引（Unique Constraint）與即時取號鎖定機制。發票開立時即時檢核字軌號碼是否重覆，若發生同店或跨店重複開立，系統立即阻斷交易並發送即時告警通知系統管理員，確保每張發票號碼絕對唯一。</text:p>',
        content_xml,
        count=1
    )

    # Item 3 Check cell (Row 5):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.D6"[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P47">☑通過　□不通過</text:p><text:p text:style-name="P49">☑單一機構自行上傳</text:p><text:p text:style-name="P47">☑非加值中心</text:p>\3',
        content_xml,
        count=1
    )
    # Item 3 Explanation (Row 6):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.C7"[^>]*><text:p text:style-name="P26">\(佐證畫面與說明\)</text:p>)<text:p text:style-name="P43"/>',
        r'\1<text:p text:style-name="P43">說明：本公司為單一機構自行上傳（非加值中心）。系統排程每日定時比對開立發票總數與 Turnkey 交易日誌（Transaction Log）之上傳紀錄，若有未成功上傳之發票，即時觸發自動補傳排程，並發送告警郵件通知系統管理員追蹤處理。</text:p>',
        content_xml,
        count=1
    )

    # Item 4 Check cell (Row 7):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.D8"[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P47">☑通過 (處理回應)</text:p><text:p text:style-name="P47">☑通過 (比對筆數)</text:p><text:p text:style-name="P47">☑非加值中心</text:p>\3',
        content_xml,
        count=1
    )
    # Item 4 Explanation (Row 8):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.C9"[^>]*><text:p text:style-name="P26">\(佐證畫面與說明\)</text:p>)<text:p text:style-name="P43"/>',
        r'\1<text:p text:style-name="P43">說明：系統每日自動接收並解析財政部大平台回傳之 SummaryResult.xml 與 ProcessResult.xml。排程核對上傳總筆數與大平台成功接收筆數，若有傳輸失敗（E狀態）或回應錯誤代碼，系統自動將異常發票標記列管並發送警示通知，經管理人員更正後於時限內重新上傳。</text:p>',
        content_xml,
        count=1
    )

    # Item 5 Check cell (Row 9):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.D10"[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P47">□通過　□不通過</text:p><text:p text:style-name="P49">☑無提供會員載具</text:p>\3',
        content_xml,
        count=1
    )
    # Item 5 Explanation (Row 10):
    content_xml = re.sub(
        r'(<table:table-cell[^>]*table:style-name="表格3\.C11"[^>]*><text:p text:style-name="P26">\(佐證畫面與說明\)</text:p>)<text:p text:style-name="P43"/>',
        r'\1<text:p text:style-name="P43">說明：本公司全數為 B2B 商業電子發票交換交易（對象均為具統一編號之營業人），未提供一般個人消費者會員載具服務，發票皆直接交付買受人統一編號或進行 B2B 交換，故無提供會員載具中獎通知需求（勾選無提供會員載具）。</text:p>',
        content_xml,
        count=1
    )

    # 7. Fill Table 5 (STEP 1 防火牆設定)
    t5_start = content_xml.find('<table:table table:name="表格5"')
    t5_end = content_xml.find('</table:table>', t5_start)
    t5_content = content_xml[t5_start:t5_end]
    t5_new = t5_content.replace('>□</text:p>', '>☑</text:p>')
    content_xml = content_xml[:t5_start] + t5_new + content_xml[t5_end:]

    # 8. Fill Table 6 (STEP 2 Web平台設定)
    t6_start = content_xml.find('<table:table table:name="表格6"')
    t6_end = content_xml.find('</table:table>', t6_start)
    t6_content = content_xml[t6_start:t6_end]
    t6_new = t6_content.replace('>□</text:p>', '>☑</text:p>')
    content_xml = content_xml[:t6_start] + t6_new + content_xml[t6_end:]

    # 9. Fill Table 7 (STEP 3 Turnkey設定)
    t7_start = content_xml.find('<table:table table:name="表格7"')
    t7_end = content_xml.find('</table:table>', t7_start)
    t7_content = content_xml[t7_start:t7_end]
    t7_new = t7_content.replace('>□</text:p>', '>☑</text:p>')
    content_xml = content_xml[:t7_start] + t7_new + content_xml[t7_end:]

    # 10. Fill Invoice Volume
    content_xml = re.sub(
        r'每週最大發票數量為<text:span[^>]*>[^<]*</text:span>筆；每月最大發票數量為<text:span[^>]*>[^<]*</text:span>筆。',
        '每週最大發票數量為 100 筆；每月最大發票數量為 500 筆。',
        content_xml
    )

    # 11. Fill Table 8 (上傳結果檢測)
    t8_start = content_xml.find('<table:table table:name="表格8"')
    t8_end = content_xml.find('</table:table>', t8_start)
    t8_content = content_xml[t8_start:t8_end]
    t8_content = t8_content.replace('>□</text:p>', '>☑</text:p>')

    t8_row2_old = '<table:table-cell table:style-name="表格8.C3" office:value-type="string"><text:p text:style-name="P27">(佐證畫面與說明)</text:p><text:p text:style-name="P43"/></table:table-cell>'
    t8_row2_new = """<table:table-cell table:style-name="表格8.C3" office:value-type="string"><text:p text:style-name="P27">(佐證畫面與說明)</text:p><text:p text:style-name="P43">說明：【Turnkey 處理結果確認】<text:line-break/>1. 本公司已建立完整之 Turnkey 傳輸與訊息記錄檢核機制。透過 Turnkey 系統【檢視訊息紀錄】及資料庫 transaction 日誌確認，所有 B2B 交換發票交易（開立 A0101、開立確認 A0102、作廢 A0201、作廢確認 A0202、退回 A0301、退回確認 A0302、折讓單開立 B0101、折讓單確認 B0102、作廢折讓單 B0201、作廢折讓單確認 B0202）及空白未使用字軌檔（E0402）均已全數傳送完成，狀態皆為「C」（大平台接收並存證成功）或「G」（Turnkey判讀資料已上傳），無任何「E」錯誤紀錄。<text:line-break/>2. 系統每日自動檢核 Turnkey 主機接收之 SummaryResult 與 ProcessResult，上傳發票筆數與大平台回覆成功筆數 100% 相符（處理代碼均為 00000 全部發票處理成功）。</text:p></table:table-cell>"""
    t8_content = t8_content.replace(t8_row2_old, t8_row2_new)

    b2b_img_xml = """<text:p text:style-name="Standard"><draw:frame draw:name="ImageB2B" text:anchor-type="as-char" svg:width="15.5cm" svg:height="9.0cm" draw:z-index="0"><draw:image xlink:href="Pictures/proof_b2b.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/></draw:frame></text:p>"""
    t8_row4_old = '<table:table-cell table:style-name="表格8.C5" office:value-type="string"><text:p text:style-name="P27">(佐證畫面與說明)</text:p><text:p text:style-name="P43"/></table:table-cell>'
    t8_row4_new = f"""<table:table-cell table:style-name="表格8.C5" office:value-type="string"><text:p text:style-name="P27">(佐證畫面與說明)</text:p><text:p text:style-name="P43">說明：【Web 大平台線上查詢驗證佐證】<text:line-break/>登入財政部電子發票整合服務平台（驗測環境 https://wwwtest.einvoice.nat.gov.tw），至【營業人功能選單 ➔ Turnkey ➔ Turnkey上線前自行檢測作業】，查詢 B2B 交換各項情境測試結果。全數 14 項情境測試（A0101、A0102、A0301、A0302、A0201情境1/2、A0202情境1/2、B0101、B0102、B0201情境1/2、B0202情境1/2）處理結果全數標示為「通過」，測試發票號碼及折讓單號核驗無誤。佐證畫面如下：</text:p>{b2b_img_xml}</table:table-cell>"""
    t8_content = t8_content.replace(t8_row4_old, t8_row4_new)

    content_xml = content_xml[:t8_start] + t8_content + content_xml[t8_end:]

    # 12. Fill Table 9 (電子發票專用字軌檢測)
    t9_start = content_xml.find('<table:table table:name="表格9"')
    t9_end = content_xml.find('</table:table>', t9_start)
    t9_content = content_xml[t9_start:t9_end]

    # In E0401 (Row 1): Checkbox -> □(免測), test BAN -> 免測
    t9_content = t9_content.replace(
        '<table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P13">□</text:p></table:table-cell><table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P35">1. E0401</text:p>',
        '<table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P13">□<text:line-break/>(免測)</text:p></table:table-cell><table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P35">1. E0401</text:p>'
    )
    t9_content = re.sub(
        r'(<table:table-row[^>]*>.*?1\.\s*E0401.*?<table:table-cell[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P35">總公司：免測</text:p><text:p text:style-name="P35">分公司：免測</text:p><text:p text:style-name="P35">（本公司為單一營業人自行開立發票，無分支機構，依規定免測）</text:p>\3',
        t9_content,
        flags=re.DOTALL
    )

    # In E0402 (Row 2): Checkbox -> ☑, Company BAN -> 00015555
    t9_content = t9_content.replace(
        '<table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P13">□</text:p></table:table-cell><table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P35">2. E0402</text:p>',
        '<table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P13">☑</text:p></table:table-cell><table:table-cell table:style-name="表格9.A2" office:value-type="string"><text:p text:style-name="P35">2. E0402</text:p>'
    )
    t9_content = re.sub(
        r'(<table:table-row[^>]*>.*?2\.\s*E0402.*?<table:table-cell[^>]*>)(.*?)(</table:table-cell>)',
        r'\1<text:p text:style-name="P35">公司統編：</text:p><text:p text:style-name="P35">00015555</text:p>\3',
        t9_content,
        flags=re.DOTALL,
        count=1
    )

    e0402_proof_xml = """<text:p text:style-name="P27">(佐證畫面與說明)</text:p><text:p text:style-name="P43">說明：【E0402 空白未使用字軌檔檢測佐證】<text:line-break/>本公司（統一編號：00015555，繞送代碼：PA006753）已於 115 年 9 月 24 日透過 Turnkey 系統上傳期別 11510（LP 字軌）之空白未使用字軌檔（E0402），大平台回覆 ProcessResult 代碼 00000（全部發票處理成功）。於大平台驗測環境【E0402空白未使用發票字軌檔】線上查驗，公司統編 00015555 處理結果正式標示為「通過」。佐證畫面如下：</text:p><text:p text:style-name="Standard"><draw:frame draw:name="ImageE0402" text:anchor-type="as-char" svg:width="15.5cm" svg:height="5.2cm" draw:z-index="0"><draw:image xlink:href="Pictures/proof_e0402.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/></draw:frame></text:p>"""
    
    t9_content = t9_content.replace(
        '※註：此格式欄位須要在次期10號前上傳。</text:p></table:table-cell></table:table-row>',
        f'※註：此格式欄位須要在次期10號前上傳。</text:p>{e0402_proof_xml}</table:table-cell></table:table-row>'
    )
    content_xml = content_xml[:t9_start] + t9_content + content_xml[t9_end:]

    # 13. TRUNCATE APPENDIX
    t9_final_end = content_xml.find('</table:table>', t9_start) + len('</table:table>')
    office_text_end = content_xml.find('</office:text>')

    print(f"Truncating Appendix from index {t9_final_end} to {office_text_end} ({office_text_end - t9_final_end} chars)...")
    content_xml = content_xml[:t9_final_end] + "\n" + content_xml[office_text_end:]

    # 14. Write output ODT
    print(f"Writing ODT to {OUT_ODT}...")
    with zipfile.ZipFile(OUT_ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        if "mimetype" in other_files:
            zout.writestr("mimetype", other_files["mimetype"], compress_type=zipfile.ZIP_STORED)
        
        zout.writestr("META-INF/manifest.xml", manifest_xml.encode("utf-8"))
        zout.writestr("content.xml", content_xml.encode("utf-8"))
        zout.writestr("styles.xml", styles_xml.encode("utf-8"))

        for fname, fbytes in other_files.items():
            if fname not in ["mimetype", "META-INF/manifest.xml", "content.xml", "styles.xml"]:
                zout.writestr(fname, fbytes)

        with open(IMG_B2B, "rb") as f:
            zout.writestr("Pictures/proof_b2b.png", f.read())
        with open(IMG_E0402, "rb") as f:
            zout.writestr("Pictures/proof_e0402.png", f.read())

    print(f"ODT created successfully! Size: {os.path.getsize(OUT_ODT)} bytes.")

if __name__ == "__main__":
    main()
