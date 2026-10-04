#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate and transmit B2B Allowance Scenario 1 (with confirmation before cancel):
BWLP50936603: B0101 -> B0102 -> B0201 -> B0202
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
TURNKEY_BASE = "/invoice/EINVTurnkey"

def dispatch(sub_dir, fname, content):
    target_dir = os.path.join(TURNKEY_BASE, "UpCast", "B2BEXCHANGE", sub_dir, "SRC")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, fname)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[*] Dispatched to {target_path}")

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
            <UnitPrice>1000</UnitPrice>
            <Amount>1000</Amount>
            <Tax>50</Tax>
            <AllowanceSequenceNumber>001</AllowanceSequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <TaxAmount>50</TaxAmount>
        <TotalAmount>1000</TotalAmount>
    </Amount>
</Allowance>""".strip()

def get_b0102_xml(allowance_num, allowance_date, recv_date, recv_time):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<AllowanceConfirm xmlns="urn:GEINV:eInvoiceMessage:B0102:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <AllowanceNumber>{allowance_num}</AllowanceNumber>
    <AllowanceDate>{allowance_date}</AllowanceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <ReceiveDate>{recv_date}</ReceiveDate>
    <ReceiveTime>{recv_time}</ReceiveTime>
    <AllowanceType>2</AllowanceType>
</AllowanceConfirm>""".strip()

def get_b0201_xml(cancel_allowance_num, allowance_date, cancel_date, cancel_time, reason="折讓確認後更正作廢"):
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

def main():
    now = datetime.now()
    d_today = now.strftime("%Y%m%d")
    t1 = now.strftime("%H:%M:%S")
    t2 = (now + timedelta(minutes=1)).strftime("%H:%M:%S")

    # Step 1: Issue B0101
    print("Step 1: B0101 BWLP50936603")
    dispatch("B0101", "B0101_BWLP50936603.xml", get_b0101_xml("BWLP50936603", d_today, "LP50936611", "20260923"))
    time.sleep(3)

    # Step 2: Confirm B0102
    print("Step 2: B0102 BWLP50936603")
    dispatch("B0102", "B0102_BWLP50936603.xml", get_b0102_xml("BWLP50936603", d_today, d_today, t1))
    time.sleep(3)

    # Step 3: Cancel B0201
    print("Step 3: B0201 BWLP50936603")
    dispatch("B0201", "B0201_BWLP50936603.xml", get_b0201_xml("BWLP50936603", d_today, d_today, t2))
    time.sleep(3)

    # Step 4: Confirm Cancel B0202
    print("Step 4: B0202 BWLP50936603")
    dispatch("B0202", "B0202_BWLP50936603.xml", get_b0202_xml("BWLP50936603", d_today, d_today, t2))

if __name__ == "__main__":
    main()
