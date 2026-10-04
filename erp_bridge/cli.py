#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Line Interface for Turnkey-ERP Bridge.
"""

import sys
import time
import argparse
import logging
from .config import POLL_INTERVAL_SECONDS, SUPABASE_URL
from .supabase_client import SupabaseClient
from .processor import BridgeProcessor
from .syncer import StatusSyncer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("erp_bridge")

def cmd_run(args):
    """Run one batch of invoice issuance, cancellations, and status synchronization."""
    sb = SupabaseClient()
    if not sb.is_configured():
        logger.error("Supabase is not configured. Please check your .env file (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).")
        sys.exit(1)

    processor = BridgeProcessor(sb)
    syncer = StatusSyncer(sb)

    logger.info("Executing ERP-to-Turnkey batch run...")
    inv_stats = processor.process_invoices_once()
    logger.info(f"Invoice Issuance Batch: {inv_stats}")

    cancel_stats = processor.process_cancellations_once()
    logger.info(f"Cancellation Batch: {cancel_stats}")

    sync_stats = syncer.sync_once()
    logger.info(f"Status Sync: {sync_stats}")
    logger.info("Batch run complete.")

def cmd_sync(args):
    """Run status synchronization only."""
    sb = SupabaseClient()
    syncer = StatusSyncer(sb)
    stats = syncer.sync_once()
    logger.info(f"Status Sync Complete: {stats}")

def cmd_daemon(args):
    """Run 24/7 background polling daemon."""
    sb = SupabaseClient()
    if not sb.is_configured():
        logger.error("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        sys.exit(1)

    interval = args.interval or POLL_INTERVAL_SECONDS
    processor = BridgeProcessor(sb)
    syncer = StatusSyncer(sb)

    logger.info(f"Starting Turnkey-ERP Bridge Daemon (Poll interval: {interval}s)...")
    try:
        while True:
            try:
                processor.process_invoices_once()
                processor.process_cancellations_once()
                syncer.sync_once()
            except Exception as e:
                logger.error(f"Error in daemon polling cycle: {e}", exc_info=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user.")

def cmd_add_track(args):
    """Add a new bimonthly track quota to Supabase."""
    sb = SupabaseClient()
    if not sb.is_configured():
        logger.error("Supabase is not configured. Please check .env file.")
        sys.exit(1)

    try:
        res = sb.add_track_quota(
            year_month=args.period,
            track_prefix=args.prefix,
            start_no=args.start,
            end_no=args.end
        )
        logger.info(f"Successfully added track quota for period {args.period}: {args.prefix}{args.start:08d} ~ {args.prefix}{args.end:08d}")
    except Exception as e:
        logger.error(f"Failed adding track quota: {e}")
        sys.exit(1)

def cmd_status(args):
    """Print status summary."""
    sb = SupabaseClient()
    print("=" * 70)
    print("  Turnkey to Supabase ERP Integration Bridge Status")
    print("=" * 70)
    print(f"  Supabase Configured : {sb.is_configured()} ({SUPABASE_URL or 'None'})")

    if sb.is_configured():
        try:
            pending_invoices = len(sb.get_pending_issuance_orders(limit=100))
            pending_cancels = len(sb.get_pending_cancellation_orders(limit=100))
            print(f"  Pending Invoices    : {pending_invoices}")
            print(f"  Pending Cancels     : {pending_cancels}")
        except Exception as e:
            print(f"  Supabase Connection : Error ({e})")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Turnkey to Supabase ERP Bridge")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # run command
    p_run = subparsers.add_parser("run", help="Run a single issuance and sync batch")
    p_run.set_defaults(func=cmd_run)

    # sync command
    p_sync = subparsers.add_parser("sync", help="Sync Turnkey MOF results back to Supabase")
    p_sync.set_defaults(func=cmd_sync)

    # daemon command
    p_daemon = subparsers.add_parser("daemon", help="Run as continuous background daemon")
    p_daemon.add_argument("--interval", type=int, default=POLL_INTERVAL_SECONDS, help="Polling interval in seconds")
    p_daemon.set_defaults(func=cmd_daemon)

    # add-track command
    p_track = subparsers.add_parser("add-track", help="Register new bimonthly track quota")
    p_track.add_argument("--period", required=True, help="ROC Year-Month (e.g. 11510)")
    p_track.add_argument("--prefix", required=True, help="2-letter track prefix (e.g. LP)")
    p_track.add_argument("--start", type=int, required=True, help="Start number (e.g. 50936600)")
    p_track.add_argument("--end", type=int, required=True, help="End number (e.g. 50939099)")
    p_track.set_defaults(func=cmd_add_track)

    # status command
    p_status = subparsers.add_parser("status", help="Show system status")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
