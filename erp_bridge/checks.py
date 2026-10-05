#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily e-invoice integrity checks for the MOF Turnkey pre-launch self-test.

Four checks (matching 前置作業檢測 items 1-4):
  1. Track check      (字軌檢核)       invoice numbers are well-formed, belong to an
                                        active quota range of the current period.
  2. Duplicate check  (重號檢核)       no invoice number is used by more than one order.
  3. Missing upload   (漏上傳檢核)     every issued invoice reached status SUCCESS;
                                        issued vs. confirmed counts reconcile.
  4. Error handling   (發票異常處理檢核) invoices in FAILED / CANCEL_FAILED state are listed
                                        with their MOF result code.

The check functions are pure (they take plain row dictionaries) so they can be
unit-tested; `run_checks` fetches the rows from Supabase and renders a report.
"""

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

INVOICE_RE = re.compile(r"^[A-Z]{2}[0-9]{8}$")

# An invoice still DISPATCHED after this many minutes is reported as not confirmed.
DISPATCH_GRACE_MINUTES = 60


def check_tracks(orders: List[Dict[str, Any]], quotas: List[Dict[str, Any]]) -> List[str]:
    """Return a list of anomaly descriptions for malformed / out-of-range numbers."""
    problems = []
    for o in orders:
        num = o.get("einv_number")
        if not num:
            continue
        if not INVOICE_RE.match(num):
            problems.append(f"{num}: malformed invoice number (expected 2 letters + 8 digits)")
            continue
        prefix, serial = num[:2], int(num[2:])
        in_range = [
            q for q in quotas
            if q["track_prefix"] == prefix and q["start_no"] <= serial <= q["end_no"]
        ]
        if not in_range:
            problems.append(f"{num}: not inside any registered track quota range")
        elif not any(q.get("is_active", True) for q in in_range):
            problems.append(f"{num}: belongs to an inactive (non-current) track quota")
    return problems


def check_duplicates(orders: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return {invoice_number: occurrences} for numbers used more than once."""
    counts: Dict[str, int] = defaultdict(int)
    for o in orders:
        if o.get("einv_number"):
            counts[o["einv_number"]] += 1
    return {n: c for n, c in counts.items() if c > 1}


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_missing_uploads(orders: List[Dict[str, Any]], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Reconcile issued invoices against confirmed (SUCCESS) ones."""
    now = now or datetime.now(timezone.utc)
    issued = [o for o in orders if o.get("einv_number")]
    confirmed = [o for o in issued if o.get("einv_status") in ("SUCCESS", "CANCEL_PENDING", "CANCEL_DISPATCHED", "CANCELLED", "CANCEL_FAILED")]
    unconfirmed = []
    for o in issued:
        if o.get("einv_status") == "DISPATCHED":
            sent = _parse_ts(o.get("einv_dispatched_at"))
            age_min = (now - sent).total_seconds() / 60 if sent else None
            if age_min is None or age_min >= DISPATCH_GRACE_MINUTES:
                unconfirmed.append((o["einv_number"], None if age_min is None else int(age_min)))
        elif o.get("einv_status") == "PENDING":
            unconfirmed.append((o["einv_number"], None))
    return {"issued": len(issued), "confirmed": len(confirmed), "unconfirmed": unconfirmed}


def check_errors(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return invoices that Turnkey / MOF rejected."""
    return [
        {
            "number": o.get("einv_number"),
            "status": o.get("einv_status"),
            "code": o.get("einv_result_code") or o.get("einv_cancel_result_code"),
            "desc": o.get("einv_result_desc"),
        }
        for o in orders
        if o.get("einv_status") in ("FAILED", "CANCEL_FAILED")
    ]


def render_report(orders, quotas, now: Optional[datetime] = None) -> (str, bool):
    """Build a human-readable report. Returns (text, all_ok)."""
    now = now or datetime.now(timezone.utc)
    tracks = check_tracks(orders, quotas)
    dups = check_duplicates(orders)
    missing = check_missing_uploads(orders, now)
    errors = check_errors(orders)

    line = "=" * 74
    out = [line,
           "  E-Invoice Integrity Check  |  奧銳有限公司 (00015555)",
           f"  Run time: {now.astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}",
           line]

    out.append(f"[1] 字軌檢核 Track check        : {'PASS' if not tracks else 'ALERT (%d)' % len(tracks)}")
    out.append(f"      invoices checked={sum(1 for o in orders if o.get('einv_number'))}, "
               f"quota ranges={len(quotas)}")
    out += [f"      ! {p}" for p in tracks]

    out.append(f"[2] 重號檢核 Duplicate check    : {'PASS' if not dups else 'ALERT (%d)' % len(dups)}")
    out += [f"      ! {n} used {c} times" for n, c in dups.items()]

    ok_missing = not missing["unconfirmed"] and missing["issued"] == missing["confirmed"]
    out.append(f"[3] 漏上傳檢核 Missing upload   : {'PASS' if ok_missing else 'ALERT (%d)' % len(missing['unconfirmed'])}")
    out.append(f"      issued={missing['issued']}  confirmed by MOF={missing['confirmed']}")
    for n, age in missing["unconfirmed"]:
        out.append(f"      ! {n} not confirmed" + (f" after {age} min" if age is not None else ""))

    out.append(f"[4] 發票異常處理檢核 Errors     : {'PASS' if not errors else 'ALERT (%d)' % len(errors)}")
    for e in errors:
        out.append(f"      ! {e['number']} status={e['status']} code={e['code']} {e['desc'] or ''}")

    all_ok = not tracks and not dups and ok_missing and not errors
    out.append(line)
    out.append(f"  RESULT: {'ALL CHECKS PASSED' if all_ok else 'ATTENTION REQUIRED - see items marked !'}")
    out.append(line)
    return "\n".join(out), all_ok


def run_checks(sb) -> int:
    """Fetch data from Supabase, print the report, return process exit code."""
    orders = sb.get_all_einv_orders()
    quotas = sb.get_track_quotas()
    text, ok = render_report(orders, quotas)
    print(text)
    return 0 if ok else 1
