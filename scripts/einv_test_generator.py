#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taiwan MOF Electronic Invoice MIG 4.1 Test Dataset Generator & Orchestrator
Supports both B2C (B2SSTORAGE) and B2B (B2BEXCHANGE).
Entity: 奧銳有限公司 (00015555) | Routing: PA006753
Allocated Test Range: LP50936600 ~ LP50939099 (115/09 ~ 115/10)
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime, timedelta

COMPANY_SELLER_BAN = "00015555"
COMPANY_SELLER_NAME = "奧銳有限公司"
COMPANY_SELLER_ADDR = "臺北市中正區漢口街1段45號10樓"

TEST_BUYER_B2B_BAN = "00015555"
TEST_BUYER_B2B_NAME = "奧銳有限公司"

TEST_BUYER_B2C_BAN = "0000000000"
TEST_BUYER_B2C_NAME = "個人消費者"

XSD_BASE_DIR = "/home/striker/.gemini/antigravity/brain/eac4e908-15f3-4532-b3f0-bf63e188d602/scratch/xsd_v41/xsd/v41"
VALIDATOR_CP = "/home/striker/.gemini/antigravity/brain/eac4e908-15f3-4532-b3f0-bf63e188d602/scratch"
TURNKEY_BASE = "/invoice/EINVTurnkey"

def get_f0401_xml(inv_num, inv_date, inv_time, scenario="consumer_paper"):
    """
    Generate F0401 MIG 4.1 XML
    scenario options: 'consumer_paper', 'consumer_carrier', 'consumer_donate', 'b2b_storage'
    """
    if scenario == "consumer_carrier":
        buyer_ban = TEST_BUYER_B2C_BAN
        buyer_name = TEST_BUYER_B2C_NAME
        print_mark = "N"
        donate_mark = "0"
        carrier_block = """        <CarrierType>3J0002</CarrierType>
        <CarrierId1>/ABC+123</CarrierId1>
        <CarrierId2>/ABC+123</CarrierId2>"""
        npoban_block = ""
    elif scenario == "consumer_donate":
        buyer_ban = TEST_BUYER_B2C_BAN
        buyer_name = TEST_BUYER_B2C_NAME
        print_mark = "N"
        donate_mark = "1"
        carrier_block = ""
        npoban_block = """        <NPOBAN>25885</NPOBAN>"""
    elif scenario == "b2b_storage":
        buyer_ban = TEST_BUYER_B2B_BAN
        buyer_name = TEST_BUYER_B2B_NAME
        print_mark = "Y"
        donate_mark = "0"
        carrier_block = ""
        npoban_block = ""
    else:  # consumer_paper
        buyer_ban = TEST_BUYER_B2C_BAN
        buyer_name = TEST_BUYER_B2C_NAME
        print_mark = "Y"
        donate_mark = "0"
        carrier_block = ""
        npoban_block = ""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:GEINV:eInvoiceMessage:F0401:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
            <Identifier>{buyer_ban}</Identifier>
            <Name>{buyer_name}</Name>
        </Buyer>
        <InvoiceType>07</InvoiceType>
        <DonateMark>{donate_mark}</DonateMark>
{carrier_block if carrier_block else ''}
        <PrintMark>{print_mark}</PrintMark>
{npoban_block if npoban_block else ''}
        <RandomNumber>9876</RandomNumber>
    </Main>
    <Details>
        <ProductItem>
            <Description>智慧遙控器</Description>
            <Quantity>1</Quantity>
            <UnitPrice>400</UnitPrice>
            <Amount>400</Amount>
            <SequenceNumber>001</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
        <ProductItem>
            <Description>定時排插</Description>
            <Quantity>2</Quantity>
            <UnitPrice>300</UnitPrice>
            <Amount>600</Amount>
            <SequenceNumber>002</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <SalesAmount>1000</SalesAmount>
        <FreeTaxSalesAmount>0</FreeTaxSalesAmount>
        <ZeroTaxSalesAmount>0</ZeroTaxSalesAmount>
        <TaxType>1</TaxType>
        <TaxRate>0.05</TaxRate>
        <TaxAmount>50</TaxAmount>
        <TotalAmount>1050</TotalAmount>
    </Amount>
</Invoice>
"""
    return "\n".join([line for line in xml.splitlines() if line.strip()])

def get_f0501_xml(cancel_inv_num, inv_date, cancel_date, cancel_time, reason="買受人要求退換貨作廢"):
    """
    Generate F0501 MIG 4.1 Cancel Invoice XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoice xmlns="urn:GEINV:eInvoiceMessage:F0501:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2C_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelInvoice>
"""
    return xml.strip()

def get_g0401_xml(allowance_num, allowance_date, orig_inv_num, orig_inv_date):
    """
    Generate G0401 MIG 4.1 Allowance XML (Seller Issued AllowanceType=2)
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Allowance xmlns="urn:GEINV:eInvoiceMessage:G0401:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
            <OriginalDescription>定時排插</OriginalDescription>
            <Quantity>1</Quantity>
            <UnitPrice>300</UnitPrice>
            <Amount>300</Amount>
            <Tax>15</Tax>
            <AllowanceSequenceNumber>001</AllowanceSequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <TaxAmount>15</TaxAmount>
        <TotalAmount>300</TotalAmount>
    </Amount>
</Allowance>
"""
    return xml.strip()

def get_g0501_xml(cancel_allowance_num, allowance_date, cancel_date, cancel_time, reason="折讓金額有誤作廢"):
    """
    Generate G0501 MIG 4.1 Cancel Allowance XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelAllowance xmlns="urn:GEINV:eInvoiceMessage:G0501:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelAllowanceNumber>{cancel_allowance_num}</CancelAllowanceNumber>
    <AllowanceType>2</AllowanceType>
    <AllowanceDate>{allowance_date}</AllowanceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelAllowance>
"""
    return xml.strip()

def get_a0101_xml(inv_num, inv_date, inv_time):
    """
    Generate A0101 MIG 4.1 B2B Exchange Invoice Issue XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
            <Description>工業級伺服控制器</Description>
            <Quantity>2</Quantity>
            <UnitPrice>5000</UnitPrice>
            <Amount>10000</Amount>
            <SequenceNumber>001</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <SalesAmount>10000</SalesAmount>
        <TaxType>1</TaxType>
        <TaxRate>0.05</TaxRate>
        <TaxAmount>500</TaxAmount>
        <TotalAmount>10500</TotalAmount>
    </Amount>
</Invoice>
"""
    return xml.strip()

def get_a0102_xml(inv_num, inv_date, recv_date, recv_time):
    """
    Generate A0102 MIG 4.1 B2B Invoice Confirm XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<InvoiceConfirm xmlns="urn:GEINV:eInvoiceMessage:A0102:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <InvoiceNumber>{inv_num}</InvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <ReceiveDate>{recv_date}</ReceiveDate>
    <ReceiveTime>{recv_time}</ReceiveTime>
</InvoiceConfirm>
"""
    return xml.strip()

def get_a0201_xml(cancel_inv_num, inv_date, cancel_date, cancel_time, reason="買賣合約變更作廢"):
    """
    Generate A0201 MIG 4.1 B2B Cancel Invoice Issue XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoice xmlns="urn:GEINV:eInvoiceMessage:A0201:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelInvoice>
"""
    return xml.strip()

def get_a0202_xml(cancel_inv_num, inv_date, cancel_date, cancel_time):
    """
    Generate A0202 MIG 4.1 B2B Cancel Confirm XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoiceConfirm xmlns="urn:GEINV:eInvoiceMessage:A0202:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
</CancelInvoiceConfirm>
"""
    return xml.strip()

def get_b0101_xml(allowance_num, allowance_date, orig_inv_num, orig_inv_date):
    """
    Generate B0101 MIG 4.1 B2B Allowance Issue XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
            <UnitPrice>5000</UnitPrice>
            <Amount>5000</Amount>
            <Tax>250</Tax>
            <AllowanceSequenceNumber>001</AllowanceSequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>
    </Details>
    <Amount>
        <TaxAmount>250</TaxAmount>
        <TotalAmount>5000</TotalAmount>
    </Amount>
</Allowance>
"""
    return xml.strip()

def get_b0102_xml(allowance_num, allowance_date, recv_date, recv_time):
    """
    Generate B0102 MIG 4.1 B2B Allowance Confirm XML
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<AllowanceConfirm xmlns="urn:GEINV:eInvoiceMessage:B0102:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <AllowanceNumber>{allowance_num}</AllowanceNumber>
    <AllowanceDate>{allowance_date}</AllowanceDate>
    <BuyerId>{TEST_BUYER_B2B_BAN}</BuyerId>
    <SellerId>{COMPANY_SELLER_BAN}</SellerId>
    <ReceiveDate>{recv_date}</ReceiveDate>
    <ReceiveTime>{recv_time}</ReceiveTime>
    <AllowanceType>2</AllowanceType>
</AllowanceConfirm>
"""
    return xml.strip()

def get_stage_definitions(prefix="LP", base_seq=50936600):
    """
    Define test items grouped into chronological dependency stages.
    """
    now = datetime.now()
    inv_date = now.strftime("%Y%m%d")
    t1 = now.strftime("%H:%M:%S")
    t2 = (now + timedelta(minutes=1)).strftime("%H:%M:%S")
    t3 = (now + timedelta(minutes=2)).strftime("%H:%M:%S")
    t4 = (now + timedelta(minutes=3)).strftime("%H:%M:%S")

    # Invoices numbers
    num_b2c_paper = f"{prefix}{base_seq:08d}"         # 50936600 -> F0501 Cancel later
    num_b2c_carrier = f"{prefix}{base_seq + 1:08d}"   # 50936601 -> Mobile Carrier
    num_b2c_donate = f"{prefix}{base_seq + 2:08d}"    # 50936602 -> Donation
    num_b2c_b2b_1 = f"{prefix}{base_seq + 3:08d}"     # 50936603 -> G0401 Allowance later
    num_b2c_b2b_2 = f"{prefix}{base_seq + 4:08d}"     # 50936604 -> G0401 Allowance then G0501 Cancel later

    num_b2b_inv_1 = f"{prefix}{base_seq + 10:08d}"    # 50936610 -> A0102 Confirm, A0201 Cancel, A0202 Confirm
    num_b2b_inv_2 = f"{prefix}{base_seq + 11:08d}"    # 50936611 -> A0102 Confirm, B0101 Allowance, B0102 Confirm

    # Allowance numbers
    gw_num_1 = f"GW{prefix}50936601"
    gw_num_2 = f"GW{prefix}50936602"
    bw_num_1 = f"BW{prefix}50936601"

    stages = {
        1: {
            "name": "Stage 1: Issue Invoices (B2C F0401 + B2B A0101)",
            "files": [
                ("B2SSTORAGE/F0401", f"F0401_{num_b2c_paper}.xml", get_f0401_xml(num_b2c_paper, inv_date, t1, "consumer_paper"), "F0401.xsd"),
                ("B2SSTORAGE/F0401", f"F0401_{num_b2c_carrier}.xml", get_f0401_xml(num_b2c_carrier, inv_date, t1, "consumer_carrier"), "F0401.xsd"),
                ("B2SSTORAGE/F0401", f"F0401_{num_b2c_donate}.xml", get_f0401_xml(num_b2c_donate, inv_date, t1, "consumer_donate"), "F0401.xsd"),
                ("B2SSTORAGE/F0401", f"F0401_{num_b2c_b2b_1}.xml", get_f0401_xml(num_b2c_b2b_1, inv_date, t1, "b2b_storage"), "F0401.xsd"),
                ("B2SSTORAGE/F0401", f"F0401_{num_b2c_b2b_2}.xml", get_f0401_xml(num_b2c_b2b_2, inv_date, t1, "b2b_storage"), "F0401.xsd"),
                ("B2BEXCHANGE/A0101", f"A0101_{num_b2b_inv_1}.xml", get_a0101_xml(num_b2b_inv_1, inv_date, t1), "A0101.xsd"),
                ("B2BEXCHANGE/A0101", f"A0101_{num_b2b_inv_2}.xml", get_a0101_xml(num_b2b_inv_2, inv_date, t1), "A0101.xsd"),
            ]
        },
        2: {
            "name": "Stage 2: Confirm Invoices & Issue Allowances (A0102 + G0401 + B0101)",
            "files": [
                ("B2BEXCHANGE/A0102", f"A0102_{num_b2b_inv_1}.xml", get_a0102_xml(num_b2b_inv_1, inv_date, inv_date, t2), "A0102.xsd"),
                ("B2BEXCHANGE/A0102", f"A0102_{num_b2b_inv_2}.xml", get_a0102_xml(num_b2b_inv_2, inv_date, inv_date, t2), "A0102.xsd"),
                ("B2SSTORAGE/G0401", f"G0401_{gw_num_1}.xml", get_g0401_xml(gw_num_1, inv_date, num_b2c_b2b_1, inv_date), "G0401.xsd"),
                ("B2SSTORAGE/G0401", f"G0401_{gw_num_2}.xml", get_g0401_xml(gw_num_2, inv_date, num_b2c_b2b_2, inv_date), "G0401.xsd"),
                ("B2BEXCHANGE/B0101", f"B0101_{bw_num_1}.xml", get_b0101_xml(bw_num_1, inv_date, num_b2b_inv_2, inv_date), "B0101.xsd"),
            ]
        },
        3: {
            "name": "Stage 3: Confirm Allowances & Issue Cancels (B0102 + F0501 + G0501 + A0201)",
            "files": [
                ("B2BEXCHANGE/B0102", f"B0102_{bw_num_1}.xml", get_b0102_xml(bw_num_1, inv_date, inv_date, t3), "B0102.xsd"),
                ("B2SSTORAGE/F0501", f"F0501_{num_b2c_paper}.xml", get_f0501_xml(num_b2c_paper, inv_date, inv_date, t3), "F0501.xsd"),
                ("B2SSTORAGE/G0501", f"G0501_{gw_num_2}.xml", get_g0501_xml(gw_num_2, inv_date, inv_date, t3), "G0501.xsd"),
                ("B2BEXCHANGE/A0201", f"A0201_{num_b2b_inv_1}.xml", get_a0201_xml(num_b2b_inv_1, inv_date, inv_date, t3), "A0201.xsd"),
            ]
        },
        4: {
            "name": "Stage 4: Confirm B2B Cancel (A0202)",
            "files": [
                ("B2BEXCHANGE/A0202", f"A0202_{num_b2b_inv_1}.xml", get_a0202_xml(num_b2b_inv_1, inv_date, inv_date, t4), "A0202.xsd"),
            ]
        }
    }
    return stages

def write_and_validate_stage(stage_num, stage_info, out_base, validate=True):
    written = []
    print(f"\n=======================================================")
    print(f"[*] {stage_info['name']}")
    print(f"=======================================================")
    for rel_dir, fname, content, xsd_name in stage_info["files"]:
        target_dir = os.path.join(out_base, rel_dir)
        os.makedirs(target_dir, exist_ok=True)
        dst_path = os.path.join(target_dir, fname)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append((dst_path, rel_dir, fname, xsd_name))

    if validate:
        all_ok = True
        for dst_path, _, _, xsd_name in written:
            xsd_path = os.path.join(XSD_BASE_DIR, xsd_name)
            cmd = ["java", "-cp", VALIDATOR_CP, "XmlValidator", xsd_path, dst_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                print(f"  [XSD OK] {os.path.basename(dst_path)} -> {xsd_name}")
            else:
                print(f"  [XSD FAIL] {os.path.basename(dst_path)} -> {res.stderr.strip()}")
                all_ok = False
        if not all_ok:
            raise RuntimeError(f"Stage {stage_num} XSD validation failed!")
    return written

def deploy_stage(written_items):
    print(f"[+] Deploying {len(written_items)} files to Turnkey UpCast...")
    for src_path, rel_dir, fname, _ in written_items:
        # e.g. rel_dir is B2SSTORAGE/F0401
        target_src = os.path.join(TURNKEY_BASE, "UpCast", rel_dir, "SRC")
        os.makedirs(target_src, exist_ok=True)
        dst = os.path.join(target_src, fname)
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  -> Dispatched to {target_src}/{fname}")

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

def wait_for_stage_completion(identifiers, timeout_secs=120):
    """
    Polls database until all invoice/allowance identifiers reach final status ('G' or 'E').
    Returns True if all 'G', False if any 'E' or timeout.
    """
    print(f"[*] Awaiting transmission and platform acknowledgement for: {', '.join(identifiers)}...")
    start_time = time.time()
    while time.time() - start_time < timeout_secs:
        where_clauses = " OR ".join([f"invoice_identifier LIKE '%{ident}%'" for ident in identifiers])
        query = f"""
        SELECT message_type, invoice_identifier, status, message_dts
        FROM turnkey_message_log
        WHERE {where_clauses}
        ORDER BY message_dts DESC;
        """
        rows = query_psql(query)
        # Find latest status for each identifier
        status_map = {}
        for r in rows:
            if len(r) >= 3:
                mtype, full_ident, st = r[0], r[1], r[2]
                for ident in identifiers:
                    if ident in full_ident and ident not in status_map:
                        status_map[ident] = (mtype, st)

        pending = [ident for ident in identifiers if ident not in status_map or status_map[ident][1] in ("P", "C", "S")]
        if not pending and len(status_map) == len(identifiers):
            # All have finalized!
            all_g = all(st == "G" for _, st in status_map.values())
            for ident, (mtype, st) in status_map.items():
                print(f"  -> Result [{mtype}] {ident}: Status = {st}")
            return all_g

        time.sleep(5)

    print("[!] Timeout waiting for Turnkey transmission.")
    return False

def main():
    parser = argparse.ArgumentParser(description="MOF MIG 4.1 Test Dataset Generator & Orchestrator")
    parser.add_argument("--out", default="/invoice/EINVTurnkey/test_samples", help="Output directory for generated XMLs")
    parser.add_argument("--prefix", default="LP", help="2-character invoice track prefix (default: LP)")
    parser.add_argument("--start", type=int, default=50936600, help="Starting sequence number (default: 50936600)")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], help="Deploy specific stage only")
    parser.add_argument("--validate-only", action="store_true", help="Only generate and validate XSD schemas")
    parser.add_argument("--run-all", action="store_true", help="Run all 4 stages sequentially with status verification")
    args = parser.parse_args()

    stages = get_stage_definitions(args.prefix, args.start)

    if args.validate_only:
        print(f"=== Validating all stages for Track {args.prefix}{args.start} ===")
        for s_num in sorted(stages.keys()):
            write_and_validate_stage(s_num, stages[s_num], args.out, validate=True)
        print("\n[SUCCESS] All XMLs generated and verified valid according to official MIG 4.1 schemas!")
        return

    if args.stage:
        s_num = args.stage
        items = write_and_validate_stage(s_num, stages[s_num], args.out, validate=True)
        deploy_stage(items)
        print(f"\nStage {s_num} dispatched to Turnkey.")
        return

    if args.run_all:
        print(f"=== Starting Orchestrated 4-Stage Turnkey Test Execution ===")
        print(f"Track: {args.prefix} | Range Base: {args.start} | Entity: 00015555")

        for s_num in [1, 2, 3, 4]:
            stage_info = stages[s_num]
            items = write_and_validate_stage(s_num, stage_info, args.out, validate=True)
            deploy_stage(items)

            # Extract identifiers
            stage_idents = []
            for _, fname, _, _ in stage_info["files"]:
                ident = fname.replace(".xml", "").split("_", 1)[1]
                stage_idents.append(ident)

            success = wait_for_stage_completion(stage_idents, timeout_secs=120)
            if not success:
                print(f"\n[!] Stage {s_num} encountered errors or unconfirmed messages. Check einv_status.py.")
                sys.exit(1)
            print(f"\n[+] Stage {s_num} completed successfully with ALL GREEN (Status G) confirmations!")
            time.sleep(5)

        print("\n=========================================================================")
        print(" [ALL STAGES COMPLETED SUCCESSFULLY] All test invoices/allowances passed!")
        print("=========================================================================")

if __name__ == "__main__":
    main()
