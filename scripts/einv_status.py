#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turnkey Transmission Status & Audit Reporting Tool
Queries PostgreSQL database for latest Turnkey message logs and process results.
"""

import sys
import subprocess
import json

def run_psql(query):
    cmd = [
        "psql", "-U", "turnkey", "-h", "127.0.0.1", "-d", "turnkey",
        "-t", "-A", "-F", "\t", "-c", query
    ]
    env = {"PGPASSWORD": "turnkey", "PATH": "/usr/local/bin:/usr/bin:/bin"}
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if res.returncode != 0:
        print(f"Error querying database: {res.stderr.strip()}", file=sys.stderr)
        return []
    rows = []
    for line in res.stdout.strip().split("\n"):
        if line:
            rows.append(line.split("\t"))
    return rows

def print_status_summary():
    print("=" * 80)
    print("  MOF Electronic Invoice Turnkey Transmission Status Report")
    print("  Entity: 00015555 (奧銳有限公司) | Routing: PA006753")
    print("=" * 80)

    # 1. Total statistics by message_type and status
    stats_query = """
    SELECT message_type, category_type, process_type, status, count(*)
    FROM turnkey_message_log
    GROUP BY message_type, category_type, process_type, status
    ORDER BY message_type, status;
    """
    stats = run_psql(stats_query)
    print("\n[+] Message Statistics:")
    print(f"{'Msg Type':<10} {'Category':<10} {'Process':<12} {'Status':<8} {'Count':<6}")
    print("-" * 50)
    for row in stats:
        if len(row) >= 5:
            st = row[3]
            st_desc = "G (Success)" if st == "G" else ("E (Error)" if st == "E" else f"{st} (Pending)")
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<12} {st_desc:<16} {row[4]:<6}")

    # 2. Latest 15 messages
    latest_query = """
    SELECT seqno, uuid, message_type, from_party_id, to_party_id, invoice_identifier, status, message_dts
    FROM turnkey_message_log
    ORDER BY message_dts DESC
    LIMIT 15;
    """
    latest = run_psql(latest_query)
    print("\n[+] Latest 15 Messages:")
    print(f"{'SeqNo':<10} {'Type':<8} {'Identifier':<26} {'To Party':<12} {'Status':<8} {'Timestamp':<18}")
    print("-" * 84)
    for row in latest:
        if len(row) >= 8:
            st = row[6]
            st_color = "G" if st == "G" else ("E" if st == "E" else st)
            print(f"{row[0]:<10} {row[2]:<8} {row[5]:<26} {row[4]:<12} {st_color:<8} {row[7]:<18}")

    # 3. Check for any recent errors in sysevent_log
    err_query = """
    SELECT eventdts, errorcode, uuid, message1
    FROM turnkey_sysevent_log
    ORDER BY eventdts DESC
    LIMIT 5;
    """
    errs = run_psql(err_query)
    if errs:
        print("\n[+] Recent System Events / Errors:")
        print(f"{'Timestamp':<18} {'Code':<8} {'UUID':<10} {'Message':<40}")
        print("-" * 80)
        for r in errs:
            if len(r) >= 4:
                print(f"{r[0]:<18} {r[1]:<8} {r[2]:<10} {r[3]:<40}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    print_status_summary()
