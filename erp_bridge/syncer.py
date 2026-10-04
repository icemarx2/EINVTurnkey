#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status Synchronizer: Turnkey Message Log -> Supabase ERP Orders.
Queries Turnkey's PostgreSQL message logs and updates Supabase orders with MOF result codes.
"""

import re
import sys
import subprocess
from typing import Dict, List, Tuple
from .config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
from .supabase_client import SupabaseClient

def run_turnkey_psql(query: str) -> List[List[str]]:
    """Runs a query against Turnkey's local PostgreSQL database."""
    cmd = [
        "psql", "-U", PG_USER, "-h", PG_HOST, "-p", PG_PORT, "-d", PG_DATABASE,
        "-t", "-A", "-F", "\t", "-c", query
    ]
    env = {"PGPASSWORD": PG_PASSWORD, "PATH": "/usr/local/bin:/usr/bin:/bin"}
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if res.returncode != 0:
            return []
        rows = []
        for line in res.stdout.strip().split("\n"):
            if line:
                rows.append(line.split("\t"))
        return rows
    except Exception:
        return []

def extract_clean_invoice_number(raw_identifier: str) -> str:
    """
    Extracts 10-char invoice number (e.g. 'LP50936600') from raw Turnkey identifier
    like 'F0401LP5093660020260925' or 'LP50936600'.
    """
    if not raw_identifier:
        return ""
    m = re.search(r"([A-Z]{2}[0-9]{8})", raw_identifier)
    if m:
        return m.group(1)
    return raw_identifier

class StatusSyncer:
    def __init__(self, sb_client: SupabaseClient):
        self.sb = sb_client

    def sync_once(self) -> Dict[str, int]:
        """
        Polls recent Turnkey transmission logs and syncs status back to Supabase orders.
        Returns: summary dict with counts of synced records.
        """
        stats = {"success": 0, "failed": 0, "cancelled": 0, "skipped": 0}

        # Query messages updated within recent interval
        query = """
        SELECT message_type, invoice_identifier, status, uuid, message_dts
        FROM turnkey_message_log
        WHERE status IN ('G', 'C', 'E')
        ORDER BY message_dts DESC
        LIMIT 100;
        """

        rows = run_turnkey_psql(query)
        if not rows:
            return stats

        for row in rows:
            if len(row) < 4:
                continue

            msg_type, raw_id, status, uuid = row[0], row[1], row[2], row[3]
            inv_number = extract_clean_invoice_number(raw_id)
            if not inv_number:
                continue

            # Check if this invoice is in DISPATCHED or CANCEL_DISPATCHED in Supabase
            if msg_type in ("F0401", "A0101"):
                if status in ("G", "C"):
                    # Success
                    ok = self.sb.update_order_status(
                        invoice_number=inv_number,
                        status="SUCCESS",
                        result_code="00000",
                        uuid=uuid
                    )
                    if ok:
                        stats["success"] += 1
                elif status == "E":
                    # Error
                    ok = self.sb.update_order_status(
                        invoice_number=inv_number,
                        status="FAILED",
                        result_code="E9999",
                        result_desc="Turnkey processing error (E)",
                        uuid=uuid
                    )
                    if ok:
                        stats["failed"] += 1

            elif msg_type in ("F0501", "A0201"):
                if status in ("G", "C"):
                    # Cancellation Success
                    ok = self.sb.update_order_cancelled_status(
                        invoice_number=inv_number,
                        status="CANCELLED",
                        result_code="00000",
                        uuid=uuid
                    )
                    if ok:
                        stats["cancelled"] += 1
                elif status == "E":
                    ok = self.sb.update_order_cancelled_status(
                        invoice_number=inv_number,
                        status="CANCEL_FAILED",
                        result_code="E9999",
                        uuid=uuid
                    )
                    if ok:
                        stats["failed"] += 1

        return stats
