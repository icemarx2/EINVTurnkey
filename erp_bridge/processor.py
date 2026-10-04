#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Processor for Turnkey-ERP Bridge.
Orchestrates:
1. Pending Order Invoicing (Fetch -> Allocate -> Build XML -> Validate -> Dispatch -> Patch)
2. Pending Order Cancellation (Fetch -> Build Cancel XML -> Validate -> Dispatch -> Patch)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from .config import CURRENT_YEAR_MONTH
from .supabase_client import SupabaseClient
from .xml_builder import build_f0401_xml, build_f0501_xml, build_a0101_xml, build_a0201_xml
from .validator import validate_xml
from .dispatcher import dispatch_xml

logger = logging.getLogger("erp_bridge")

class BridgeProcessor:
    def __init__(self, sb_client: SupabaseClient):
        self.sb = sb_client

    def process_invoices_once(self) -> Dict[str, int]:
        """
        Polls and processes all pending orders ready for invoice issuance.
        """
        stats = {"processed": 0, "dispatched": 0, "failed": 0, "skipped": 0}
        orders = self.sb.get_pending_issuance_orders(limit=50)

        if not orders:
            return stats

        now = datetime.now()
        inv_date = now.strftime("%Y%m%d")
        inv_time = now.strftime("%H:%M:%S")

        for order in orders:
            order_id = order.get("id")
            order_num = order.get("shopee_order_number") or str(order_id)
            stats["processed"] += 1

            try:
                # 1. Allocate invoice number & random number if not already present
                inv_no = order.get("einv_number")
                rand_no = order.get("einv_random_number")

                if not inv_no:
                    alloc_res = self.sb.allocate_next_invoice_number(CURRENT_YEAR_MONTH)
                    inv_no = alloc_res["invoice_number"]
                    rand_no = alloc_res.get("random_number", "0000")

                order["einv_number"] = inv_no
                order["einv_random_number"] = rand_no
                order["einv_date"] = inv_date
                order["einv_time"] = inv_time

                items = order.get("order_items", [])

                # 2. Determine Message Type (F0401 vs A0101)
                buyer_ban = (order.get("buyer_ban") or "").strip()
                is_b2b = bool(buyer_ban and buyer_ban != "0000000000" and len(buyer_ban) == 8)
                msg_type = "A0101" if (is_b2b and order.get("einv_msg_type") == "A0101") else "F0401"
                category = "B2BEXCHANGE" if msg_type == "A0101" else "B2SSTORAGE"

                # 3. Build XML
                if msg_type == "A0101":
                    xml_content = build_a0101_xml(order, items)
                else:
                    xml_content = build_f0401_xml(order, items)

                # 4. In-Memory XSD Schema Pre-Validation
                is_valid, err_msg = validate_xml(msg_type, xml_content)
                if not is_valid:
                    logger.error(f"[XSD ERROR] Order {order_num} ({inv_no}) invalid: {err_msg}")
                    self.sb.update_order_status(
                        invoice_number=inv_no,
                        status="FAILED",
                        result_code="XSD_ERR",
                        result_desc=f"XML Schema Validation Failed: {err_msg[:200]}"
                    )
                    stats["failed"] += 1
                    continue

                # 5. Atomic Dispatch to Turnkey UpCast
                filename = f"{msg_type}_{inv_no}"
                dispatched_path = dispatch_xml(category, msg_type, filename, xml_content)
                logger.info(f"[DISPATCH OK] Order {order_num} -> {inv_no} dropped to {dispatched_path}")

                # 6. Update Supabase Order to DISPATCHED
                self.sb.update_order_dispatched(
                    order_id=order_id,
                    invoice_number=inv_no,
                    random_number=rand_no,
                    invoice_date=inv_date,
                    invoice_time=inv_time,
                    msg_type=msg_type
                )
                stats["dispatched"] += 1

            except Exception as e:
                logger.error(f"[ERROR] Failed processing order {order_num}: {e}", exc_info=True)
                stats["failed"] += 1

        return stats

    def process_cancellations_once(self) -> Dict[str, int]:
        """
        Polls and processes all orders requiring electronic invoice cancellation.
        """
        stats = {"cancelled": 0, "failed": 0, "skipped": 0}
        orders = self.sb.get_pending_cancellation_orders(limit=50)

        if not orders:
            return stats

        now = datetime.now()
        cancel_date = now.strftime("%Y%m%d")
        cancel_time = now.strftime("%H:%M:%S")

        for order in orders:
            order_id = order.get("id")
            order_num = order.get("shopee_order_number") or str(order_id)
            inv_no = order.get("einv_number")

            if not inv_no:
                stats["skipped"] += 1
                continue

            try:
                order["einv_cancel_date"] = order.get("einv_cancel_date") or cancel_date
                order["einv_cancel_time"] = order.get("einv_cancel_time") or cancel_time
                reason = order.get("einv_cancel_reason") or "訂單取消退貨作廢"
                order["einv_cancel_reason"] = reason

                # Determine cancellation message type
                orig_msg_type = order.get("einv_msg_type", "F0401")
                if orig_msg_type == "A0101":
                    cancel_msg_type = "A0201"
                    category = "B2BEXCHANGE"
                    xml_content = build_a0201_xml(order)
                else:
                    cancel_msg_type = "F0501"
                    category = "B2SSTORAGE"
                    xml_content = build_f0501_xml(order)

                # Validate cancel XML against schema
                is_valid, err_msg = validate_xml(cancel_msg_type, xml_content)
                if not is_valid:
                    logger.error(f"[CANCEL XSD ERROR] Order {order_num} ({inv_no}): {err_msg}")
                    stats["failed"] += 1
                    continue

                # Atomic dispatch
                filename = f"{cancel_msg_type}_{inv_no}"
                dispatched_path = dispatch_xml(category, cancel_msg_type, filename, xml_content)
                logger.info(f"[CANCEL DISPATCH OK] Order {order_num} ({inv_no}) cancel dropped to {dispatched_path}")

                # Update Supabase status
                self.sb.update_order_cancel_dispatched(
                    order_id=order_id,
                    cancel_date=order["einv_cancel_date"],
                    cancel_time=order["einv_cancel_time"],
                    reason=reason
                )
                stats["cancelled"] += 1

            except Exception as e:
                logger.error(f"[CANCEL ERROR] Failed cancelling invoice for order {order_num}: {e}", exc_info=True)
                stats["failed"] += 1

        return stats
