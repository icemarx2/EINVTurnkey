#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration loader for erp_bridge.
Loads settings from environment variables and optional .env file.
"""

import os
from pathlib import Path

def load_dotenv(dotenv_path=None):
    """Simple parser for .env file without external dependencies."""
    if dotenv_path is None:
        dotenv_path = Path("/invoice/EINVTurnkey/.env")
    else:
        dotenv_path = Path(dotenv_path)

    if not dotenv_path.is_file():
        return

    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key not in os.environ:
                os.environ[key] = val

# Load .env on import
load_dotenv()

# Supabase REST API Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Seller Company Details (MIG 4.1 Required)
COMPANY_SELLER_BAN = os.environ.get("COMPANY_SELLER_BAN", "00015555")
COMPANY_SELLER_NAME = os.environ.get("COMPANY_SELLER_NAME", "奧銳有限公司")
COMPANY_SELLER_ADDR = os.environ.get("COMPANY_SELLER_ADDR", "臺北市中正區漢口街1段45號10樓")
TURNKEY_ROUTING_ID = os.environ.get("TURNKEY_ROUTING_ID", "PA006753")

# Turnkey System Paths
TURNKEY_ROOT = Path(os.environ.get("TURNKEY_ROOT", "/invoice/EINVTurnkey"))
XSD_ROOT = Path(os.environ.get("XSD_ROOT", str(TURNKEY_ROOT / "scripts" / "xsd_temp" / "xsd" / "v41")))

# Order Trigger Statuses
raw_triggers = os.environ.get("EINV_TRIGGER_INTERNAL_STATUSES", "shipped,delivered,completed")
EINV_TRIGGER_INTERNAL_STATUSES = [s.strip().lower() for s in raw_triggers.split(",") if s.strip()]

# Current ROC Period (e.g. '11510' for 115年09-10月)
CURRENT_YEAR_MONTH = os.environ.get("CURRENT_YEAR_MONTH", "11510")

# Polling Interval
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "10"))

# Local PostgreSQL for Turnkey Message Log
PG_HOST = os.environ.get("PGHOST", "127.0.0.1")
PG_PORT = os.environ.get("PGPORT", "5432")
PG_USER = os.environ.get("PGUSER", "turnkey")
PG_PASSWORD = os.environ.get("PGPASSWORD", "turnkey")
PG_DATABASE = os.environ.get("PGDATABASE", "turnkey")
