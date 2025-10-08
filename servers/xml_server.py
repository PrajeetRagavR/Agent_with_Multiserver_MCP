# xml_server.py
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import xml.etree.ElementTree as ET
from langchain_core.messages import HumanMessage
import re
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
from typing import List, Dict, Any

# Try to use lxml for better XPath support; fallback to stdlib
try:
    from lxml import etree as LET
    LXML_AVAILABLE = True
except Exception:
    LXML_AVAILABLE = False

# Optional: placeholder for LLM import (uncomment and configure if you want)
# from langchain_groq import ChatGroq
# llm = ChatGroq(model="meta-llama/...", temperature=0)

# ======================================================
# Server & paths
# ======================================================
mcp = FastMCP("XMLServer")
BASE = Path(".").resolve()
XML_DIR = BASE / "xml_data"
XML_DIR.mkdir(exist_ok=True)

# Thread pool for blocking file I/O and cpu-light parsing
io_executor = ThreadPoolExecutor(max_workers=4)
# Limit concurrent XML operations (prevent overload)
xml_semaphore = asyncio.Semaphore(4)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xml_server")


# ======================================================
# Helpers
# ======================================================
def _safe_path(filename: str) -> Path:
    """Resolve filename into XML_DIR and prevent path escape."""
    p = (XML_DIR / filename).resolve()
    try:
        p.relative_to(XML_DIR)
    except Exception:
        raise ValueError("Path escape not allowed")
    return p

def _parse_tree_sync(path: Path):
    """Return parsed tree and root; uses lxml when available for richer XPath."""
    if LXML_AVAILABLE:
        parser = LET.parse(str(path))
        return parser, parser.getroot()
    else:
        tree = ET.parse(str(path))
        return tree, tree.getroot()

def _to_pretty_string(elem) -> str:
    if LXML_AVAILABLE:
        return LET.tostring(elem, pretty_print=True, encoding="unicode")
    else:
        return ET.tostring(elem, encoding="unicode")


# ======================================================
# Tools
# ======================================================
@mcp.tool()
async def ping() -> str:
    """Simple health check."""
    return "XMLServer alive"

@mcp.tool()
async def list_xml_files() -> List[str]:
    try:
        return [p.name for p in XML_DIR.glob("*.xml")]
    except Exception as e:
        logger.exception("list_xml_files failed")
        return [f"ERROR: {e}"]

@mcp.tool()
async def read_xml_file(filename: str) -> str:
    """Return raw XML content (safe path)."""
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: file not found: {filename}"
            return await loop.run_in_executor(io_executor, p.read_text, "utf-8")
        except Exception as e:
            logger.exception("read_xml_file failed")
            return f"ERROR: {e}"

@mcp.tool()
async def create_xml_file(filename: str, root_tag: str) -> str:
    """Create new XML with root tag. Won't overwrite by default."""
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if p.exists():
                return f"ERROR: {filename} already exists"
            def _task():
                root = ET.Element(root_tag)
                tree = ET.ElementTree(root)
                tree.write(str(p), encoding="utf-8", xml_declaration=True)
                return True
            await loop.run_in_executor(io_executor, _task)
            return f"Created XML file: {filename}"
        except Exception as e:
            logger.exception("create_xml_file failed")
            return f"ERROR: {e}"

@mcp.tool()
async def add_xml_element(filename: str, parent_xpath: str, new_tag: str, new_text: str = "") -> str:
    """
    Add a new element under matched parent(s). parent_xpath supports basic XPath.
    Returns number of parents updated.
    """
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: {filename} not found"

            def _task():
                tree, root = _parse_tree_sync(p)
                if LXML_AVAILABLE:
                    parents = root.findall(parent_xpath)
                else:
                    # xml.etree supports a subset of XPath - keep it simple
                    parents = root.findall(parent_xpath)
                if not parents:
                    raise ValueError("Parent not found for xpath: " + parent_xpath)
                for parent in parents:
                    new_elem = ET.SubElement(parent, new_tag)
                    new_elem.text = new_text
                # write back using appropriate writer
                if LXML_AVAILABLE:
                    tree.write(str(p), encoding="utf-8", pretty_print=True, xml_declaration=True)
                else:
                    tree.write(str(p), encoding="utf-8", xml_declaration=True)
                return len(parents)

            count = await loop.run_in_executor(io_executor, _task)
            return f"Added <{new_tag}> under {count} parent(s) in {filename}"
        except Exception as e:
            logger.exception("add_xml_element failed")
            return f"ERROR: {e}"

@mcp.tool()
async def update_xml_text(filename: str, xpath: str, new_text: str) -> str:
    """Update text of elements matched by xpath. Returns number updated."""
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: {filename} not found"
            def _task():
                tree, root = _parse_tree_sync(p)
                elems = root.findall(xpath)
                if not elems:
                    raise ValueError("No elements matched xpath")
                for e in elems:
                    e.text = new_text
                if LXML_AVAILABLE:
                    tree.write(str(p), encoding="utf-8", pretty_print=True, xml_declaration=True)
                else:
                    tree.write(str(p), encoding="utf-8", xml_declaration=True)
                return len(elems)
            changed = await loop.run_in_executor(io_executor, _task)
            return f"Updated text for {changed} elements in {filename}"
        except Exception as e:
            logger.exception("update_xml_text failed")
            return f"ERROR: {e}"

@mcp.tool()
async def delete_xml_element(filename: str, xpath: str) -> str:
    """Delete elements matched by xpath. Returns number deleted."""
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: {filename} not found"
            def _task():
                tree, root = _parse_tree_sync(p)
                elems = root.findall(xpath)
                if not elems:
                    return 0
                # need parent removal: for lxml it's simple; for ET we search parent
                deleted = 0
                if LXML_AVAILABLE:
                    for e in elems:
                        parent = e.getparent()
                        if parent is not None:
                            parent.remove(e)
                            deleted += 1
                else:
                    # xml.etree: iterate over all parents and remove children matching xpath
                    for parent in root.iter():
                        to_remove = [child for child in list(parent) if LET is None and child in elems] if False else []
                    # fallback: remove by tag name if xpath is simple tag
                    # We'll implement a safe fallback: remove all matching top-level children with same tag
                    for e in elems:
                        parent = root
                        for child in list(parent):
                            if child is e:
                                parent.remove(child)
                                deleted += 1
                if LXML_AVAILABLE:
                    tree.write(str(p), encoding="utf-8", pretty_print=True, xml_declaration=True)
                else:
                    tree.write(str(p), encoding="utf-8", xml_declaration=True)
                return deleted
            deleted = await loop.run_in_executor(io_executor, _task)
            return f"Deleted {deleted} elements from {filename}"
        except Exception as e:
            logger.exception("delete_xml_element failed")
            return f"ERROR: {e}"

@mcp.tool()
async def query_xml(filename: str, xpath: str) -> List[str]:
    """Query XML using XPath; returns list of stringified elements."""
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return [f"ERROR: {filename} not found"]
            def _task():
                tree, root = _parse_tree_sync(p)
                elems = root.findall(xpath)
                return [_to_pretty_string(e) for e in elems]
            return await loop.run_in_executor(io_executor, _task)
        except Exception as e:
            logger.exception("query_xml failed")
            return [f"ERROR: {e}"]

# Improved NLP -> XML: uses a simple rule parser and optional LLM placeholder
@mcp.tool()
async def nlp_to_xml(natural_text: str, filename: str = "nlp_output.xml") -> str:
    """
    Convert classic patterns into XML. Example expected input:
    "Create root <person> with <name>John</name> and <age>30</age>"
    For complex requests, you can integrate an LLM to output structured XML.
    """
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            # quick rule-based parse
            root_match = re.search(r"(root|root tag)\s*<(\w+)>", natural_text, re.I)
            if not root_match:
                # try simple "Create <root> ..." pattern
                rm = re.search(r"create\s+<(\w+)>", natural_text, re.I)
                if rm:
                    root_tag = rm.group(1)
                else:
                    return "ERROR: couldn't detect root; include 'root <tag>' or 'create <tag>'"
            else:
                root_tag = root_match.group(2)

            elems = re.findall(r"<(\w+)>(.*?)</\1>", natural_text)
            root_el = ET.Element(root_tag)
            for tag, text in elems:
                child = ET.SubElement(root_el, tag)
                child.text = text.strip()

            p = _safe_path(filename)
            def _task():
                tree = ET.ElementTree(root_el)
                tree.write(str(p), encoding="utf-8", xml_declaration=True)
                return True
            await loop.run_in_executor(io_executor, _task)
            return f"Generated {filename} from natural language (rule-based)."
        except Exception as e:
            logger.exception("nlp_to_xml failed")
            return f"ERROR: {e}"

@mcp.tool()
async def xml_to_csv(filename: str, csv_filename: str = None, row_xpath: str = ".//row", map_fields: Dict[str,str] = None) -> str:
    """
    Convert XML to CSV.
    - row_xpath: expression matching each row element
    - map_fields: mapping {csv_col: './childtag' or '@attr'}
    If map_fields is None, the first matched child's tags become columns.
    """
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: {filename} not found"
            if csv_filename is None:
                csv_filename = filename.rsplit(".",1)[0] + ".csv"
            csv_path = _safe_path(csv_filename)
            def _task():
                tree, root = _parse_tree_sync(p)
                rows = root.findall(row_xpath)
                if not rows:
                    return f"ERROR: no rows matched xpath {row_xpath}"
                # derive fields
                if map_fields:
                    headers = list(map_fields.keys())
                    records = []
                    for r in rows:
                        rec = {}
                        for col, expr in map_fields.items():
                            if expr.startswith("@"):
                                # attribute
                                rec[col] = r.get(expr[1:])
                            else:
                                # child tag
                                child = r.find(expr)
                                rec[col] = child.text if child is not None else ""
                        records.append(rec)
                else:
                    # infer from first row children tags
                    first = rows[0]
                    headers = [c.tag for c in list(first)]
                    records = []
                    for r in rows:
                        rec = {h: (r.find(h).text if r.find(h) is not None else "") for h in headers}
                        records.append(rec)
                # write CSV
                with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=headers)
                    writer.writeheader()
                    for rec in records:
                        writer.writerow(rec)
                return f"Wrote CSV to {csv_path.name} with {len(records)} rows"
            res = await loop.run_in_executor(io_executor, _task)
            return res
        except Exception as e:
            logger.exception("xml_to_csv failed")
            return f"ERROR: {e}"

@mcp.tool()
async def validate_xml(filename: str, xsd_content: str = None) -> str:
    """
    Validate XML against an XSD string if lxml is available.
    If no XSD provided, only parse for well-formedness.
    """
    async with xml_semaphore:
        loop = asyncio.get_event_loop()
        try:
            p = _safe_path(filename)
            if not p.exists():
                return f"ERROR: {filename} not found"
            def _task():
                if LXML_AVAILABLE:
                    doc = LET.parse(str(p))
                    if xsd_content:
                        schema_root = LET.XML(xsd_content)
                        schema = LET.XMLSchema(schema_root)
                        valid = schema.validate(doc)
                        return "VALID" if valid else "INVALID: " + str(schema.error_log)
                    else:
                        # check well-formedness already done by parse
                        return "WELL-FORMED"
                else:
                    # stdlib: parse to check well-formed
                    ET.parse(str(p))
                    return "WELL-FORMED (lxml not available for XSD validation)"
            return await loop.run_in_executor(io_executor, _task)
        except Exception as e:
            logger.exception("validate_xml failed")
            return f"ERROR: {e}"


# ======================================================
# Resource (async-safe)
# ======================================================
@mcp.resource("xml://data")
def xml_directory_listing() -> List[str]:
    try:
        return [entry.name for entry in XML_DIR.iterdir() if entry.is_file() and entry.suffix.lower() == ".xml"]
    except Exception as e:
        logger.exception("xml_directory_listing failed")
        return []

# ======================================================
# Prompt (for LLM use)
# ======================================================
@mcp.prompt("summarize_xml")
def summarize_xml_prompt(xml_content: str):
    return [
        HumanMessage(
            content=(
                "You are an XML summarizer. Given this XML content:\n\n"
                f"{xml_content}\n\n"
                "Summarize its structure and data in 3 concise sentences."
            )
        )
    ]


# ======================================================
# Run Server (streamable_http as you used)
# ======================================================
if __name__ == "__main__":
    # Use streamable_http transport (external client connects via HTTP/WS)
    mcp.run(transport="stdio")
