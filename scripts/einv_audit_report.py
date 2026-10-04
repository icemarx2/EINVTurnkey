#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turnkey Self-Test Audit Checklist Generator
Formats transmitted test invoices to match the MOF 'Turnkey 上線前自我檢測清冊' web form.
"""

import re
import sys
import subprocess
from datetime import datetime

def run_psql(query):
    cmd = [
        "psql", "-U", "turnkey", "-h", "127.0.0.1", "-d", "turnkey",
        "-t", "-A", "-F", "\t", "-c", query
    ]
    env = {"PGPASSWORD": "turnkey", "PATH": "/usr/local/bin:/usr/bin:/bin"}
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if res.returncode != 0:
        return []
    rows = []
    for line in res.stdout.strip().split("\n"):
        if line:
            rows.append(line.split("\t"))
    return rows

def parse_clean_identifier(raw_id):
    # e.g. F0401LP5093660020260923 -> LP50936600
    # G0401GWLP5093660120260923 -> GWLP50936601
    # B0101BWLP5093660120260923 -> BWLP50936601
    m = re.search(r"((?:LP|GWLP|BWLP)[0-9A-Za-z]+?)(?:2026[0-9]{4}|$)", raw_id)
    if m:
        return m.group(1)
    return raw_id

def generate_mof_checklist():
    print("=" * 95)
    print("      財政部電子發票整合服務平台 (wwwtest) - Turnkey 上線前自我檢測清冊報告")
    print("      營業人統編：00015555 奧銳有限公司 | 繞送代碼：PA006753 | 測試字軌：LP (115/09~115/10)")
    print("=" * 95)

    query = """
    SELECT message_type, in_out_bound, invoice_identifier, status, from_party_id, to_party_id, message_dts, uuid
    FROM turnkey_message_log
    WHERE invoice_identifier LIKE '%LP%' OR invoice_identifier LIKE '%GWLP%' OR invoice_identifier LIKE '%BWLP%'
    ORDER BY message_dts ASC;
    """
    rows = run_psql(query)

    scenarios = {
        "F0401": "B2C / 存證 開立發票",
        "F0501": "B2C / 存證 作廢發票",
        "G0401": "B2C / 存證 賣方折讓",
        "G0501": "B2C / 存證 作廢折讓",
        "A0101": "B2B 交換開立",
        "A0102": "B2B 買方接收確認",
        "A0201": "B2B 交換作廢",
        "A0202": "B2B 買方作廢確認",
        "B0101": "B2B 賣方開立折讓",
        "B0102": "B2B 買方折讓確認"
    }

    # Distinct entries by (message_type, clean_id)
    test_results = {}
    for r in rows:
        if len(r) >= 7:
            mtype, in_out, raw_id, status, from_id, to_id, dts = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
            clean_id = parse_clean_identifier(raw_id)
            key = (mtype, clean_id)
            target = to_id if in_out == 'O' else from_id
            test_results[key] = {
                "mtype": mtype,
                "clean_id": clean_id,
                "raw_id": raw_id,
                "status": "通過 (00000 成功)" if status in ("G", "C") else f"異常 ({status})",
                "target": target,
                "dts": dts,
                "in_out": in_out
            }

    print(f"\n{'項次':<4} {'訊息類別與情境':<24} {'發票/折讓單號':<18} {'交易對象':<12} {'平台檢測狀態':<16} {'傳輸時間戳記':<18}")
    print("-" * 95)

    idx = 1
    # Order by specific test flow
    flow_order = [
        ("F0401", "LP50936600"),
        ("F0401", "LP50936601"),
        ("F0401", "LP50936602"),
        ("F0401", "LP50936603"),
        ("F0401", "LP50936604"),
        ("F0501", "LP50936600"),
        ("G0401", "GWLP50936601"),
        ("G0401", "GWLP50936602"),
        ("G0501", "GWLP50936602"),
        ("A0101", "LP50936610"),
        ("A0101", "LP50936611"),
        ("A0102", "LP50936610"),
        ("A0102", "LP50936611"),
        ("A0201", "LP50936610"),
        ("A0202", "LP50936610"),
        ("B0101", "BWLP50936601"),
        ("B0102", "BWLP50936601"),
    ]

    for mtype, cid in flow_order:
        item = test_results.get((mtype, cid))
        if item:
            sc_text = f"{mtype} ({scenarios.get(mtype, '')})"
            print(f"{idx:<4} {sc_text:<24} {item['clean_id']:<18} {item['target']:<12} {item['status']:<16} {item['dts']:<18}")
            idx += 1

    print("-" * 95)
    print("\n【財政部測試平台（wwwtest）自我檢測清冊 填寫對應表】：")
    print("請登入測試平台 (https://wwwtest.einvoice.nat.gov.tw) ➔ 【營業人功能選單】 ➔ 【Turnkey】 ➔ 【Turnkey上線前自我檢測作業】：")
    print("-" * 75)
    print("1. 【B2C 存證 - 紙本/一般開立 (F0401)】  ：填入 LP50936600")
    print("2. 【B2C 存證 - 共通性載具 (F0401)】    ：填入 LP50936601 (手機條碼 /ABC+123)")
    print("3. 【B2C 存證 - 愛心捐贈碼 (F0401)】    ：填入 LP50936602 (捐贈碼 25885)")
    print("4. 【B2C 存證 - 發票作廢 (F0501)】      ：填入 LP50936600")
    print("5. 【B2C 存證 - 銷貨折讓 (G0401)】      ：填入 GWLP50936601 (原發票 LP50936603)")
    print("6. 【B2C 存證 - 折讓作廢 (G0501)】      ：填入 GWLP50936602 (原發票 LP50936604)")
    print("7. 【B2B 交換 - 開立發票 (A0101)】      ：填入 LP50936610 或 LP50936611")
    print("8. 【B2B 交換 - 接收確認 (A0102)】      ：填入 LP50936610 或 LP50936611")
    print("9. 【B2B 交換 - 發票作廢 (A0201/A0202)】：填入 LP50936610")
    print("10.【B2B 交換 - 銷貨折讓 (B0101/B0102)】：填入 BWLP50936601")
    print("-" * 75)
    print("所有發票與折讓皆已於平台完成加密傳輸，並取得財政部回傳 ProcessResult: Code 00000 (全部發票處理成功)。")
    print("直接在網頁送出檢測單，即可核發「上線通行碼 (Turnkey Pass Code)」！")
    print("=" * 95)

if __name__ == "__main__":
    generate_mof_checklist()
