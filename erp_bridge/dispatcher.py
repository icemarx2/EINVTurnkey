#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atomic XML File Dispatcher into Turnkey UpCast staging folders.
"""

import os
from pathlib import Path
from .config import TURNKEY_ROOT

def get_upcast_src_dir(category: str, msg_type: str) -> Path:
    """Returns the Turnkey UpCast SRC directory for the given category and message type."""
    target_dir = Path(TURNKEY_ROOT) / "UpCast" / category / msg_type / "SRC"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def dispatch_xml(category: str, msg_type: str, filename_base: str, xml_content: str) -> str:
    """
    Atomically writes XML content to Turnkey UpCast SRC directory.
    Writes to .tmp first, then renames to .xml.
    Returns: Destination file path.
    """
    src_dir = get_upcast_src_dir(category, msg_type)
    final_filename = f"{filename_base}.xml" if not filename_base.endswith(".xml") else filename_base
    tmp_filename = f"{final_filename}.tmp"

    final_path = src_dir / final_filename
    tmp_path = src_dir / tmp_filename

    # Write to temporary file
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Atomic rename
    os.replace(tmp_path, final_path)
    return str(final_path)
