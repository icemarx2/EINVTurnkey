#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase REST API Client for e-Invoice Integration.
Uses HTTP requests to communicate with Supabase PostgREST endpoints.
"""

import time
import requests
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    EINV_TRIGGER_INTERNAL_STATUSES,
    CURRENT_YEAR_MONTH
)

class SupabaseClient:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.key = key or SUPABASE_SERVICE_ROLE_KEY
        self.session = requests.Session()
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation"
        }
        self.session.headers.update(self.headers)
        self._product_cache: Dict[str, Dict[str, Any]] = {}
        self._product_cache_time = 0.0

    def is_configured(self) -> bool:
        """Returns True if Supabase URL and key are provided."""
        return bool(self.url and self.key and not self.url.startswith("https://your-project"))

    def _ensure_product_cache(self, force: bool = False):
        """Caches product SKU -> invoice_name/chinese_name/name mappings."""
        now = time.time()
        # Refresh every 300 seconds (5 minutes)
        if not force and self._product_cache and (now - self._product_cache_time < 300):
            return

        if not self.is_configured():
            return

        endpoint = f"{self.url}/rest/v1/products?select=sku,invoice_name,chinese_name,name"
        try:
            resp = self.session.get(endpoint, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._product_cache = {p["sku"]: p for p in data if "sku" in p}
                self._product_cache_time = now
        except Exception as e:
            # Fallback gracefully
            pass

    def allocate_next_invoice_number(self, period: Optional[str] = None) -> Dict[str, str]:
        """
        Calls the atomic Supabase RPC function allocate_next_invoice_number(p_year_month).
        Returns: {'invoice_number': 'LP50936605', 'random_number': '1234', 'year_month': '11510'}
        """
        period = period or CURRENT_YEAR_MONTH
        endpoint = f"{self.url}/rest/v1/rpc/allocate_next_invoice_number"
        payload = {"p_year_month": period}

        resp = self.session.post(endpoint, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to allocate invoice number from Supabase: {resp.status_code} - {resp.text}")
        return resp.json()

    def get_pending_issuance_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches orders ready for invoice issuance:
        einv_status is PENDING, and internal_status is in EINV_TRIGGER_INTERNAL_STATUSES.
        """
        if not self.is_configured():
            return []

        self._ensure_product_cache()

        status_filter = ",".join(EINV_TRIGGER_INTERNAL_STATUSES)
        # PostgREST query: filter by einv_status and internal_status, embed order_items
        endpoint = (
            f"{self.url}/rest/v1/orders"
            f"?einv_status=eq.PENDING"
            f"&internal_status=in.({status_filter})"
            f"&select=*,order_items(*)"
            f"&order=id.asc"
            f"&limit={limit}"
        )

        resp = self.session.get(endpoint, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Error fetching pending orders from Supabase: {resp.status_code} - {resp.text}")

        orders = resp.json()

        # Augment item records with product invoice_name
        for order in orders:
            for item in order.get("order_items", []):
                sku = item.get("product_sku")
                if sku and sku in self._product_cache:
                    prod = self._product_cache[sku]
                    item["invoice_name"] = prod.get("invoice_name")
                    item["chinese_name"] = prod.get("chinese_name")
                    item["name"] = prod.get("name")

        return orders

    def get_pending_cancellation_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches orders requiring cancellation:
        1. einv_status = 'CANCEL_PENDING', OR
        2. internal_status = 'cancelled' AND einv_status = 'SUCCESS' AND einv_number IS NOT NULL.
        """
        if not self.is_configured():
            return []

        endpoint = (
            f"{self.url}/rest/v1/orders"
            f"?or=(einv_status.eq.CANCEL_PENDING,and(internal_status.eq.cancelled,einv_status.eq.SUCCESS))"
            f"&einv_number=not.is.null"
            f"&select=*"
            f"&limit={limit}"
        )

        resp = self.session.get(endpoint, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Error fetching cancellation orders from Supabase: {resp.status_code} - {resp.text}")

        return resp.json()

    def update_order_dispatched(
        self,
        order_id: int,
        invoice_number: str,
        random_number: str,
        invoice_date: str,
        invoice_time: str,
        msg_type: str = "F0401"
    ) -> bool:
        """Updates order record after dispatching XML to Turnkey UpCast."""
        endpoint = f"{self.url}/rest/v1/orders?id=eq.{order_id}"
        payload = {
            "einv_number": invoice_number,
            "einv_random_number": random_number,
            "einv_date": invoice_date,
            "einv_time": invoice_time,
            "einv_msg_type": msg_type,
            "einv_status": "DISPATCHED",
            "einv_dispatched_at": datetime.now(timezone.utc).isoformat()
        }

        resp = self.session.patch(endpoint, json=payload, timeout=10)
        return resp.status_code in (200, 204)

    def update_order_cancel_dispatched(
        self,
        order_id: int,
        cancel_date: str,
        cancel_time: str,
        reason: str
    ) -> bool:
        """Updates order record after dispatching cancellation XML to Turnkey."""
        endpoint = f"{self.url}/rest/v1/orders?id=eq.{order_id}"
        payload = {
            "einv_status": "CANCEL_DISPATCHED",
            "einv_cancel_date": cancel_date,
            "einv_cancel_time": cancel_time,
            "einv_cancel_reason": reason
        }

        resp = self.session.patch(endpoint, json=payload, timeout=10)
        return resp.status_code in (200, 204)

    def update_order_status(
        self,
        invoice_number: str,
        status: str,
        result_code: str,
        result_desc: Optional[str] = None,
        uuid: Optional[str] = None
    ) -> bool:
        """Updates order issuance completion status (SUCCESS / FAILED)."""
        endpoint = f"{self.url}/rest/v1/orders?einv_number=eq.{invoice_number}"
        payload = {
            "einv_status": status,
            "einv_result_code": result_code
        }
        if status == "SUCCESS":
            payload["einv_completed_at"] = datetime.now(timezone.utc).isoformat()
        if result_desc:
            payload["einv_result_desc"] = result_desc
        if uuid:
            payload["einv_turnkey_uuid"] = uuid

        resp = self.session.patch(endpoint, json=payload, timeout=10)
        return resp.status_code in (200, 204)

    def update_order_cancelled_status(
        self,
        invoice_number: str,
        status: str,
        result_code: str,
        uuid: Optional[str] = None
    ) -> bool:
        """Updates order cancellation completion status (CANCELLED / CANCEL_FAILED)."""
        endpoint = f"{self.url}/rest/v1/orders?einv_number=eq.{invoice_number}"
        payload = {
            "einv_status": status,
            "einv_cancel_result_code": result_code
        }
        if status == "CANCELLED":
            payload["einv_cancel_completed_at"] = datetime.now(timezone.utc).isoformat()
        if uuid:
            payload["einv_turnkey_uuid"] = uuid

        resp = self.session.patch(endpoint, json=payload, timeout=10)
        return resp.status_code in (200, 204)

    def add_track_quota(
        self,
        year_month: str,
        track_prefix: str,
        start_no: int,
        end_no: int
    ) -> Dict[str, Any]:
        """Inserts a new bimonthly track quota row into einv_track_quota."""
        endpoint = f"{self.url}/rest/v1/einv_track_quota"
        payload = {
            "year_month": year_month,
            "track_prefix": track_prefix.upper(),
            "start_no": int(start_no),
            "end_no": int(end_no),
            "current_no": int(start_no),
            "is_active": True
        }

        resp = self.session.post(endpoint, json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to add track quota: {resp.status_code} - {resp.text}")
        return resp.json()
