# Turnkey Changelog

--------------------------------------------
## 2025/11/19 Version 3.2.1(gateway 3.1.3)
1. 新增 資料庫連線佇列等候逾時機制，避免因等候連線時間過長，而造成執行緒阻塞
2. 修正 調整 Pack 更新資料庫訊息狀態的流程，以避免在短時間內重複更新同一筆資料
3. 修正 資料庫連線不可用時，使用啟動密碼進行登入，會導致程式沒有回應
4. 更新 einvoice-common-qrcode 1.0.1-SNAPSHOT -> einvoice-btc-common-qrcode 2.0.0-SNAPSHOT
5. 更新 h2 資料庫 2.3.232 -> 2.4.240
6. 新增 unpack 自動判斷 E0504 檢查 MIG 版本
7. 修正 pack 交換發票，繞送代碼未設定情形下，會出現失敗訊息不ㄧ致問題
 
### (gateway) 元件
1. 新增 E0501 E0504 PR SR xsd 驗證
2. 新增 產生 xml 檔，可設定顯示 encoding 宣告抬頭
3. 新增 支援 TLS 1.3 的伺服器建立安全傳輸連線
4. 修正 F0401 xsd FreeTaxSalesAmount、ZeroTaxSalesAmount 不應為負數
5. 修正 E0502 E0503 xsd TaxAmount 不應為負數
6. 修正 E0504 xsd RandomNumber 為非必填

--------------------------------------------
## 2025/02/17 Version 3.2.0(gateway 3.1.2)
1. 新增 目錄設定可選擇v41版本
2. 新增 3.2.0 只得傳送 v41 版發票
3. 更新 3.2.0 下載流程目錄設定可設定所有版本
4. 更新 logback-classic 1.4.14->1.5.16

### (gateway) 元件
5. 新增 v41版訊息，異動訊息如下
- 5-1. B0101, B0201 需由賣方傳送。
- 5-2. B0102, B0202 需由買方傳送。
- 5-3. B0201, B0202 增加 AllowanceType 欄位，皆為必填。
- 5-4. G0401 AllowanceType只能申報2賣方傳送。
- 5-5. B0101, G0401, E0503 增加 原始發票賣方統編欄位(OriginalInvoiceSellerId), 原始發票買方統編欄位(OriginalInvoiceBuyerId)。
- 5-6. E0502, E0503 增加 註銷資料(Void)資訊。

--------------------------------------------
## 2025/01/03 Version 3.1.4(gateway 3.1.2-SNAPSHOT)
1. 新增 訊息紀錄可查詢B2S選項
2. 修正 設定啟動密碼無法接收平台通知
3. 修正 存證無法使用代理人傳送
4. 修正 H2重置資料庫時無需輸入DB密碼
5. 新增 列印存證報表出現筆數不符時，會將比對有問題之uuid寫入syslog
6. 修正 H2套件版本更新
7. 修正 由序號及檢核錯誤寫入msgLog出現的Duplicate錯誤
8. 修正 mysql protobuf-java 升級為 4.29.1
9. 新增 增加軟體憑證輸入說明，密碼只得輸入英數字8碼
10. 修正 移除jdk11密碼格式及轉換
11. 修正 移除文字模式的排程紀錄
12. 修正 mail timeout時間為10秒

### (gateway) 元件
12. 修正 v40 F0401 Amount金額欄xsd增加負數檢核
13. 新增 mig 統編欄位檢核，只能輸入數字

--------------------------------------------
## 2024/07/01 Version 3.1.3(gateway 3.1.1)
1. 修正 如果使用代理人上傳E040X，記錄檔送方使用代理人。
2. 修正 新安裝設定桌面捷徑時會顯示ICON。
3. 修正 未接收通知排除收方記錄。
4. 新增 上傳營業人 Turnkey 資訊。
5. 修正 bcprov-jdk18on 第三方套件更新。
6. 新增 檢核是否已有啟動排程，防止2組排程同時執行。
7. 修正 E0401 E0402 不列入 存證報表統計。

--------------------------------------------
## 2024/03/04 Version 3.1.2(gateway 3.1.1)
1. 修正 H2套件版本以符合資安，重新進入系統後會自動重新匯入設定資料，紀錄檔需關閉Turnkey後手動執行AlterEncrypt.cmd自動匯入。
2. 新增 H2更新前會自動備份到 工作目錄/innerfs/bak 下。
3. 移除 Turnkey 2.x 版的密碼轉換功能。
4. 修正 部份錯誤代碼
    1. 找不到送方繞送代碼 -011 改為 -003
    2. 下載失敗 -017 改為 -024
    3. sftp刪檔失敗 -017 改為 -025
    4. 排程未啟動，列表中原顯示 停止中 改為 已停止
    5. 結束排程 程式停止中 改為 排程已暫停
5. 修正 logback及okio套件。
6. 修正 目錄設定檢查更改為只檢核資料庫有無設定資料，於環境檢測時會確認是否有讀寫權限。
7. 修正 清檔效率問題。
8. 修正 更新檔原放置工作目錄下 EINVUPGRADE 改為安裝目錄下。
9. 修正 存證檢核表列印錯誤，及當天其它未傳送的繞送也會產生數據0的報表。
10. 修正 E0504 改用 AES256 解密。
11. 新增 6天內狀態未處理至C會發送mail通知。
12. 修正 postgresql、mysql jar 套件。

--------------------------------------------
## 2023/12/18 Version 3.1.1(gateway 3.1.0)
1. 新增 平台訊息通知，平台公告事項將會透過系統在登入時顯示通知，並會寫入事件記錄發mail通知。
2. 新增 當存證檢核表上線時，守門員會提示舊排程是否刪除。
3. 修正 遠端桌面黑頻問題。
4. 新增 啟動時會顯示啟動中。
5. 修正 自動更新功能。
6. 修正 收取交換發票時出現I/O錯誤。
7. 新增 ACK訊息的記錄檔明細資料。
8. 修正 事件記錄通知只顯示一個表頭。
9. 新增 通知設定寄件人未輸入檢查。
10. 新增 通知訊息、監控、db設定不限制欄位長度。
11. 新增 憑證密碼輸入錯誤，移除錯誤的pfx。
12. 新增 憑證代碼的提示訊息。
13. 修正 傳送檔案階段檢核檔案大小為20MB。
14. 新增 收取交換發票在轉檔時會加入xml宣告。
15. 新增 db中斷時會發通知。
16. 新增 當上傳轉檔時無法使用最後異動時間排序，將改用檔名排序(小至大)。
17. 新增 E0501 MIG版本會自動轉成下載目錄設定的版本。
18. 修正 清檔作業無法刪除有管理者權限內的檔案。
19. 修正 同時啟動Minitor作業會有log無法分日包檔情況。
20. 修正 精靈檢核的傳送帳號，當有綠色勾代表有帳號資料。不會檢核密碼是否正確，密碼需於環境檢核中執行傳送帳號檢核。

--------------------------------------------
## 2023/10/16 Version 3.1.0(gateway 3.1.0)
1. 新增 存證的明細從Pack至Receive只寫一筆的方式。
2. 新增 提供文字介面可做DB重置。
3. 新增 可處理v30 v40版本的ProcessResult及SummaryResult。
4. 修正 存證同封套中有相同的發票號碼無法更新狀態之異常。
5. 修正 加密填充演算法改為PKCS7Padding。
6. 新增 密碼轉換工具加密填充由PKCS5 -> PKCS7。
7. 修正 部份目錄設定、msgLog Key值錯誤及Config檔無正常儲存未提示。
8. 修正 文字模式不會自動更新。
9. 新增 存證檢核表，需配合平台測試方能使用此功能，同時合併平台回覆失敗及上傳筆數報表。
10. 新增 配合列印存證檢核表，當配合平台測試時，SummaryResult會改依傳輸日期存放。
11. 新增 組合PFX憑證發生錯誤時會有詳細提示。
12. 新增 軟體憑證密碼有8碼及只能輸入英數字防呆。
13. 修正 文字模式輸入非可使用參數導致系統停止。
14. 新增 連線測試顯示詳細說明。
15. 修正 開啟Turnkey後自動執行啟動沒有寫訊息記錄在畫面上。
16. 修正 訊息查詢狀態下拉選單，項目中的C應為「確認」。
17. 新增 更新mysql jdbc 版本 8.0.32 -> 8.1.0，mariadb 3.0.4 -> 3.1.4。
18. 新增 <zip-before-send>true</zip-before-send>可先壓縮再傳檔。
19. 新增 einvTurnkeyConfig.xml平台連線路徑。
20. 新增 Api及ProcessResult回覆代碼中英化。syslog db存證方式配合修正。
21. 新增 E0504功能，需配合平台測試方能使用。
22. 修正 windows 移除exe執行檔，只保留cmd執行檔。
23. 新增 境外電商資料，在啟動排程後，於24:00時會自動重load資料。
24. 移除 3.0.3的執行時會先顯示啟動畫面，因此次功能導致無法自動更新，會再修正後於下次還原功能。目前此版本啟動時會多等待一段時間才會顯示畫面，但執行時間與前一版本是相同的。

### (gateway) 元件
24. 新增 gateway改為 web api 模式。
25. 修正 G0501 AllowanceType為2時送方要使用seller。
26. 修正 G0401分別檢查傳送方，當allowtype為2賣方為境外電商時，買方需為消費者，allowtype為1時買方不可為消費者。
27. 修正 F0401「發票防偽隨機碼」可填入空白。
28. 修正 C0401 F0401 R0401 當列印註記N時CarrierID1不可為空，調整顯示的錯誤訊息。
29. 修正 F0401消費者使用手機條碼索取，載具顯碼id不管是否列印必填。
30. 修正 MIG V4.0 B0101、G0501 境外電商不可傳b2b發票檢核。

### 提供create index sql 如下，手動建立前請注意owner及schema是否要更換
#### 說明
1. 配合明細檔過多無用資料，將使用TURNKEY_MESSAGE_LOG_DETAIL的UUID與TURNKEY_MESSAGE_LOG做對應。將detail的uuid設為index。
2. 另 TURNKEY_MESSAGE_LOG_INDEX1 此組，因系統提供的「建立資料庫」功能未將此index加入，營業人使用「自動建立表格」功能才需執行2的ddl。重覆執行資料庫會自行報錯誤訊息，忽略即可。
#### 資料庫版本
- H2 
1. CREATE INDEX TURNKEY_MESSAGE_LOG_DETAIL_UUID_IDX ON PUBLIC.TURNKEY_MESSAGE_LOG_DETAIL (UUID);
2. CREATE INDEX TURNKEY_MESSAGE_LOG_INDEX1 ON PUBLIC.TURNKEY_MESSAGE_LOG (MESSAGE_DTS);
- PostgreSQL
1. CREATE INDEX turnkey_message_log_detail_uuid_idx ON public.turnkey_message_log_detail (uuid);
2. CREATE INDEX turnkey_message_log_index1 ON public.turnkey_message_log (message_dts);
- MySQL
1. CREATE INDEX TURNKEY_MESSAGE_LOG_DETAIL_UUID_IDX USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG_DETAIL (UUID);
2. CREATE INDEX TURNKEY_MESSAGE_LOG_INDEX1 USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG (MESSAGE_DTS);
- MsSQL
1. CREATE INDEX TURNKEY_MESSAGE_LOG_DETAIL_UUID_IDX ON turnkey.dbo.TURNKEY_MESSAGE_LOG_DETAIL (UUID);
2. CREATE INDEX TURNKEY_MESSAGE_LOG_INDEX1 ON turnkey.dbo.TURNKEY_MESSAGE_LOG (MESSAGE_DTS);
- Oracle
1. CREATE INDEX TURNKEY_MESSAGE_LOG_DETAIL_UUID_IDX ON TURNKEY.TURNKEY_MESSAGE_LOG_DETAIL (UUID);
2. CREATE INDEX TURNKEY_MESSAGE_LOG_INDEX1 ON TURNKEY.TURNKEY_MESSAGE_LOG (MESSAGE_DTS);
- MariaDB
1. CREATE INDEX TURNKEY_MESSAGE_LOG_DETAIL_UUID_IDX USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG_DETAIL (UUID);
2. CREATE INDEX TURNKEY_MESSAGE_LOG_INDEX1 USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG (MESSAGE_DTS);

--------------------------------------------
## 2023/7/31 Version 3.0.3(gateway 3.0.2)
1. 新增 執行啟動時未放入IC卡片將會提示卡片不存在；新增軟體憑證時憑證密碼輸入錯誤或PFX檔案損毀會顯示相對應提示。
2. 新增 UpCast 不會處理內容為空的檔案。
3. 修正 Linux 啟動 AlterEncrypt 問題。
4. 修正 Pack 時DB未寫入繞送資料。
5. 修正 配合mariadb 修正sql語法。
6. 修正 3.0.2更版後無法收取交換發票。
7. 修正 Linux啟動指令。
8. 修正 訊息紀錄查詢時會出現空白，需要點畫面一下才會跑出資料來。
9. 修正 清檔功能沒有顯示log。
10. 修正 呼叫WebService的timeout時間為120秒。
11. 修正 守門員列印報表功能，日期改為傳輸日期，日期選擇改為只能選擇單一日期。
12. 修正 排程作業畫面增加 scrollbar。

--------------------------------------------
## 2023/6/26 Version 3.0.2(gateway 3.0.1)
1. 修正 linux 目錄設定問題。
2. 修正 背景程式執行出現境外電商錯誤。
3. 修正 通知信件主旨亂碼及中英文通知。
4. 修正 通知設定未輸入密碼無法儲存問題。
5. 新增 UpCast處理存證資料時，滿足1千筆發票後將打包至Pack。
6. 修正 寫資料庫過慢問題。
7. 新增 UpCast時，存證發票查無送方設定時，使用代理人。
8. 修正 MSSQL無法使用INSTANCE問題。
9. 新增 通知訊息的mail server 不會檢核是否有CA認證。
10. 新增 可使用發票號碼在發票識別碼欄做查詢。
11. 新增 通知訊息密碼不限長度。
12. 新增 訊息查詢可使用uuid群組查詢，以便查詢上傳檔案結果。
13. 修正 調整pack 至 unpack的效能。
14. 修正 多筆寫入syslog時，取sysdate的方式使用連續值，不再重取時間。
15. 修正 排程啟動後，狀態條動畫影響CPU效能。
16. 新增 訊息查詢可以查詢舊版事件記錄。
17. 提升uuid群組查詢，需將TURNKEY_MESSAGE_LOG 加上 UUID + MESSAGE_DTS 為 INDEX。
### 提供create index sql 如下，手動建立前請注意owner及schema是否要更換
1. H2 
- CREATE INDEX TURNKEY_MESSAGE_LOG_UUID_IDX ON PUBLIC.TURNKEY_MESSAGE_LOG (UUID,MESSAGE_DTS);
2. PostgreSQL
- CREATE INDEX turnkey_message_log_uuid_idx ON public.turnkey_message_log USING btree (uuid, message_dts);
3. MySQL
- CREATE INDEX TURNKEY_MESSAGE_LOG_UUID_IDX USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG (UUID,MESSAGE_DTS);
4. MsSQL
- CREATE INDEX TURNKEY_MESSAGE_LOG_UUID_IDX ON turnkey.dbo.TURNKEY_MESSAGE_LOG (UUID,MESSAGE_DTS);
5. Oracle
- CREATE INDEX TURNKEY_MESSAGE_LOG_UUID_IDX ON TURNKEY.TURNKEY_MESSAGE_LOG (UUID,MESSAGE_DTS);
6. MariaDB
- CREATE INDEX TURNKEY_MESSAGE_LOG_UUID_IDX USING BTREE ON turnkey.TURNKEY_MESSAGE_LOG (UUID,MESSAGE_DTS);

--------------------------------------------
## 2023/5/8 Version 3.0.1(gateway 3.0.1)
1. DB轉換工具提供密碼還原功能。
2. 新增 可以處理BOM檔發票檔案。
3. 修正 MsSql寫入事件記錄檔因中文字長度問題。
4. 新增 資料庫名稱可輸入100字元。
5. 修正 已輸入正確傳送帳密，檢核出有誤情況。
6. 新增 自動處理營業人MIG欄位順序不正確問題。
7. 修正 自動創建表格功能，欄位宣告改用大寫。
8. 修正 文字介面連線資料庫設定無法輸入資料庫名稱。
9. 新增 通知設定及監控可輸入多個通知mail，使用分號隔開(不加空白)。
10. 修正 v3.0.0自動更新下載問題。

--------------------------------------------
## 2023/5/1 Version 3.0.0(gateway 3.0.0)
1. 新版Turnkey上線
