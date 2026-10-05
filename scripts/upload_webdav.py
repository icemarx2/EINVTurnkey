#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload generated ODT, PDF, and evidence files to WebDAV server:
Target URL: http://guest:guest@192.168.1.28/invoice/
"""

import os
import sys
import subprocess

WEBDAV_BASE = "http://guest:guest@192.168.1.28/invoice"

def upload_file(local_path: str, remote_filename: str = None):
    if not os.path.exists(local_path):
        print(f"[SKIP] Local file not found: {local_path}")
        return False
    
    if remote_filename is None:
        remote_filename = os.path.basename(local_path)
        
    url = f"{WEBDAV_BASE}/{remote_filename}"
    print(f"[UPLOADING] {local_path} -> {url}...")
    
    cmd = [
        "curl", "-s", "-S",
        "-u", "guest:guest",
        "-T", local_path,
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[SUCCESS] Uploaded {remote_filename}")
        return True
    else:
        print(f"[ERROR] Failed to upload {remote_filename}: {res.stderr.strip()}")
        return False

def main():
    docs_dir = "/invoice/EINVTurnkey/docs"
    evidence_dir = os.path.join(docs_dir, "evidence")
    
    # Upload all main documents (00 through 06) and self-test files
    files_to_upload = []
    for f in sorted(os.listdir(docs_dir)):
        if any(f.startswith(f"{i:02d}_") for i in range(7)) and (f.endswith(".odt") or f.endswith(".pdf") or f.endswith(".docx")):
            files_to_upload.append(os.path.join(docs_dir, f))
    
    # Also include any evidence files if available
    if os.path.isdir(evidence_dir):
        for f in sorted(os.listdir(evidence_dir)):
            if f.endswith(".png"):
                files_to_upload.append(os.path.join(evidence_dir, f))
                
    success_count = 0
    for p in files_to_upload:
        if os.path.exists(p):
            if upload_file(p):
                success_count += 1
                
    print(f"\nFinished uploading {success_count} files to {WEBDAV_BASE}/")

if __name__ == "__main__":
    main()
