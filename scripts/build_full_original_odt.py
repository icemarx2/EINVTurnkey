#!/usr/bin/env python3
"""
Generate Version B of the Turnkey pre-launch self-test document:
- Starts directly from pristine 5440_original.odt (downloaded straight from MOF).
- Keeps the entire Appendix (附錄, Tables 10-12, all 32+ pages) 100% intact.
- Fills in all applicant details, test checkboxes, technical descriptions,
  and proof screenshots into Chapters 1 to 3 answer fields.
- Preserves all original styles, fonts, margins, and table widths.
"""

import os
import zipfile
import re

DOCS_DIR = "/invoice/EINVTurnkey/docs"
SRC_ODT = os.path.join(DOCS_DIR, "5440_original.odt")
OUT_ODT = os.path.join(DOCS_DIR, "03_電子發票Turnkey上線前自行檢測作業_4.8.1_Full_vB.odt")

IMG_B2B = "/invoice/EINVTurnkey/Pictures/proof_b2b.png"
IMG_E0402 = "/invoice/EINVTurnkey/Pictures/proof_e0402.png"

def main():
    print(f"Reading pristine original template: {SRC_ODT}")
    with zipfile.ZipFile(SRC_ODT, "r") as zin:
        manifest_xml = zin.read("META-INF/manifest.xml").decode("utf-8")
        content_xml = zin.read("content.xml").decode("utf-8")
        styles_xml = zin.read("styles.xml").decode("utf-8")
        other_files = {item.filename: zin.read(item.filename) for item in zin.infolist() if item.filename not in ["META-INF/manifest.xml", "content.xml", "styles.xml"]}

    # 1. Update manifest for embedded images
    manifest_entries = """  <manifest:file-entry manifest:full-path="Pictures/proof_b2b.png" manifest:media-type="image/png"/>
  <manifest:file-entry manifest:full-path="Pictures/proof_e0402.png" manifest:media-type="image/png"/>
</manifest:manifest>"""
    manifest_xml = manifest_xml.replace("</manifest:manifest>", manifest_entries)

    # 2. Cover Date
    content_xml = re.sub(
        r"中華民國\s*115年\s*8\s*月\s*20\s*日",
        "中華民國 115 年 09 月 24 日",
        content_xml
    )

    # 3. Table 2 (貳、申請檢測業者資訊)
    # Row 0: 營業人名稱
    content_xml = content_xml.replace(
        '<ns2:p ns2:style-name="P64">營業人名稱</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65" />',
        '<ns2:p ns2:style-name="P64">營業人名稱</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65">奧銳有限公司</ns2:p>'
    )
    # Row 1: 營業人統一編號
    content_xml = content_xml.replace(
        '<ns2:p ns2:style-name="P64">營業人統一編號</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65" />',
        '<ns2:p ns2:style-name="P64">營業人統一編號</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65">00015555</ns2:p>'
    )
    # Row 2: 申請業者類型
    t2_type_old = '<ns2:p ns2:style-name="P65"><ns2:span ns2:style-name="T4">□</ns2:span><ns2:span ns2:style-name="T7">營業人</ns2:span><ns2:span ns2:style-name="T9">　　</ns2:span><ns2:span ns2:style-name="T5"> <ns2:s ns2:c="4" /></ns2:span><ns2:span ns2:style-name="T9">　　</ns2:span><ns2:span ns2:style-name="T4">□</ns2:span><ns2:span ns2:style-name="T7">加值中心</ns2:span></ns2:p>'
    t2_type_new = '<ns2:p ns2:style-name="P65"><ns2:span ns2:style-name="T4">☑</ns2:span><ns2:span ns2:style-name="T7">營業人 (B2B交換)　　</ns2:span><ns2:span ns2:style-name="T4">□</ns2:span><ns2:span ns2:style-name="T7">加值中心</ns2:span></ns2:p>'
    content_xml = content_xml.replace(t2_type_old, t2_type_new)

    # Row 3: 檢測人員姓名 & 聯絡電話
    content_xml = content_xml.replace(
        '<ns2:p ns2:style-name="P64">檢測人員姓名</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns1:value-type="string"><ns2:p ns2:style-name="P65" />',
        '<ns2:p ns2:style-name="P64">檢測人員姓名</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns1:value-type="string"><ns2:p ns2:style-name="P65">王世全</ns2:p>'
    )
    content_xml = content_xml.replace(
        '<ns2:p ns2:style-name="P64">聯絡電話</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns1:value-type="string"><ns2:p ns2:style-name="P66" />',
        '<ns2:p ns2:style-name="P64">聯絡電話</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns1:value-type="string"><ns2:p ns2:style-name="P66">0903888022</ns2:p>'
    )
    # Row 4: 電子郵件Email
    content_xml = content_xml.replace(
        '<ns2:p ns2:style-name="P64">電子郵件<ns2:span ns2:style-name="T7">Email</ns2:span></ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65" />',
        '<ns2:p ns2:style-name="P64">電子郵件<ns2:span ns2:style-name="T7">Email</ns2:span></ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格2.A1" ns0:number-columns-spanned="3" ns1:value-type="string"><ns2:p ns2:style-name="P65">paul@wang.net</ns2:p>'
    )
    # Row 5: 完成檢測日期
    t2_date_old = '<ns2:span ns2:style-name="T9">　　　　</ns2:span><ns2:span ns2:style-name="T8">年</ns2:span><ns2:span ns2:style-name="T9">　　　　</ns2:span><ns2:span ns2:style-name="T8">月</ns2:span><ns2:span ns2:style-name="T9">　　　　</ns2:span><ns2:span ns2:style-name="T8">日</ns2:span>'
    t2_date_new = '<ns2:span ns2:style-name="T9"> 115 </ns2:span><ns2:span ns2:style-name="T8">年</ns2:span><ns2:span ns2:style-name="T9"> 09 </ns2:span><ns2:span ns2:style-name="T8">月</ns2:span><ns2:span ns2:style-name="T9"> 24 </ns2:span><ns2:span ns2:style-name="T8">日</ns2:span>'
    content_xml = content_xml.replace(t2_date_old, t2_date_new)

    # 4. Table 3 (前置作業檢測項目)
    # Item 1 Check
    t3_r1_chk_old = '<ns0:table-cell ns0:style-name="表格3.D2" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P42" /><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□非加值中心</ns2:p></ns0:table-cell>'
    t3_r1_chk_new = '<ns0:table-cell ns0:style-name="表格3.D2" ns1:value-type="string"><ns2:p ns2:style-name="P47">☑通過　□不通過</ns2:p><ns2:p ns2:style-name="P47">☑非加值中心</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r1_chk_old, t3_r1_chk_new)

    # Item 1 Explanation
    t3_r2_exp_old = '<ns0:table-cell ns0:style-name="表格3.C3" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t3_r2_exp_new = '<ns0:table-cell ns0:style-name="表格3.C3" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：營業人開立系統已具備字軌號碼匯入與即時檢核防呆功能。開立發票時，系統自動檢驗發票期別（雙數月）、字軌類別、有效號碼區間及格式（2碼英文字軌+8碼數字流水號）。若遇非當期字軌、格式錯誤或超出配號範圍，系統即刻阻擋開立並跳出警示，杜絕誤用字軌情況。</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r2_exp_old, t3_r2_exp_new)

    # Item 2 Check
    t3_r3_chk_old = '<ns0:table-cell ns0:style-name="表格3.D4" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P42" /><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□非加值中心</ns2:p></ns0:table-cell>'
    t3_r3_chk_new = '<ns0:table-cell ns0:style-name="表格3.D4" ns1:value-type="string"><ns2:p ns2:style-name="P47">☑通過　□不通過</ns2:p><ns2:p ns2:style-name="P47">☑非加值中心</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r3_chk_old, t3_r3_chk_new)

    # Item 2 Explanation
    t3_r4_exp_old = '<ns0:table-cell ns0:style-name="表格3.C5" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t3_r4_exp_new = '<ns0:table-cell ns0:style-name="表格3.C5" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：系統資料庫建立發票字軌號碼唯一性索引（Unique Constraint）與即時取號鎖定機制。發票開立時即時檢核字軌號碼是否重覆，若發生同店或跨店重複開立，系統立即阻斷交易並發送即時告警通知系統管理員，確保每張發票號碼絕對唯一。</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r4_exp_old, t3_r4_exp_new)

    # Item 3 Check
    t3_r5_chk_old = '<ns0:table-cell ns0:style-name="表格3.D6" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P49">□單一機構或分支機構自行上傳</ns2:p><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□非加值中心</ns2:p><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□非加值中心</ns2:p></ns0:table-cell>'
    t3_r5_chk_new = '<ns0:table-cell ns0:style-name="表格3.D6" ns1:value-type="string"><ns2:p ns2:style-name="P47">☑通過　□不通過</ns2:p><ns2:p ns2:style-name="P49">☑單一機構自行上傳</ns2:p><ns2:p ns2:style-name="P47">☑非加值中心</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r5_chk_old, t3_r5_chk_new)

    # Item 3 Explanation
    t3_r6_exp_old = '<ns0:table-cell ns0:style-name="表格3.C7" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t3_r6_exp_new = '<ns0:table-cell ns0:style-name="表格3.C7" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：本公司為單一機構自行上傳（非加值中心）。系統排程每日定時比對開立發票總數與 Turnkey 交易日誌（Transaction Log）之上傳紀錄，若有未成功上傳之發票，即時觸發自動補傳排程，並發送告警郵件通知系統管理員追蹤處理。</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r6_exp_old, t3_r6_exp_new)

    # Item 4 Check
    t3_r7_chk_old = '<ns0:table-cell ns0:style-name="表格3.D8" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47" /><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P47">□非加值中心</ns2:p></ns0:table-cell>'
    t3_r7_chk_new = '<ns0:table-cell ns0:style-name="表格3.D8" ns1:value-type="string"><ns2:p ns2:style-name="P47">☑通過 (處理回應)</ns2:p><ns2:p ns2:style-name="P47">☑通過 (比對筆數)</ns2:p><ns2:p ns2:style-name="P47">☑非加值中心</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r7_chk_old, t3_r7_chk_new)

    # Item 4 Explanation
    t3_r8_exp_old = '<ns0:table-cell ns0:style-name="表格3.C9" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t3_r8_exp_new = '<ns0:table-cell ns0:style-name="表格3.C9" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：系統每日自動接收並解析財政部大平台回傳之 SummaryResult.xml 與 ProcessResult.xml。排程核對上傳總筆數與大平台成功接收筆數，若有傳輸失敗（E狀態）或回應錯誤代碼，系統自動將異常發票標記列管並發送警示通知，經管理人員更正後於時限內重新上傳。</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r8_exp_old, t3_r8_exp_new)

    # Item 5 Check
    t3_r9_chk_old = '<ns0:table-cell ns0:style-name="表格3.D10" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過□不通過</ns2:p><ns2:p ns2:style-name="P49">□無提供會員載具</ns2:p></ns0:table-cell>'
    t3_r9_chk_new = '<ns0:table-cell ns0:style-name="表格3.D10" ns1:value-type="string"><ns2:p ns2:style-name="P47">□通過　□不通過</ns2:p><ns2:p ns2:style-name="P49">☑無提供會員載具</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r9_chk_old, t3_r9_chk_new)

    # Item 5 Explanation
    t3_r10_exp_old = '<ns0:table-cell ns0:style-name="表格3.C11" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t3_r10_exp_new = '<ns0:table-cell ns0:style-name="表格3.C11" ns0:number-columns-spanned="2" ns1:value-type="string"><ns2:p ns2:style-name="P26">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：本公司全數為 B2B 商業電子發票交換交易（對象均為具統一編號之營業人），未提供一般個人消費者會員載具服務，發票皆直接交付買受人統一編號或進行 B2B 交換，故無提供會員載具中獎通知需求（勾選無提供會員載具）。</ns2:p></ns0:table-cell>'
    content_xml = content_xml.replace(t3_r10_exp_old, t3_r10_exp_new)

    # 5. Tables 5, 6, 7 (Firewall, Web platform, Turnkey settings)
    def check_boxes_in_table(xml, tbl_name):
        start = xml.find(f'table:name="{tbl_name}"')
        if start == -1:
            start = xml.find(f'name="{tbl_name}"')
        end = xml.find('</table:table>', start)
        if end == -1:
            end = xml.find('</ns0:table>', start)
        sub = xml[start:end]
        sub_new = sub.replace('>□</', '>☑</')
        return xml[:start] + sub_new + xml[end:]

    content_xml = check_boxes_in_table(content_xml, "表格5")
    content_xml = check_boxes_in_table(content_xml, "表格6")
    content_xml = check_boxes_in_table(content_xml, "表格7")

    # 6. Invoice Volume
    content_xml = re.sub(
        r'每週最大發票數量為<ns2:span[^>]*>[^<]*</ns2:span>筆；每月最大發票數量為<ns2:span[^>]*>[^<]*</ns2:span>筆。',
        '每週最大發票數量為 100 筆；每月最大發票數量為 500 筆。',
        content_xml
    )

    # 7. Table 8 (四、上傳結果檢測)
    # Checkbox item 1 & item 2
    t8_start = content_xml.find('name="表格8"')
    t8_end = content_xml.find('</ns0:table>', t8_start)
    t8_sub = content_xml[t8_start:t8_end]
    t8_sub = t8_sub.replace('>□</', '>☑</')

    # Item 1 Explanation
    t8_r2_old = '<ns0:table-cell ns0:style-name="表格8.C3" ns1:value-type="string"><ns2:p ns2:style-name="P27">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t8_r2_new = '<ns0:table-cell ns0:style-name="表格8.C3" ns1:value-type="string"><ns2:p ns2:style-name="P27">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：【Turnkey 處理結果確認】<ns2:line-break/>1. 本公司已建立完整之 Turnkey 傳輸與訊息記錄檢核機制。透過 Turnkey 系統【檢視訊息紀錄】及資料庫 transaction 日誌確認，所有 B2B 交換發票交易（開立 A0101、開立確認 A0102、作廢 A0201、作廢確認 A0202、退回 A0301、退回確認 A0302、折讓單開立 B0101、折讓單確認 B0102、作廢折讓單 B0201、作廢折讓單確認 B0202）及空白未使用字軌檔（E0402）均已全數傳送完成，狀態皆為「C」（大平台接收並存證成功）或「G」（Turnkey判讀資料已上傳），無任何「E」錯誤紀錄。<ns2:line-break/>2. 系統每日自動檢核 Turnkey 主機接收之 SummaryResult 與 ProcessResult，上傳發票筆數與大平台回覆成功筆數 100% 相符（處理代碼均為 00000 全部發票處理成功）。</ns2:p></ns0:table-cell>'
    t8_sub = t8_sub.replace(t8_r2_old, t8_r2_new)

    # Item 2 Explanation + Screenshot
    b2b_img_xml = '<ns2:p ns2:style-name="Standard"><draw:frame draw:name="ImageB2B" text:anchor-type="as-char" svg:width="15.5cm" svg:height="9.0cm" draw:z-index="0"><draw:image xlink:href="Pictures/proof_b2b.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/></draw:frame></ns2:p>'
    t8_r4_old = '<ns0:table-cell ns0:style-name="表格8.C5" ns1:value-type="string"><ns2:p ns2:style-name="P27">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43" /></ns0:table-cell>'
    t8_r4_new = f'<ns0:table-cell ns0:style-name="表格8.C5" ns1:value-type="string"><ns2:p ns2:style-name="P27">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：【Web 大平台線上查詢驗證佐證】<ns2:line-break/>登入財政部電子發票整合服務平台（驗測環境 https://wwwtest.einvoice.nat.gov.tw），至【營業人功能選單 ➔ Turnkey ➔ Turnkey上線前自行檢測作業】，查詢 B2B 交換各項情境測試結果。全數 14 項情境測試（A0101、A0102、A0301、A0302、A0201情境1/2、A0202情境1/2、B0101、B0102、B0201情境1/2、B0202情境1/2）處理結果全數標示為「通過」，測試發票號碼及折讓單號核驗無誤。佐證畫面如下：</ns2:p>{b2b_img_xml}</ns0:table-cell>'
    t8_sub = t8_sub.replace(t8_r4_old, t8_r4_new)

    content_xml = content_xml[:t8_start] + t8_sub + content_xml[t8_end:]

    # 8. Table 9 (五、電子發票專用字軌檢測)
    t9_start = content_xml.find('name="表格9"')
    t9_end = content_xml.find('</ns0:table>', t9_start)
    t9_sub = content_xml[t9_start:t9_end]

    # Row 1 (E0401): Checkbox -> □(免測), Test BAN -> 總公司/分公司 免測
    t9_sub = t9_sub.replace(
        '<ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P13">□</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P35">1. E0401</ns2:p>',
        '<ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P13">□<ns2:line-break/>(免測)</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P35">1. E0401</ns2:p>'
    )
    t9_sub = t9_sub.replace(
        '<ns0:table-cell ns0:style-name="表格9.C2" ns1:value-type="string"><ns2:p ns2:style-name="P35">總公司</ns2:p><ns2:p ns2:style-name="P35">分公司</ns2:p></ns0:table-cell>',
        '<ns0:table-cell ns0:style-name="表格9.C2" ns1:value-type="string"><ns2:p ns2:style-name="P35">總公司：免測</ns2:p><ns2:p ns2:style-name="P35">分公司：免測</ns2:p><ns2:p ns2:style-name="P35">（單一營業人無分支機構免測）</ns2:p></ns0:table-cell>'
    )

    # Row 2 (E0402): Checkbox -> ☑, Company BAN -> 00015555
    t9_sub = t9_sub.replace(
        '<ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P13">□</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P35">2. E0402</ns2:p>',
        '<ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P13">☑</ns2:p></ns0:table-cell><ns0:table-cell ns0:style-name="表格9.A2" ns1:value-type="string"><ns2:p ns2:style-name="P35">2. E0402</ns2:p>'
    )
    t9_sub = t9_sub.replace(
        '<ns0:table-cell ns0:style-name="表格9.C2" ns1:value-type="string"><ns2:p ns2:style-name="P35">公司統編</ns2:p></ns0:table-cell>',
        '<ns0:table-cell ns0:style-name="表格9.C2" ns1:value-type="string"><ns2:p ns2:style-name="P35">公司統編：</ns2:p><ns2:p ns2:style-name="P35">00015555</ns2:p></ns0:table-cell>'
    )

    # Row 2 E0402 Note + Proof image
    e0402_img_xml = '<ns2:p ns2:style-name="Standard"><draw:frame draw:name="ImageE0402" text:anchor-type="as-char" svg:width="15.5cm" svg:height="5.2cm" draw:z-index="0"><draw:image xlink:href="Pictures/proof_e0402.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/></draw:frame></ns2:p>'
    e0402_proof_xml = f'<ns2:p ns2:style-name="P27">(佐證畫面與說明)</ns2:p><ns2:p ns2:style-name="P43">說明：【E0402 空白未使用字軌檔檢測佐證】<ns2:line-break/>本公司（統一編號：00015555，繞送代碼：PA006753）已於 115 年 9 月 24 日透過 Turnkey 系統上傳期別 11510（LP 字軌）之空白未使用字軌檔（E0402），大平台回覆 ProcessResult 代碼 00000（全部發票處理成功）。於大平台驗測環境【E0402空白未使用發票字軌檔】線上查驗，公司統編 00015555 處理結果正式標示為「通過」。佐證畫面如下：</ns2:p>{e0402_img_xml}'
    
    t9_sub = t9_sub.replace(
        '※註：此格式欄位須要在次期10號前上傳。</ns2:p></ns0:table-cell></ns0:table-row>',
        f'※註：此格式欄位須要在次期10號前上傳。</ns2:p>{e0402_proof_xml}</ns0:table-cell></ns0:table-row>'
    )

    content_xml = content_xml[:t9_start] + t9_sub + content_xml[t9_end:]

    # NOTE: APPENDIX (Tables 10, 11, 12, pages 14-32) IS FULLY PRESERVED UNTOUCHED!

    # 9. Write to OUT_ODT
    print(f"Writing Version B ODT to: {OUT_ODT}")
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

    print("Version B ODT generated successfully!")
    print(f"File size: {os.path.getsize(OUT_ODT)} bytes")

if __name__ == "__main__":
    main()
