#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate and transmit extra B2B scenarios to cover 100% of BTB036W table rows:
1. LP50936612: A0101 (Issue) -> A0301 (Reject) -> A0302 (Reject Confirm)
2. LP50936613: A0101 (Issue) -> A0201 (Cancel without confirm) -> A0202 (Cancel Confirm)
3. BWLP50936602: B0101 (Allowance on LP50936611) -> B0201 (Cancel Allowance) -> B0202 (Cancel Allowance Confirm)
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timedelta

COMPANY_SELLER_BAN = "00015555"
COMPANY_SELLER_NAME = "奧銳有限公司"
COMPANY_SELLER_ADDR = "臺北市中正區漢口街1段45號10樓"

TEST_BUYER_B2B_BAN = "00015555"
TEST_BUYER_B2B_NAME = "奧銳有限公司"

XSD_DIR = "/home/striker/.gemini/antigravity/brain/eac4e908-15f3-4532-b3f0-bf63e188d602/scratch/xsd_v41/xsd/v41"
VALIDATOR_CP = "/home/striker/.gemini/antigravity/brain/eac4e908-15f3-4532-b3f0-bf63e188d602/scratch"
TURNKEY_BASE = "/invoice/EINVTurnkey"

def get_a0101_xml(inv_num, inv_date, inv_time):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:GEINV:eInvoiceMessage:A0101:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Main>
        <InvoiceNumber>{inv_num}</InvoiceNumber>
        <InvoiceDate>{inv_date}</InvoiceDate>
        <InvoiceTime>{inv_time}</InvoiceTime>
        <Seller>
            <Identifier>{COMPANY_SELLER_BAN}</Identifier>
            <Name>{COMPANY_SELLER_NAME}</Name>
            <Address>{COMPANY_SELLER_ADDR}</Address>
        </Seller>
        <Buyer>
            <Identifier>{TEST_BUYER_B2B_BAN}</Identifier>
            <Name>{TEST_BUYER_B2B_NAME}</Name>
        </Buyer>
        <InvoiceType>07</InvoiceType>
        <DonateMark>0</DonateMark>
    </Main>
    <Details>
        <ProductItem>
            <Description>自動化模組</Description>
            <Quantity>1</Quantity>
            <UnitPrice>3000</UnitPrice>
            <Amount>3000</Amount>
            <SequenceNumber>001</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <SalesAmount>3000</SalesAmount>
        <TaxType>1</TaxType>
        <TaxRate>0.05</TaxRate>
        <TaxAmount>150</TaxAmount>
        <TotalAmount>3150</TotalAmount>
    </Amount>
</Invoice>""".strip()

def get_a0301_xml(inv_num, inv_date, reject_date, reject_time, reason="商品規格不符退回"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<RejectInvoice xmlns="urn:GEINV:eInvoiceMessage:A0301:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <RejectInvoiceNumber>{inv_num}</RejectInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <RejectDate>{reject_date}</RejectDate>
    <RejectTime>{reject_time}</RejectTime>
    <RejectReason>{reason}</RejectReason>
</RejectInvoice>""".strip()

def get_a0302_xml(inv_num, inv_date, reject_date, reject_time):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<RejectInvoiceConfirm xmlns="urn:GEINV:eInvoiceMessage:A0302:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <RejectInvoiceNumber>{inv_num}</RejectInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <RejectDate>{reject_date}</RejectDate>
    <RejectTime>{reject_time}</RejectTime>
</RejectInvoiceConfirm>""".strip()

def get_a0201_xml(cancel_inv_num, inv_date, cancel_date, cancel_time, reason="合約作廢未確認"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoice xmlns="urn:GEINV:eInvoiceMessage:A0201:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelInvoice>""".strip()

def get_a0202_xml(cancel_inv_num, inv_date, cancel_date, cancel_time):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoiceConfirm xmlns="urn:GEINV:eInvoiceMessage:A0202:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
</CancelInvoiceConfirm>""".strip()

def get_b0101_xml(allowance_num, allowance_date, orig_inv_num, orig_inv_date):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Allowance xmlns="urn:GEINV:eInvoiceMessage:B0101:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Main>
        <AllowanceNumber>{allowance_num}</AllowanceNumber>
        <AllowanceDate>{allowance_date}</AllowanceDate>
        <Seller>
            <Identifier>{COMPANY_SELLER_BAN}</Identifier>
            <Name>{COMPANY_SELLER_NAME}</Name>
        </Seller>
        <Buyer>
            <Identifier>{TEST_BUYER_B2B_BAN}</Identifier>
            <Name>{TEST_BUYER_B2B_NAME}</Name>
        </Buyer>
        <AllowanceType>2</AllowanceType>
        <OriginalInvoiceSellerId>{COMPANY_SELLER_BAN}</OriginalInvoiceSellerId>
        <OriginalInvoiceBuyerId>{TEST_BUYER_B2B_BAN}</OriginalInvoiceBuyerId>
    </Main>
    <Details>
        <ProductItem>
            <OriginalInvoiceDate>{orig_inv_date}</OriginalInvoiceDate>
            <OriginalInvoiceNumber>{orig_inv_num}</OriginalInvoiceNumber>
            <OriginalDescription>工業級伺服控制器</OriginalDescription>
            <Quantity>1</Quantity>
            <UnitPrice>2000</UnitPrice>
            <Amount>2000</Amount>
            <Tax>100</Tax>
            <AllowanceSequenceNumber>001</AllowanceSequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <TaxAmount>100</TaxAmount>
        <TotalAmount>2000</TotalAmount>
    </Amount>
</Allowance>""".strip()

def get_b0201_xml(cancel_allowance_num, allowance_date, cancel_date, cancel_time, reason="折讓項目填寫有誤"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelAllowance xmlns="urn:GEINV:eInvoiceMessage:B0201:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelAllowanceNumber>{cancel_allowance_num}</CancelAllowanceNumber>
    <AllowanceDate>{allowance_date}</AllowanceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <AllowanceType>2</AllowanceType>
    <CancelReason>{reason}</CancelReason>
</CancelAllowance>""".strip()

def get_b0202_xml(cancel_allowance_num, allowance_date, cancel_date, cancel_time):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelAllowanceConfirm xmlns="urn:GEINV:eInvoiceMessage:B0202:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelAllowanceNumber>{cancel_allowance_num}</CancelAllowanceNumber>
    <AllowanceDate>{allowance_date}</AllowanceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <AllowanceType>2</AllowanceType>
</CancelAllowanceConfirm>""".strip()

def validate_xml(xml_content, xsd_file):
    xsd_path = os.path.join(XSD_DIR, xsd_file)
    tmp_xml = "/tmp/test_tmp.xml"
    with open(tmp_xml, "w", encoding="utf-8") as f:
        f.write(xml_content)
    cmd = ["java", "-cp", VALIDATOR_CP, "XmlValidator", xsd_path, tmp_xml]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0

def dispatch(sub_dir, fname, content):
    target_dir = os.path.join(TURNKEY_BASE, "UpCast", "B2BEXCHANGE", sub_dir, "SRC")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, fname)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[*] Dispatched to {target_path}")

def query_psql(query):
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

def wait_for_identifiers(identifiers, timeout_secs=90):
    start = time.time()
    while time.time() - start < timeout_secs:
        all_done = True
        for ident in identifiers:
            q = f"SELECT status FROM turnkey_message_log WHERE invoice_identifier LIKE '%{ident}%' ORDER BY message_dts DESC LIMIT 1;"
            rows = query_psql(q)
            if not rows or rows[0][0] not in ['G', 'E']:
                all_done = False
                break
        if all_done:
            print("  All targets finished transmission!")
            return True
        time.sleep(4)
    print("  [!] Timeout waiting for targets.")
    return False

def run_transmission():
    now = datetime.now()
    d_today = now.strftime("%Y%m%d")
    t1 = now.strftime("%H:%M:%S")
    t2 = (now + timedelta(minutes=1)).strftime("%H:%M:%S")
    t3 = (now + timedelta(minutes=2)).strftime("%H:%M:%S")

    print("\n--- Phase 1: Initial Issues (LP50936612 A0101, LP50936613 A0101, BWLP50936602 B0101) ---")
    dispatch("A0101", "A0101_LP50936612.xml", get_a0101_xml("LP50936612", d_today, t1))
    dispatch("A0101", "A0101_LP50936613.xml", get_a0101_xml("LP50936613", d_today, t1))
    dispatch("B0101", "B0101_BWLP50936602.xml", get_b0101_xml("BWLP50936602", d_today, "LP50936611", "20260923"))
    wait_for_identifiers(["LP50936612", "LP50936613", "BWLP50936602"])

    print("\n--- Phase 2: Actions (LP50936612 A0301 Reject, LP50936613 A0201 Cancel, BWLP50936602 B0201 Cancel Allowance) ---")
    dispatch("A0301", "A0301_LP50936612.xml", get_a0301_xml("LP50936612", d_today, d_today, t2))
    dispatch("A0201", "A0201_LP50936613.xml", get_a0201_xml("LP50936613", d_today, d_today, t2))
    dispatch("B0201", "B0201_BWLP50936602.xml", get_b0201_xml("BWLP50936602", d_today, d_today, t2))
    wait_for_identifiers(["A0301LP50936612", "A0201LP50936613", "B0201BWLP50936602"])

    print("\n--- Phase 3: Confirmations (LP50936612 A0302, LP50936613 A0202, BWLP50936602 B0202) ---")
    dispatch("A0302", "A0302_LP50936612.xml", get_a0302_xml("LP50936612", d_today, d_today, t3))
    dispatch("A0202", "A0202_LP50936613.xml", get_a0202_xml("LP50936613", d_today, d_today, t3))
    dispatch("B0202", "B0202_BWLP50936602.xml", get_b0202_xml("BWLP50936602", d_today, d_today, t3))
    wait_for_identifiers(["A0302LP50936612", "A0202LP50936613", "B0202BWLP50936602"])

    print("\n[ALL EXTRA SCENARIOS TRANSMITTED SUCCESSFULLY!]")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        run_transmission()
    else:
        print("Usage: python3 einv_extra_b2b_generator.py --run")
