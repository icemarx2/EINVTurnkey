#!/usr/bin/env python3
"""
erp_bridge_checks.py - daily e-invoice integrity checks for the Turnkey
self-test items 1-4 (track, duplicate, missing upload, error handling).

Every command prints what it really found, exits 0 (all fine), 1 (anomaly
found -> alert written/sent) or 2 (config/parse problem). Nothing is faked:
negative tests use real validators on real data (see `track --check-number`).

!! The table/column names below are ASSUMPTIONS taken from your self-test
!! document. Edit CFG so they match your real schema before using it.

Usage examples
  export ERP_DSN="dbname=erp_db user=erp host=localhost"
  python3 erp_bridge_checks.py track
  python3 erp_bridge_checks.py track --check-number AB12345678 --check-number LP99999999
  python3 erp_bridge_checks.py duplicate
  python3 erp_bridge_checks.py missing
  python3 erp_bridge_checks.py errors
  python3 erp_bridge_checks.py summary --dir /path/to/SummaryResult --date 2026-09-24
  python3 erp_bridge_checks.py all --dir /path/to/SummaryResult

Alerting: every anomaly is appended to EINV_ALERT_LOG (default ./alert.log).
If SMTP_HOST and EINV_ALERT_TO are set, an email is also sent (optional
SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM). The result of the send attempt
is printed as-is, including failures.
"""
import argparse
import datetime as dt
import glob
import os
import re
import smtplib
import sqlite3  # only used when ERP_SQLITE is set (offline self-test)
import sys
import xml.etree.ElementTree as ET
from email.message import EmailMessage

# --------------------------------------------------------------------------
# EDIT THIS to match your schema (assumed from the self-test document)
# --------------------------------------------------------------------------
CFG = {
    "quota_table": "einv_track_quota",   # track_year_month, track_prefix, start_no, end_no, is_active
    "orders_table": "orders",
    "col_number": "einv_number",         # e.g. LP50936610
    "col_status": "einv_status",         # PENDING / DISPATCHED / SUCCESS / FAILED / CANCEL_FAILED
    "col_code": "einv_result_code",
    "col_desc": "einv_result_desc",
    "col_issued_at": "einv_issued_at",   # set to None if you have no such column
    "col_sent_at": "einv_sent_at",       # when the XML was handed to Turnkey
    "msglog_table": "turnkey_message_log",
    "msglog_sent_at": "sent_at",
    "dispatched_timeout_min": 60,
    "alert_log": os.environ.get("EINV_ALERT_LOG", "./alert.log"),
}
INVOICE_RE = re.compile(r"^[A-Z]{2}[0-9]{8}$")


# ----------------------------- helpers ------------------------------------
class PsqlCur:
    def __init__(self, dsn):
        self.dsn = dsn
        self.rows = []
    def execute(self, sql):
        import subprocess
        cmd = ["psql", self.dsn, "-t", "-A", "-F", "\t", "-c", sql]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or f"psql exited with {res.returncode}")
        self.rows = []
        for line in res.stdout.strip().split("\n"):
            if not line:
                continue
            cols = line.split("\t")
            parsed = []
            for c in cols:
                if c == "t":
                    parsed.append(True)
                elif c == "f":
                    parsed.append(False)
                elif c.isdigit():
                    parsed.append(int(c))
                else:
                    parsed.append(c)
            self.rows.append(tuple(parsed))
    def fetchall(self):
        return self.rows
    def close(self):
        pass

class PsqlConn:
    def __init__(self, dsn):
        self.dsn = dsn
    def cursor(self):
        return PsqlCur(self.dsn)
    def close(self):
        pass

def connect():
    if os.environ.get("ERP_SQLITE"):            # offline self-test only
        return sqlite3.connect(os.environ["ERP_SQLITE"]), "sqlite"
    dsn = os.environ.get("ERP_DSN")
    if not dsn:
        sys.exit("ERP_DSN is not set (e.g. 'dbname=erp_db user=erp host=localhost')")
    try:
        import psycopg2                          # pip install psycopg2-binary
        return psycopg2.connect(dsn), "postgres"
    except ImportError:
        return PsqlConn(dsn), "postgres"


def q(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    return rows


def to_dt(v):
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.replace(tzinfo=None)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    return dt.datetime.fromisoformat(str(v).replace("Z", "")[:19])


def period_of(d):
    """Taiwan invoice period code, e.g. 2026-09 -> '11510' (ROC year + even month)."""
    month = d.month if d.month % 2 == 0 else d.month + 1
    return f"{d.year - 1911}{month:02d}"


def split_number(n):
    return n[:2], int(n[2:])


def notify(subject, lines):
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CFG["alert_log"], "a", encoding="utf-8") as f:
        for ln in lines:
            f.write(f"[{stamp}] [ALERT] {subject}: {ln}\n")
    status = f"alert log: {CFG['alert_log']}"
    host, to = os.environ.get("SMTP_HOST"), os.environ.get("EINV_ALERT_TO")
    if not (host and to):
        return status + "; email: NOT sent (SMTP_HOST / EINV_ALERT_TO not set)"
    try:
        msg = EmailMessage()
        msg["Subject"], msg["To"] = f"[ALERT] {subject}", to
        msg["From"] = os.environ.get("SMTP_FROM", to)
        msg.set_content("\n".join(lines))
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "25")), timeout=15) as s:
            if os.environ.get("SMTP_USER"):
                s.starttls()
                s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASS", ""))
            s.send_message(msg)
        return status + f"; email sent to {to}"
    except Exception as e:  # report honestly
        return status + f"; email FAILED: {e}"


def finish(name, issues, details):
    print(f"== {name}  ({dt.datetime.now():%Y-%m-%d %H:%M:%S}) ==")
    for d in details:
        print("  " + d)
    if issues:
        print(f"RESULT: {len(issues)} ANOMALY(IES)")
        for i in issues:
            print("  [!] " + i)
        print("  " + notify(name, issues))
        return 1
    print("RESULT: no anomaly")
    return 0


# ------------------------------- checks -----------------------------------
def load_quota(conn):
    rows = q(conn, f"SELECT track_year_month, track_prefix, start_no, end_no, is_active "
                   f"FROM {CFG['quota_table']}")
    return [(str(p), pre, int(a), int(b), bool(act)) for p, pre, a, b, act in rows]


def validate_number(num, issued, quota):
    """Return a list of problems for one invoice number (empty list = fine)."""
    if not INVOICE_RE.match(num):
        return [f"{num}: bad format (need 2 capital letters + 8 digits)"]
    pre, n = split_number(num)
    hits = [x for x in quota if x[1] == pre and x[2] <= n <= x[3]]
    if not hits:
        return [f"{num}: not inside any registered track range"]
    if not any(h[4] for h in hits):
        return [f"{num}: track range is registered but not active"]
    expected = period_of(issued or dt.datetime.now())
    if not any(h[0] == expected and h[4] for h in hits):
        return [f"{num}: track belongs to period {hits[0][0]}, expected {expected}"]
    return []


def check_track(conn, extra_numbers):
    quota = load_quota(conn)
    issues, details = [], [f"registered ranges: {len(quota)}"]
    if extra_numbers:                              # real negative test, no DB writes
        for n in extra_numbers:
            problems = validate_number(n, None, quota)
            details.append(f"validate {n}: {'OK' if not problems else 'REJECTED'}")
            issues += problems
        return finish("track-check (manual numbers)", issues, details)
    sel = f"{CFG['col_number']}" + (f", {CFG['col_issued_at']}" if CFG["col_issued_at"] else "")
    rows = q(conn, f"SELECT {sel} FROM {CFG['orders_table']} WHERE {CFG['col_number']} IS NOT NULL")
    for r in rows:
        issues += validate_number(r[0], to_dt(r[1]) if len(r) > 1 else None, quota)
    details.append(f"invoices checked: {len(rows)}")
    return finish("track-check", issues, details)


def has_unique_index(conn, kind):
    col, tbl = CFG["col_number"], CFG["orders_table"]
    if kind == "postgres":
        rows = q(conn, f"SELECT indexdef FROM pg_indexes WHERE tablename='{tbl}'")
        return any("UNIQUE" in r[0].upper() and col in r[0] for r in rows)
    for r in q(conn, f"PRAGMA index_list({tbl})"):          # sqlite: r[2] = unique flag
        cols = [c[2] for c in q(conn, f"PRAGMA index_info({r[1]})")]
        if r[2] and col in cols:
            return True
    return False


def check_duplicate(conn, kind):
    col, tbl = CFG["col_number"], CFG["orders_table"]
    dups = q(conn, f"SELECT {col}, COUNT(*) FROM {tbl} WHERE {col} IS NOT NULL "
                   f"GROUP BY {col} HAVING COUNT(*) > 1")
    total = q(conn, f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NOT NULL")[0][0]
    uniq = has_unique_index(conn, kind)
    details = [f"invoices checked: {total}", f"unique index on {col}: {'present' if uniq else 'MISSING'}"]
    issues = [f"{n} used {c} times" for n, c in dups]
    if not uniq:
        issues.append(f"no UNIQUE index on {tbl}.{col}")
    return finish("duplicate-check", issues, details)


def check_missing(conn):
    c = CFG
    rows = q(conn, f"SELECT {c['col_number']}, {c['col_status']}, {c['col_sent_at']} "
                   f"FROM {c['orders_table']} WHERE {c['col_number']} IS NOT NULL")
    now, limit = dt.datetime.now(), dt.timedelta(minutes=c["dispatched_timeout_min"])
    issued = len(rows)
    ok = [r for r in rows if r[1] == "SUCCESS"]
    pending = [r for r in rows if r[1] == "PENDING"]
    late = [r for r in rows if r[1] == "DISPATCHED" and (to_dt(r[2]) is None or now - to_dt(r[2]) > limit)]
    failed = [r for r in rows if r[1] in ("FAILED", "CANCEL_FAILED")]
    details = [f"issued in ERP: {issued}", f"confirmed (SUCCESS): {len(ok)}",
               f"PENDING (never sent): {len(pending)}",
               f"DISPATCHED > {c['dispatched_timeout_min']} min: {len(late)}",
               f"FAILED (see `errors`): {len(failed)}"]
    issues = [f"{r[0]}: never handed to Turnkey (PENDING) - re-send" for r in pending]
    issues += [f"{r[0]}: no confirmation after {c['dispatched_timeout_min']} min - re-send/check Turnkey" for r in late]
    return finish("missing-upload-check", issues, details)


def check_errors(conn):
    c = CFG
    rows = q(conn, f"SELECT {c['col_number']}, {c['col_status']}, {c['col_code']}, {c['col_desc']} "
                   f"FROM {c['orders_table']} WHERE {c['col_status']} IN ('FAILED','CANCEL_FAILED')")
    issues = [f"{n} [{s}] code={code} desc={desc} - correct and re-issue" for n, s, code, desc in rows]
    return finish("error-handling-check", issues, [f"invoices in FAILED/CANCEL_FAILED: {len(rows)}"])


def parse_summary(path):
    """Tolerant SummaryResult reader. Supports standard Turnkey 4.1 DetailList/Message/ResultType
    as well as flat summary schemas."""
    if path.endswith("-Final.SummaryResult"):
        return None
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None
    root = tree.getroot()
    messages = root.findall(".//{*}Message")
    if messages:
        total, good, bad = 0, 0, 0
        for m in messages:
            t = m.findtext(".//{*}Total/{*}ResultDetailType/{*}Count") or m.findtext(".//{*}Total/{*}Count")
            g = m.findtext(".//{*}Good/{*}ResultDetailType/{*}Count") or m.findtext(".//{*}Good/{*}Count")
            f = m.findtext(".//{*}Failed/{*}ResultDetailType/{*}Count") or m.findtext(".//{*}Failed/{*}Count")
            if t is not None and t.strip().isdigit():
                total += int(t.strip())
            if g is not None and g.strip().isdigit():
                good += int(g.strip())
            if f is not None and f.strip().isdigit():
                bad += int(f.strip())
        return total, good, bad

    vals = {}
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if el.text and el.text.strip():
            vals.setdefault(tag, el.text.strip())
        for k, v in el.attrib.items():
            vals.setdefault(k.lower(), v)

    def pick(names):
        for n in names:
            if n in vals and vals[n].isdigit():
                return int(vals[n])
        return None
    total = pick(["totalcount", "total", "totalrecords", "totalnum"])
    good = pick(["successcount", "success", "good", "goodcount"])
    bad = pick(["failcount", "failed", "fail", "error", "errorcount"])
    if total is None or good is None:
        raise ValueError(f"cannot find total/success counts in {path}; tags seen: {sorted(vals)}. "
                         f"Adjust the name lists in parse_summary().")
    return total, good, (bad or 0)


def check_summary(conn, directory, day):
    d0 = dt.datetime.strptime(day, "%Y-%m-%d")
    d1 = d0 + dt.timedelta(days=1)
    files = sorted(glob.glob(os.path.join(directory, f"*{d0:%Y%m%d}*SummaryResult*")))
    if not files:
        files = sorted(glob.glob(os.path.join(directory, "**", f"*{d0:%Y%m%d}*SummaryResult*"), recursive=True))
    files = [f for f in files if not f.endswith("-Final.SummaryResult")]
    if not files:
        print(f"no SummaryResult file for {day} in {directory}")
        return 2
    try:
        parsed = [p for f in files if (p := parse_summary(f)) is not None]
    except ValueError as e:
        print(e)
        return 2
    total, good, bad = (sum(x[i] for x in parsed) for i in range(3))
    erp = q(conn, f"SELECT COUNT(*) FROM {CFG['msglog_table']} WHERE {CFG['msglog_sent_at']} >= "
                  f"'{d0:%Y-%m-%d}' AND {CFG['msglog_sent_at']} < '{d1:%Y-%m-%d}'")[0][0]
    details = [f"SummaryResult files: {len(files)}", f"SummaryResult total/success/failed: {total}/{good}/{bad}",
               f"ERP messages sent that day: {erp}"]
    issues = []
    if erp != total:
        issues.append(f"ERP sent {erp} but SummaryResult reports {total}")
    if good != total:
        issues.append(f"only {good} of {total} succeeded ({bad} failed)")
    return finish(f"summary-reconcile {day}", issues, details)


# -------------------------------- main ------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("track")
    t.add_argument("--check-number", action="append", default=[], help="validate a number without touching data")
    sub.add_parser("duplicate")
    sub.add_parser("missing")
    sub.add_parser("errors")
    for name in ("summary", "all"):
        s = sub.add_parser(name)
        s.add_argument("--dir", help="folder holding SummaryResult files")
        s.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()

    conn, kind = connect()
    codes = []
    if a.cmd == "track":
        codes.append(check_track(conn, a.check_number))
    elif a.cmd == "duplicate":
        codes.append(check_duplicate(conn, kind))
    elif a.cmd == "missing":
        codes.append(check_missing(conn))
    elif a.cmd == "errors":
        codes.append(check_errors(conn))
    elif a.cmd == "summary":
        if not a.dir:
            sys.exit("--dir is required for summary")
        codes.append(check_summary(conn, a.dir, a.date))
    else:  # all
        codes += [check_track(conn, []), check_duplicate(conn, kind), check_missing(conn), check_errors(conn)]
        if a.dir:
            codes.append(check_summary(conn, a.dir, a.date))
    sys.exit(2 if 2 in codes else (1 if 1 in codes else 0))


if __name__ == "__main__":
    main()
