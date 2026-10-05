# Evidence capture checklist (Turnkey 上線前自行檢測作業)

Rule for everything below: **unedited, full-window screenshots of the real
system, with date/time visible. No banners, labels or text added to the image.**
Explanations go in the 說明 box, and the 說明 must describe only what the
screenshot really shows.

## 0. Before you start
- [ ] Decide the real set of test documents (use the platform's own
      線上檢測 table as the source of truth: it already lists invoice/allowance
      numbers per scenario).
- [ ] Edit `CFG` at the top of `erp_bridge_checks.py` so table/column names match
      your real database. Run `python3 erp_bridge_checks.py all` once to see it work.
- [ ] Install the daily schedule (adjust paths):
      ```
      0 23 * * *  /usr/bin/python3 /opt/erp/erp_bridge_checks.py all --dir /path/to/SummaryResult >> /var/log/einv/daily_audit.log 2>&1
      ```
- [ ] Optional email alert: set `SMTP_HOST`, `EINV_ALERT_TO` (and `SMTP_PORT/USER/PASS/FROM`)
      in the cron environment. The script prints whether the email really went out.

## 1. 字軌檢核 (reviewer point 1)
- [ ] `crontab -l` showing the daily job.
- [ ] `SELECT ... FROM einv_track_quota;` (real registered range).
- [ ] Positive run: `erp_bridge_checks.py track`.
- [ ] Negative run (real validator, no data written):
      `erp_bridge_checks.py track --check-number AB12345678 --check-number LP99999999`
- [ ] The alert as it really arrived: the email in your mailbox and/or `tail alert.log`.
- [ ] Also show your issuing code refusing a bad number (call the same rule
      before `allocate_next_invoice_number`), if that is how your system works.

## 2. 重號檢核
- [ ] Unique index definition (`\d orders` or `pg_indexes`).
- [ ] A real duplicate INSERT attempt and the real PostgreSQL error (run in a
      test transaction and roll back).
- [ ] `erp_bridge_checks.py duplicate` output (it also verifies the index exists).

## 3. 漏上傳檢核
- [ ] Cron line for the daily job.
- [ ] `erp_bridge_checks.py missing` on real data. For a negative case, leave a
      test invoice un-sent (PENDING) for the run, capture the alert, then
      re-send it and capture the clean run. Re-sending is manual here; say so
      in the 說明 (the form accepts "供管理者補傳").

## 4. 發票異常處理檢核
- [ ] 4(1) A real `E` status from Turnkey (e.g. send a test message with a known
      error in the test environment), the FAILED flag in the ERP, and
      `erp_bridge_checks.py errors` listing it; then the corrected re-upload with status C.
- [ ] 4(2) Open a **real** SummaryResult file from Turnkey first. If the tag
      names differ from `parse_summary()` (it will tell you, exit code 2),
      adjust the name lists. Then capture `erp_bridge_checks.py summary --dir ... --date ...`
      next to the SummaryResult file itself.

## 5. Turnkey 確認 (reviewer point 2)
- [ ] Real Turnkey: 檢視訊息紀錄, filter status **C**, date range covering all
      test days. Whole window, status column visible. If the list is long,
      take several consecutive screenshots, no stitching.
- [ ] Check that the footer/connection shows the **test** host (`tgw.`), as in
      your own STEP 1 table.
- [ ] Also capture the real SummaryResult / ProcessResult files for the same days.

## 6. 大平台查詢確認 (reviewer point 3)
- [ ] Log in to `wwwtest.einvoice.nat.gov.tw`, open 營業人功能選單 > 查詢與下載 >
      發票查詢. Capture with the **address bar visible**, whole page, query
      range covering every test number, all columns.
- [ ] Capture the 線上檢測 result table showing 通過 for all items (you already
      have this one from the platform).
- [ ] Keep the E0402 check page (already have it).

## 7. Consistency check before you submit
- [ ] Numbers in the ERP outputs, Turnkey log and platform pages tell one story
      (same invoices, same dates, same counts). If something genuinely looks
      odd (e.g. an allowance whose base invoice was voided), explain it
      plainly in the 說明.
- [ ] 完成檢測日期 on page 2 matches the dates in the screenshots.
- [ ] Use 大平台 (not 整合服務平台) in your own text.
- [ ] Keep the original raw screenshots and logs in case the reviewer asks.
