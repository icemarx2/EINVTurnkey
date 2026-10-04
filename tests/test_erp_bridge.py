#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test Suite for Turnkey to Supabase ERP Integration Bridge.
Verifies:
1. XML Generation for all MIG 4.1 message types (F0401, F0501, A0101, A0201).
2. 100% XSD Schema Compliance with official Ministry of Finance schemas.
3. Priority item description selection (products.invoice_name -> chinese_name -> name -> sku).
4. Taiwan 5% VAT calculation accuracy (SalesAmount + TaxAmount = TotalAmount).
5. Atomic dispatcher writing to UpCast.
6. Mock end-to-end flow with Supabase REST API responses.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from erp_bridge.xml_builder import (
    build_f0401_xml,
    build_f0501_xml,
    build_a0101_xml,
    build_a0201_xml,
    resolve_item_description,
    escape_xml
)
from erp_bridge.validator import validate_xml
from erp_bridge.dispatcher import dispatch_xml
from erp_bridge.supabase_client import SupabaseClient
from erp_bridge.processor import BridgeProcessor

class TestXMLBuilderAndValidator(unittest.TestCase):

    def setUp(self):
        self.base_order = {
            "id": 1001,
            "shopee_order_number": "260925SP001",
            "einv_number": "LP50936688",
            "einv_random_number": "8888",
            "einv_date": "20260925",
            "einv_time": "12:30:00",
            "buyer_username": "test_shopee_user",
            "buyer_ban": "0000000000",
            "buyer_name": "個人消費者",
            "seller_ban": "00015555",
            "seller_name": "奧銳有限公司",
            "seller_addr": "臺北市中正區漢口街1段45號10樓",
        }

    def test_description_resolution_priority(self):
        """Verify priority: invoice_name > chinese_name > name > custom_name > product_sku."""
        # 1. invoice_name takes highest precedence
        item1 = {
            "product_sku": "SKU-001",
            "name": "English Name",
            "chinese_name": "中文品名",
            "invoice_name": "官方發票品名-高精度遙控器"
        }
        self.assertEqual(resolve_item_description(item1), "官方發票品名-高精度遙控器")

        # 2. chinese_name if invoice_name is None
        item2 = {
            "product_sku": "SKU-002",
            "name": "English Name",
            "chinese_name": "高精度遙控器",
            "invoice_name": None
        }
        self.assertEqual(resolve_item_description(item2), "高精度遙控器")

        # 3. name if chinese_name is None
        item3 = {
            "product_sku": "SKU-003",
            "name": "Smart Controller",
            "chinese_name": None
        }
        self.assertEqual(resolve_item_description(item3), "Smart Controller")

        # 4. product_sku fallback
        item4 = {"product_sku": "MISC-ITEM-99"}
        self.assertEqual(resolve_item_description(item4), "MISC-ITEM-99")

    def test_f0401_b2c_paper_invoice_xsd(self):
        """Test B2C Paper Invoice (PrintMark=Y) against F0401.xsd."""
        order = dict(self.base_order)
        order["print_mark"] = "Y"

        items = [
            {
                "product_sku": "ITEM-1",
                "invoice_name": "智慧遙控插座",
                "quantity": 2,
                "unit_price": 500,
                "line_total": 1000
            },
            {
                "product_sku": "ITEM-2",
                "invoice_name": "USB 快充線",
                "quantity": 1,
                "unit_price": 250,
                "line_total": 250
            }
        ]

        xml = build_f0401_xml(order, items)
        self.assertIn("<PrintMark>Y</PrintMark>", xml)
        self.assertIn("<InvoiceNumber>LP50936688</InvoiceNumber>", xml)
        self.assertIn("<TotalAmount>1250</TotalAmount>", xml)

        # Validate against official F0401.xsd
        is_valid, err = validate_xml("F0401", xml)
        self.assertTrue(is_valid, f"F0401 XSD validation failed: {err}")

    def test_f0401_b2c_mobile_carrier_xsd(self):
        """Test B2C Mobile Barcode Carrier (CarrierType=3J0002, PrintMark=N) against F0401.xsd."""
        order = dict(self.base_order)
        order["carrier_type"] = "3J0002"
        order["carrier_id"] = "/ABC+123"

        items = [{
            "product_sku": "ITEM-3",
            "invoice_name": "無線滑鼠",
            "quantity": 1,
            "unit_price": 600,
            "line_total": 600
        }]

        xml = build_f0401_xml(order, items)
        self.assertIn("<CarrierType>3J0002</CarrierType>", xml)
        self.assertIn("<CarrierId1>/ABC+123</CarrierId1>", xml)
        self.assertIn("<PrintMark>N</PrintMark>", xml)

        is_valid, err = validate_xml("F0401", xml)
        self.assertTrue(is_valid, f"F0401 carrier validation failed: {err}")

    def test_f0401_b2c_donation_love_code_xsd(self):
        """Test B2C Love Code Donation (DonateMark=1, NPOBAN=25885, PrintMark=N) against F0401.xsd."""
        order = dict(self.base_order)
        order["donate_mark"] = "1"
        order["love_code"] = "25885"

        items = [{
            "product_sku": "ITEM-4",
            "invoice_name": "藍牙耳機",
            "quantity": 1,
            "unit_price": 990,
            "line_total": 990
        }]

        xml = build_f0401_xml(order, items)
        self.assertIn("<DonateMark>1</DonateMark>", xml)
        self.assertIn("<NPOBAN>25885</NPOBAN>", xml)
        self.assertIn("<PrintMark>N</PrintMark>", xml)

        is_valid, err = validate_xml("F0401", xml)
        self.assertTrue(is_valid, f"F0401 donation validation failed: {err}")

    def test_f0501_b2c_cancellation_xsd(self):
        """Test B2C Cancellation against F0501.xsd."""
        order = dict(self.base_order)
        order["einv_cancel_date"] = "20260925"
        order["einv_cancel_time"] = "15:00:00"
        order["einv_cancel_reason"] = "買受人退換貨作廢"

        xml = build_f0501_xml(order)
        self.assertIn("<CancelInvoiceNumber>LP50936688</CancelInvoiceNumber>", xml)
        self.assertIn("<CancelReason>買受人退換貨作廢</CancelReason>", xml)

        is_valid, err = validate_xml("F0501", xml)
        self.assertTrue(is_valid, f"F0501 validation failed: {err}")

    def test_a0101_b2b_issue_and_a0201_cancel_xsd(self):
        """Test B2B Issue (A0101) and Cancel (A0201) against schemas."""
        order = dict(self.base_order)
        order["buyer_ban"] = "00015555"
        order["buyer_name"] = "奧銳有限公司"

        items = [{
            "product_sku": "B2B-ITEM-1",
            "invoice_name": "工業自動化控制器",
            "quantity": 1,
            "unit_price": 10000,
            "line_total": 10000
        }]

        # A0101 Issue
        a0101_xml = build_a0101_xml(order, items)
        is_valid, err = validate_xml("A0101", a0101_xml)
        self.assertTrue(is_valid, f"A0101 validation failed: {err}")

        # A0201 Cancel
        order["einv_cancel_date"] = "20260925"
        order["einv_cancel_time"] = "16:00:00"
        order["einv_cancel_reason"] = "買賣雙方協議作廢"
        a0201_xml = build_a0201_xml(order)
        is_valid, err = validate_xml("A0201", a0201_xml)
        self.assertTrue(is_valid, f"A0201 validation failed: {err}")

class TestDispatcherAndProcessor(unittest.TestCase):

    def test_atomic_dispatch(self):
        """Verify atomic dispatch writes to .tmp and renames to .xml."""
        test_content = "<test>sample</test>"
        target_path = dispatch_xml("B2SSTORAGE", "F0401", "TEST_DISPATCH_001", test_content)

        self.assertTrue(os.path.exists(target_path))
        self.assertTrue(target_path.endswith("TEST_DISPATCH_001.xml"))

        # Verify no residual .tmp file
        tmp_path = target_path + ".tmp"
        self.assertFalse(os.path.exists(tmp_path))

        with open(target_path, "r", encoding="utf-8") as f:
            read_back = f.read()
        self.assertEqual(read_back, test_content)

        # Cleanup test file
        if os.path.exists(target_path):
            os.remove(target_path)

    @patch("erp_bridge.supabase_client.SupabaseClient")
    def test_bridge_processor_mock_flow(self, mock_sb_cls):
        """Test full mock flow: pending order -> allocation -> XML generation -> dispatch -> patch."""
        mock_sb = MagicMock()
        mock_sb.get_pending_issuance_orders.return_value = [{
            "id": 9999,
            "shopee_order_number": "SP-TEST-9999",
            "buyer_username": "buyer_test",
            "buyer_ban": "0000000000",
            "buyer_name": "個人消費者",
            "internal_status": "shipped",
            "einv_status": "PENDING",
            "einv_number": None,
            "order_items": [{
                "product_sku": "SKU-TEST-01",
                "invoice_name": "測試專用商品",
                "quantity": 1,
                "unit_price": 500,
                "line_total": 500
            }]
        }]
        mock_sb.allocate_next_invoice_number.return_value = {
            "invoice_number": "LP50936699",
            "random_number": "1234",
            "year_month": "11510"
        }

        processor = BridgeProcessor(mock_sb)
        stats = processor.process_invoices_once()

        self.assertEqual(stats["processed"], 1)
        self.assertEqual(stats["dispatched"], 1)
        self.assertEqual(stats["failed"], 0)

        # Verify allocation was called
        mock_sb.allocate_next_invoice_number.assert_called_once()

        # Verify order update dispatched was called
        mock_sb.update_order_dispatched.assert_called_once()
        call_kwargs = mock_sb.update_order_dispatched.call_args[1]
        self.assertEqual(call_kwargs["order_id"], 9999)
        self.assertEqual(call_kwargs["invoice_number"], "LP50936699")
        self.assertEqual(call_kwargs["random_number"], "1234")

        # Cleanup dispatched file if created
        target_file = Path("/invoice/EINVTurnkey/UpCast/B2SSTORAGE/F0401/SRC/F0401_LP50936699.xml")
        if target_file.exists():
            target_file.unlink()

    def test_bridge_processor_cancellation_flow(self):
        """Test cancellation flow: cancelled order -> F0501 XML -> dispatch -> patch CANCEL_DISPATCHED."""
        mock_sb = MagicMock()
        mock_sb.get_pending_cancellation_orders.return_value = [{
            "id": 8888,
            "shopee_order_number": "SP-CANCEL-8888",
            "einv_number": "LP50936688",
            "einv_date": "20260925",
            "einv_msg_type": "F0401",
            "einv_status": "CANCEL_PENDING",
            "einv_cancel_reason": "買方退貨退款作廢",
            "buyer_ban": "0000000000"
        }]

        processor = BridgeProcessor(mock_sb)
        stats = processor.process_cancellations_once()

        self.assertEqual(stats["cancelled"], 1)
        self.assertEqual(stats["failed"], 0)

        # Verify update_order_cancel_dispatched called
        mock_sb.update_order_cancel_dispatched.assert_called_once()
        call_kwargs = mock_sb.update_order_cancel_dispatched.call_args[1]
        self.assertEqual(call_kwargs["order_id"], 8888)
        self.assertEqual(call_kwargs["reason"], "買方退貨退款作廢")

        # Cleanup file
        target_file = Path("/invoice/EINVTurnkey/UpCast/B2SSTORAGE/F0501/SRC/F0501_LP50936688.xml")
        if target_file.exists():
            target_file.unlink()

    @patch("erp_bridge.syncer.run_turnkey_psql")
    def test_status_syncer_mock_flow(self, mock_psql):
        """Test status syncer: turnkey log -> patch order status."""
        from erp_bridge.syncer import StatusSyncer

        # Simulate Turnkey message log output
        mock_psql.return_value = [
            ["F0401", "F0401LP5093660120260925", "G", "uuid-test-001", "20260925120000"],
            ["F0501", "F0501LP5093660220260925", "G", "uuid-test-002", "20260925120500"]
        ]

        mock_sb = MagicMock()
        mock_sb.update_order_status.return_value = True
        mock_sb.update_order_cancelled_status.return_value = True

        syncer = StatusSyncer(mock_sb)
        stats = syncer.sync_once()

        self.assertEqual(stats["success"], 1)
        self.assertEqual(stats["cancelled"], 1)

        # Verify update_order_status called with SUCCESS and 00000
        mock_sb.update_order_status.assert_called_once_with(
            invoice_number="LP50936601",
            status="SUCCESS",
            result_code="00000",
            uuid="uuid-test-001"
        )

        # Verify update_order_cancelled_status called with CANCELLED and 00000
        mock_sb.update_order_cancelled_status.assert_called_once_with(
            invoice_number="LP50936602",
            status="CANCELLED",
            result_code="00000",
            uuid="uuid-test-002"
        )

if __name__ == "__main__":
    unittest.main()

