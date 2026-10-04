#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML Schema Validator for MIG 4.1 electronic invoice documents.
Uses lxml.etree with local XSD files.
"""

import os
from pathlib import Path
from lxml import etree
from .config import XSD_ROOT

_SCHEMA_CACHE = {}

def get_schema(msg_type: str) -> etree.XMLSchema:
    """Retrieve or compile the XMLSchema for a given message type (e.g. 'F0401', 'F0501')."""
    msg_type = msg_type.upper()
    if msg_type in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[msg_type]

    xsd_file = Path(XSD_ROOT) / f"{msg_type}.xsd"
    if not xsd_file.is_file():
        raise FileNotFoundError(f"XSD schema file not found for {msg_type}: {xsd_file}")

    with open(xsd_file, "rb") as f:
        schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        _SCHEMA_CACHE[msg_type] = schema
        return schema

def validate_xml(msg_type: str, xml_bytes_or_str) -> tuple[bool, str]:
    """
    Validates XML content against the specified MIG 4.1 XSD schema.
    Returns: (is_valid: bool, error_message: str)
    """
    try:
        schema = get_schema(msg_type)
        if isinstance(xml_bytes_or_str, str):
            xml_bytes = xml_bytes_or_str.encode("utf-8")
        else:
            xml_bytes = xml_bytes_or_str

        doc = etree.fromstring(xml_bytes)
        schema.assertValid(doc)
        return True, ""
    except etree.DocumentInvalid as e:
        return False, f"XSD Schema Validation Error: {e}"
    except Exception as e:
        return False, f"XML Parsing / Validation Error: {e}"
