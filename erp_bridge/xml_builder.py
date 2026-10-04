#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIG 4.1 XML Generator for Taiwan Electronic Invoices.
Builds compliant XML strings for:
- F0401 (B2C / B2S Storage Invoice Issue)
- F0501 (B2C / B2S Storage Invoice Cancel)
- A0101 (B2B Exchange Invoice Issue)
- A0201 (B2B Exchange Invoice Cancel)
"""

import html
import math
from datetime import datetime
from .config import (
    COMPANY_SELLER_BAN,
    COMPANY_SELLER_NAME,
    COMPANY_SELLER_ADDR
)

def escape_xml(val) -> str:
    """Safely escapes XML special characters."""
    if val is None:
        return ""
    return html.escape(str(val).strip(), quote=True)

def resolve_item_description(item: dict) -> str:
    """
    Resolves product description following priority:
    1. products.invoice_name (preferred official e-invoice name)
    2. products.chinese_name
    3. products.name
    4. order_items.custom_name
    5. order_items.product_sku
    """
    desc = (
        item.get("invoice_name")
        or item.get("chinese_name")
        or item.get("name")
        or item.get("custom_name")
        or item.get("product_sku")
        or "商品"
    )
    # MIG 4.1 description max length is 500
    return escape_xml(desc[:250])

def build_f0401_xml(order: dict, items: list[dict]) -> str:
    """
    Builds MIG 4.1 F0401 B2C / Storage Invoice XML.
    """
    inv_number = order["einv_number"]
    inv_date = order.get("einv_date") or datetime.now().strftime("%Y%m%d")
    inv_time = order.get("einv_time") or datetime.now().strftime("%H:%M:%S")
    random_num = order.get("einv_random_number", "0000")

    seller_ban = escape_xml(order.get("seller_ban") or COMPANY_SELLER_BAN)
    seller_name = escape_xml(order.get("seller_name") or COMPANY_SELLER_NAME)
    seller_addr = escape_xml(order.get("seller_addr") or COMPANY_SELLER_ADDR)

    buyer_ban = escape_xml(order.get("buyer_ban") or "0000000000")
    buyer_name = escape_xml(order.get("buyer_name") or order.get("buyer_username") or "個人消費者")

    carrier_type = order.get("carrier_type")
    carrier_id = order.get("carrier_id")
    donate_mark = str(order.get("donate_mark", "0"))
    love_code = order.get("love_code")
    print_mark = order.get("print_mark", "Y")

    # If carrier or donation is specified, PrintMark is typically 'N'
    if carrier_type and carrier_id:
        print_mark = "N"
        donate_mark = "0"
        carrier_xml = f"""
        <CarrierType>{escape_xml(carrier_type)}</CarrierType>
        <CarrierId1>{escape_xml(carrier_id)}</CarrierId1>
        <CarrierId2>{escape_xml(carrier_id)}</CarrierId2>"""
        npoban_xml = ""
    elif donate_mark == "1" and love_code:
        print_mark = "N"
        carrier_xml = ""
        npoban_xml = f"""
        <NPOBAN>{escape_xml(love_code)}</NPOBAN>"""
    else:
        print_mark = "Y"
        carrier_xml = ""
        npoban_xml = ""

    # Calculate item details & amounts
    details_xml_list = []
    total_amount = 0
    seq = 1

    for item in items:
        qty = int(item.get("quantity", 1))
        unit_price = int(item.get("unit_price", 0))
        line_total = int(item.get("line_total", qty * unit_price))
        total_amount += line_total

        desc = resolve_item_description(item)
        details_xml_list.append(f"""        <ProductItem>
            <Description>{desc}</Description>
            <Quantity>{qty}</Quantity>
            <UnitPrice>{unit_price}</UnitPrice>
            <Amount>{line_total}</Amount>
            <SequenceNumber>{seq:03d}</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>""")
        seq += 1

    # In case items list was empty, avoid generating invalid XML
    if not details_xml_list:
        total_amount = int(order.get("total_amount", 100))
        details_xml_list.append(f"""        <ProductItem>
            <Description>商品</Description>
            <Quantity>1</Quantity>
            <UnitPrice>{total_amount}</UnitPrice>
            <Amount>{total_amount}</Amount>
            <SequenceNumber>001</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>""")

    # Taiwan 5% VAT: TotalAmount = SalesAmount + TaxAmount
    # SalesAmount = round(TotalAmount / 1.05)
    sales_amount = round(total_amount / 1.05)
    tax_amount = total_amount - sales_amount

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:GEINV:eInvoiceMessage:F0401:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Main>
        <InvoiceNumber>{inv_number}</InvoiceNumber>
        <InvoiceDate>{inv_date}</InvoiceDate>
        <InvoiceTime>{inv_time}</InvoiceTime>
        <Seller>
            <Identifier>{seller_ban}</Identifier>
            <Name>{seller_name}</Name>
            <Address>{seller_addr}</Address>
        </Seller>
        <Buyer>
            <Identifier>{buyer_ban}</Identifier>
            <Name>{buyer_name}</Name>
        </Buyer>
        <InvoiceType>07</InvoiceType>
        <DonateMark>{donate_mark}</DonateMark>{carrier_xml}
        <PrintMark>{print_mark}</PrintMark>{npoban_xml}
        <RandomNumber>{random_num}</RandomNumber>
    </Main>
    <Details>
{chr(10).join(details_xml_list)}
    </Details>
    <Amount>
        <SalesAmount>{sales_amount}</SalesAmount>
        <FreeTaxSalesAmount>0</FreeTaxSalesAmount>
        <ZeroTaxSalesAmount>0</ZeroTaxSalesAmount>
        <TaxType>1</TaxType>
        <TaxRate>0.05</TaxRate>
        <TaxAmount>{tax_amount}</TaxAmount>
        <TotalAmount>{total_amount}</TotalAmount>
    </Amount>
</Invoice>
"""
    return xml.strip()

def build_f0501_xml(order: dict) -> str:
    """
    Builds MIG 4.1 F0501 B2C / Storage Invoice Cancellation XML.
    """
    cancel_inv_num = order["einv_number"]
    inv_date = order.get("einv_date") or datetime.now().strftime("%Y%m%d")
    cancel_date = order.get("einv_cancel_date") or datetime.now().strftime("%Y%m%d")
    cancel_time = order.get("einv_cancel_time") or datetime.now().strftime("%H:%M:%S")
    reason = escape_xml((order.get("einv_cancel_reason") or "訂單取消退貨作廢")[:20])

    seller_ban = escape_xml(order.get("seller_ban") or COMPANY_SELLER_BAN)
    buyer_ban = escape_xml(order.get("buyer_ban") or "0000000000")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoice xmlns="urn:GEINV:eInvoiceMessage:F0501:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{buyer_ban}</BuyerId>
    <SellerId>{seller_ban}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelInvoice>
"""
    return xml.strip()

def build_a0101_xml(order: dict, items: list[dict]) -> str:
    """
    Builds MIG 4.1 A0101 B2B Exchange Invoice XML.
    """
    inv_number = order["einv_number"]
    inv_date = order.get("einv_date") or datetime.now().strftime("%Y%m%d")
    inv_time = order.get("einv_time") or datetime.now().strftime("%H:%M:%S")

    seller_ban = escape_xml(order.get("seller_ban") or COMPANY_SELLER_BAN)
    seller_name = escape_xml(order.get("seller_name") or COMPANY_SELLER_NAME)
    seller_addr = escape_xml(order.get("seller_addr") or COMPANY_SELLER_ADDR)

    buyer_ban = escape_xml(order.get("buyer_ban"))
    buyer_name = escape_xml(order.get("buyer_name") or order.get("buyer_username") or "營業人買受方")

    details_xml_list = []
    sales_amount = 0
    seq = 1

    for item in items:
        qty = int(item.get("quantity", 1))
        unit_price = int(item.get("unit_price", 0))
        line_amount = int(item.get("line_total", qty * unit_price))
        sales_amount += line_amount

        desc = resolve_item_description(item)
        details_xml_list.append(f"""        <ProductItem>
            <Description>{desc}</Description>
            <Quantity>{qty}</Quantity>
            <UnitPrice>{unit_price}</UnitPrice>
            <Amount>{line_amount}</Amount>
            <SequenceNumber>{seq:03d}</SequenceNumber>
            <TaxType>1</TaxType>
        </ProductItem>""")
        seq += 1

    tax_amount = round(sales_amount * 0.05)
    total_amount = sales_amount + tax_amount

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:GEINV:eInvoiceMessage:A0101:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Main>
        <InvoiceNumber>{inv_number}</InvoiceNumber>
        <InvoiceDate>{inv_date}</InvoiceDate>
        <InvoiceTime>{inv_time}</InvoiceTime>
        <Seller>
            <Identifier>{seller_ban}</Identifier>
            <Name>{seller_name}</Name>
            <Address>{seller_addr}</Address>
        </Seller>
        <Buyer>
            <Identifier>{buyer_ban}</Identifier>
            <Name>{buyer_name}</Name>
        </Buyer>
        <InvoiceType>07</InvoiceType>
        <DonateMark>0</DonateMark>
    </Main>
    <Details>
{chr(10).join(details_xml_list)}
    </Details>
    <Amount>
        <SalesAmount>{sales_amount}</SalesAmount>
        <TaxType>1</TaxType>
        <TaxRate>0.05</TaxRate>
        <TaxAmount>{tax_amount}</TaxAmount>
        <TotalAmount>{total_amount}</TotalAmount>
    </Amount>
</Invoice>
"""
    return xml.strip()

def build_a0201_xml(order: dict) -> str:
    """
    Builds MIG 4.1 A0201 B2B Exchange Invoice Cancellation XML.
    """
    cancel_inv_num = order["einv_number"]
    inv_date = order.get("einv_date") or datetime.now().strftime("%Y%m%d")
    cancel_date = order.get("einv_cancel_date") or datetime.now().strftime("%Y%m%d")
    cancel_time = order.get("einv_cancel_time") or datetime.now().strftime("%H:%M:%S")
    reason = escape_xml((order.get("einv_cancel_reason") or "訂單取消退貨作廢")[:20])

    seller_ban = escape_xml(order.get("seller_ban") or COMPANY_SELLER_BAN)
    buyer_ban = escape_xml(order.get("buyer_ban"))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CancelInvoice xmlns="urn:GEINV:eInvoiceMessage:A0201:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <CancelInvoiceNumber>{cancel_inv_num}</CancelInvoiceNumber>
    <InvoiceDate>{inv_date}</InvoiceDate>
    <BuyerId>{buyer_ban}</BuyerId>
    <SellerId>{seller_ban}</SellerId>
    <CancelDate>{cancel_date}</CancelDate>
    <CancelTime>{cancel_time}</CancelTime>
    <CancelReason>{reason}</CancelReason>
</CancelInvoice>
"""
    return xml.strip()
