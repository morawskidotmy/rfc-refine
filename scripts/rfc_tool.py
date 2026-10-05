#!/usr/bin/env python3
"""
RFC Tool - Search, fetch, inspect, and analyze IETF RFCs from rfc-editor.org and datatracker.ietf.org.
Part of the rfc-refine skill.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "rfcs"
USER_AGENT = "rfc-refine-skill/1.0 (+https://www.rfc-editor.org)"

KEYWORDS = [
    "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
    "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED",
    "MAY", "OPTIONAL"
]
KEYWORD_PATTERN = re.compile(
    r"\b(MUST(?:\s+NOT)?|REQUIRED|SHALL(?:\s+NOT)?|SHOULD(?:\s+NOT)?|RECOMMENDED|NOT\s+RECOMMENDED|MAY|OPTIONAL)\b"
)


def normalize_rfc_id(rfc_input: str) -> tuple[str, int]:
    """Normalize '9110', 'rfc9110', 'RFC 9110' into ('rfc9110', 9110)."""
    match = re.search(r"(\d+)", rfc_input)
    if not match:
        raise ValueError(f"Invalid RFC identifier: {rfc_input}")
    num = int(match.group(1))
    return f"rfc{num}", num


def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Error: 404 Not Found at {url}")
        sys.exit(f"HTTP Error {e.code}: {e.reason} for {url}")
    except Exception as e:
        sys.exit(f"Network error accessing {url}: {e}")


def get_rfc_text(rfc_num: int, cache_dir: Path, force: bool = False) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"rfc{rfc_num}.txt"
    if cache_file.exists() and not force:
        return cache_file.read_text(encoding="utf-8", errors="replace")

    url = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.txt"
    text = http_get(url)
    cache_file.write_text(text, encoding="utf-8")
    return text


def cmd_get(args):
    _, num = normalize_rfc_id(args.rfc)
    cache_dir = Path(args.cache_dir) if args.cache_dir else DEFAULT_CACHE_DIR
    fmt = args.format.lower()

    if fmt == "txt":
        text = get_rfc_text(num, cache_dir, force=args.force)
        cache_file = cache_dir / f"rfc{num}.txt"
        print(f"RFC {num} saved to {cache_file} ({len(text)} bytes, {text.count(chr(10))} lines)")
        if args.print:
            print(text)
    elif fmt in ("html", "xml"):
        url = f"https://www.rfc-editor.org/rfc/rfc{num}.{fmt}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"rfc{num}.{fmt}"
        if cache_file.exists() and not args.force:
            content = cache_file.read_text(encoding="utf-8", errors="replace")
        else:
            content = http_get(url)
            cache_file.write_text(content, encoding="utf-8")
        print(f"RFC {num} ({fmt}) saved to {cache_file} ({len(content)} bytes)")
        if args.print:
            print(content)


def cmd_search(args):
    query = args.query.strip()
    encoded = urllib.parse.quote(query)
    limit = args.limit
    url = f"https://datatracker.ietf.org/api/v1/doc/document/?name__startswith=rfc&title__icontains={encoded}&format=json&limit={limit}"
    raw = http_get(url)
    try:
        data = json.loads(raw)
    except Exception as e:
        sys.exit(f"Failed to parse datatracker response: {e}")

    total = data.get("meta", {}).get("total_count", 0)
    objects = data.get("objects", [])
    print(f"Found {total} RFC(s) matching '{query}' (showing top {len(objects)}):")
    print("-" * 75)
    for obj in objects:
        name = obj.get("name", "").upper()
        title = obj.get("title", "No title")
        pages = obj.get("pages", "?")
        std_level = obj.get("std_level")
        level_name = std_level.split("/")[-2] if std_level else "Unknown"
        print(f"[{name}] {title}")
        print(f"    Status: {level_name} | Pages: {pages} | URL: https://www.rfc-editor.org/rfc/{obj.get('name')}.html")
    print("-" * 75)


def cmd_info(args):
    _, num = normalize_rfc_id(args.rfc)
    cache_dir = Path(args.cache_dir) if args.cache_dir else DEFAULT_CACHE_DIR
    text = get_rfc_text(num, cache_dir)

    # Parse header lines for metadata
    header_lines = text[:4000].splitlines()[:60]
    obsoletes = []
    obsoleted_by = []
    updates = []
    updated_by = []
    category = "Unknown"
    std = None

    for line in header_lines:
        s = line.strip()
        if s.startswith("Obsoletes:"):
            obsoletes.append(s.replace("Obsoletes:", "").strip())
        elif s.startswith("Updates:"):
            updates.append(s.replace("Updates:", "").strip())
        elif s.startswith("Category:"):
            category = s.replace("Category:", "").strip()
        elif s.startswith("STD:"):
            std = s.replace("STD:", "").strip()

    # Query datatracker API for live status
    dt_url = f"https://datatracker.ietf.org/api/v1/doc/document/rfc{num}/?format=json"
    dt_meta = {}
    try:
        dt_meta = json.loads(http_get(dt_url))
    except Exception:
        pass

    # Check errata
    errata_url = f"https://www.rfc-editor.org/errata_search.php?rfc={num}"
    errata_html = ""
    errata_count = 0
    try:
        errata_html = http_get(errata_url)
        errata_count = len(re.findall(r"Errata ID:\s*<a href=", errata_html))
    except Exception:
        pass

    print(f"=== RFC {num} Metadata & Lifecycle ===")
    title = dt_meta.get("title", "(Use header text)")
    print(f"Title:        {title}")
    print(f"Category:     {category}")
    if std:
        print(f"Standard #:   STD {std}")
    if obsoletes:
        print(f"Obsoletes:    {', '.join(obsoletes)}")
    if updates:
        print(f"Updates:      {', '.join(updates)}")

    # Check live datatracker relationship fields
    if dt_meta:
        if dt_meta.get("obsoleted_by"):
            print(f"OBSOLETED BY: {dt_meta['obsoleted_by']} (DO NOT IMPLEMENT FOR NEW SYSTEMS)")
        if dt_meta.get("updated_by"):
            print(f"Updated by:   {dt_meta['updated_by']}")

    print(f"Official URL: https://www.rfc-editor.org/rfc/rfc{num}.html")
    print(f"Errata URL:   https://www.rfc-editor.org/errata/rfc{num} (Found ~{errata_count} reported/verified errata)")
    if errata_count > 0:
        print("  WARNING: Active errata exist! Review errata before finalizing implementation.")


def extract_normative_sentences(text: str, filter_level: str = "ALL"):
    paragraphs = text.split("\n\n")
    section_regex = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+([A-Z0-9].*)$")
    target_pattern = KEYWORD_PATTERN
    if filter_level != "ALL":
        target_pattern = re.compile(rf"\b({re.escape(filter_level)})\b")

    current_section = "Overview"
    results = []
    line_offset = 1

    for para in paragraphs:
        para_lines = para.splitlines()
        num_lines = len(para_lines)
        if not para_lines:
            line_offset += 1
            continue

        first_line = para_lines[0].strip()
        sec_match = section_regex.match(first_line)
        if sec_match and len(first_line) < 80:
            current_section = f"Section {sec_match.group(1)} {sec_match.group(2)}"

        # Unfold lines in the paragraph
        unfolded = " ".join(line.strip() for line in para_lines if line.strip())

        # Skip RFC 2119 definition boilerplate
        if 'The key words "MUST"' in unfolded or ('RFC 2119' in unfolded and 'key words' in unfolded):
            line_offset += num_lines + 1
            continue

        # Split into approximate sentences
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", unfolded)
        for s in sentences:
            found = target_pattern.findall(s)
            if found:
                unique_kws = sorted(list(set(found)), key=lambda k: (-len(k), k))
                results.append({
                    "line_no": line_offset,
                    "section": current_section,
                    "keywords": unique_kws,
                    "sentence": s.strip()
                })

        line_offset += num_lines + 1

    return results


def cmd_normative(args):
    _, num = normalize_rfc_id(args.rfc)
    cache_dir = Path(args.cache_dir) if args.cache_dir else DEFAULT_CACHE_DIR
    text = get_rfc_text(num, cache_dir)

    filter_level = args.level.upper() if args.level else "ALL"
    matches = extract_normative_sentences(text, filter_level)

    try:
        print(f"=== Normative Statements in RFC {num} ({len(matches)} matching '{filter_level}') ===")
        for m in matches:
            kws = ", ".join(m["keywords"])
            print(f"~Line {m['line_no']:5d} [{m['section']} | {kws}]:")
            print(f"    {m['sentence']}")
            print()
    except BrokenPipeError:
        pass


def cmd_abnf(args):
    _, num = normalize_rfc_id(args.rfc)
    cache_dir = Path(args.cache_dir) if args.cache_dir else DEFAULT_CACHE_DIR
    text = get_rfc_text(num, cache_dir)
    lines = text.splitlines()

    # Rule pattern: name = ... or name =/ ... (allowing arbitrary leading indentation)
    abnf_def = re.compile(r"^\s*([a-zA-Z][a-zA-Z0-9\-]*)\s*=(?:/)?\s*(.+)$")
    current_section = "General"
    section_regex = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+([A-Z0-9].*)$")

    rules = []
    current_rule = None

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        sec_match = section_regex.match(stripped)
        if sec_match and len(stripped) < 80:
            current_section = f"Section {sec_match.group(1)} {sec_match.group(2)}"

        match = abnf_def.match(line)
        if match:
            # Avoid matching equality in code or prose like 'foo == bar' or text
            rhs = match.group(2).strip()
            if not rhs.startswith("="):
                if current_rule:
                    rules.append(current_rule)
                current_rule = {
                    "name": match.group(1),
                    "section": current_section,
                    "line_no": idx,
                    "lines": [line.rstrip()]
                }
                continue
        if current_rule:
            # Continuation line: indented further or starts with whitespace, doesn't look like empty page break
            if (line.startswith("   ") or line.startswith("\t")) and stripped:
                current_rule["lines"].append(line.rstrip())
            elif not stripped:
                continue
            else:
                rules.append(current_rule)
                current_rule = None

    if current_rule:
        rules.append(current_rule)

    try:
        print(f"=== Extracted {len(rules)} ABNF Rule(s) from RFC {num} ===")
        for r in rules:
            print(f"# {r['section']} (Line {r['line_no']}):")
            for l in r["lines"]:
                print(f"  {l}")
            print()
    except BrokenPipeError:
        pass


def cmd_matrix(args):
    _, num = normalize_rfc_id(args.rfc)
    cache_dir = Path(args.cache_dir) if args.cache_dir else DEFAULT_CACHE_DIR
    text = get_rfc_text(num, cache_dir)

    matches = extract_normative_sentences(text, "ALL")

    try:
        print(f"# RFC {num} Conformance Matrix\n")
        print(f"Generated from RFC {num} normative statements. Use this checklist during implementation and refinement.\n")
        print("| Clause / Section | Level | Normative Requirement | Impl File & Line | Status | Verification Test |")
        print("| :--- | :---: | :--- | :--- | :---: | :--- |")
        for r in matches[:args.limit]:
            snippet = r["sentence"].replace("|", "\\|")
            if len(snippet) > 95:
                snippet = snippet[:92] + "..."
            kw_str = "/".join(r["keywords"])
            sec_parts = r["section"].split(" ", 2)
            sec_display = " ".join(sec_parts[:2]) if len(sec_parts) >= 2 else r["section"]
            print(f"| {sec_display} (L{r['line_no']}) | **{kw_str}** | {snippet} | `TODO` | Pending | `test_rfc{num}_sec...` |")
        if len(matches) > args.limit:
            print(f"\n*(Truncated: showing first {args.limit} of {len(matches)} normative requirements. Adjust with `--limit`)*")
    except BrokenPipeError:
        pass


def main():
    parser = argparse.ArgumentParser(description="RFC Tool for fetching, searching, inspecting, and analyzing RFCs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Fetch and cache an RFC")
    p_get.add_argument("rfc", help="RFC number (e.g. 9110, rfc9110)")
    p_get.add_argument("--format", choices=["txt", "html", "xml"], default="txt", help="Format to fetch")
    p_get.add_argument("--cache-dir", help="Custom cache directory")
    p_get.add_argument("--force", action="store_true", help="Force re-download")
    p_get.add_argument("--print", action="store_true", help="Print content to stdout")
    p_get.set_defaults(func=cmd_get)

    # search
    p_search = subparsers.add_parser("search", help="Search RFCs by title/topic on datatracker")
    p_search.add_argument("query", help="Search keywords (e.g. 'http cache', 'websocket', 'quic')")
    p_search.add_argument("--limit", type=int, default=10, help="Max results to return")
    p_search.set_defaults(func=cmd_search)

    # info
    p_info = subparsers.add_parser("info", help="Get RFC metadata, lifecycle status (updates/obsoleted), and errata")
    p_info.add_argument("rfc", help="RFC number (e.g. 9110)")
    p_info.add_argument("--cache-dir", help="Custom cache directory")
    p_info.set_defaults(func=cmd_info)

    # normative
    p_normative = subparsers.add_parser("normative", help="Extract RFC 2119/8174 normative statements (MUST, SHOULD, etc.)")
    p_normative.add_argument("rfc", help="RFC number (e.g. 9110)")
    p_normative.add_argument("--level", choices=["ALL", "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY", "RECOMMENDED"], default="ALL")
    p_normative.add_argument("--cache-dir", help="Custom cache directory")
    p_normative.set_defaults(func=cmd_normative)

    # abnf
    p_abnf = subparsers.add_parser("abnf", help="Extract ABNF grammar rules from an RFC")
    p_abnf.add_argument("rfc", help="RFC number (e.g. 9110)")
    p_abnf.add_argument("--cache-dir", help="Custom cache directory")
    p_abnf.set_defaults(func=cmd_abnf)

    # matrix
    p_matrix = subparsers.add_parser("matrix", help="Generate a Markdown Conformance Matrix checklist from RFC normative statements")
    p_matrix.add_argument("rfc", help="RFC number (e.g. 9110)")
    p_matrix.add_argument("--limit", type=int, default=50, help="Max rows to output")
    p_matrix.add_argument("--cache-dir", help="Custom cache directory")
    p_matrix.set_defaults(func=cmd_matrix)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
