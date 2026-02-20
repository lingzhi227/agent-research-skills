#!/usr/bin/env python3
"""Scan and verify hypertarget/hyperlink numeric references in LaTeX files.

Two modes:
  --scan: Report all \\hypertarget and \\hyperlink usage in a .tex file
  --verify: Cross-reference targets vs links for integrity

Self-contained: uses only stdlib.

Extracted from data-to-paper's ref_numeric_values.py.

Usage:
    python ref_numeric_values.py --scan main.tex --output report.json
    python ref_numeric_values.py --verify main.tex --code-output results.txt
    python ref_numeric_values.py --scan main.tex
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional


TARGET = r'\hypertarget'
LINK = r'\hyperlink'


def get_numeric_value_pattern(must_follow: Optional[str] = None,
                               allow_commas: bool = True) -> str:
    """Get a regex pattern for numeric values."""
    prefix = ""
    if must_follow is not None:
        prefix = f"(?<={must_follow})"
    if allow_commas:
        pattern = r'(?:[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?:e[-+]?\d+)?|\d{1,3}(?:,\d{3})+)(?!\d)'
    else:
        pattern = r'[-+]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    return prefix + pattern


NUMERIC_PATTERN = get_numeric_value_pattern(
    must_follow=r'[$,{<=\s\n\(\[]', allow_commas=True
)


@dataclass
class ReferencedValue:
    """A numeric value with a reference label."""
    value: str
    label: Optional[str] = None
    is_target: bool = True
    line_num: int = 0

    @property
    def command(self) -> str:
        return TARGET if self.is_target else LINK


def get_hyperlink_pattern(is_target: bool = False) -> str:
    """Get regex pattern for \\hypertarget or \\hyperlink commands."""
    command = re.escape(TARGET if is_target else LINK)
    return rf'{command}\{{(?P<reference>[^}}]*)\}}\{{(?P<value>[^}}]*)\}}'


def find_references(text: str, is_targets: bool = False) -> list[ReferencedValue]:
    """Find all hypertarget or hyperlink references in text."""
    pattern = get_hyperlink_pattern(is_targets)
    refs = []
    for i, line in enumerate(text.splitlines(), 1):
        for match in re.finditer(pattern, line):
            refs.append(ReferencedValue(
                value=match.group('value'),
                label=match.group('reference'),
                is_target=is_targets,
                line_num=i,
            ))
    return refs


def find_numeric_values(text: str, remove_hyperlinks: bool = True) -> list[str]:
    """Find all unreferenced numeric values in text."""
    text = ' ' + text + ' '
    if remove_hyperlinks:
        text = re.sub(get_hyperlink_pattern(is_target=False), '', text)
        text = re.sub(get_hyperlink_pattern(is_target=True), '', text)
    return re.findall(NUMERIC_PATTERN, text)


def replace_hyperlinks_with_values(text: str, is_targets: bool = False) -> str:
    """Replace all hypertarget/hyperlink commands with just their values."""
    def replace_match(match):
        return match.group('value')
    pattern = get_hyperlink_pattern(is_targets)
    return re.sub(pattern, replace_match, text)


def scan_file(tex_content: str) -> dict:
    """Scan a .tex file and report all hypertarget/hyperlink usage."""
    targets = find_references(tex_content, is_targets=True)
    links = find_references(tex_content, is_targets=False)
    unreferenced = find_numeric_values(tex_content)

    return {
        "hypertargets": [asdict(t) for t in targets],
        "hyperlinks": [asdict(l) for l in links],
        "target_count": len(targets),
        "link_count": len(links),
        "target_labels": sorted(set(t.label for t in targets if t.label)),
        "link_labels": sorted(set(l.label for l in links if l.label)),
        "unreferenced_numeric_values": unreferenced[:50],
        "unreferenced_count": len(unreferenced),
    }


def verify_integrity(tex_content: str, code_output: str = "") -> dict:
    """Verify cross-reference integrity between targets and links."""
    targets = find_references(tex_content, is_targets=True)
    links = find_references(tex_content, is_targets=False)

    target_labels = {t.label for t in targets if t.label}
    link_labels = {l.label for l in links if l.label}

    # Find mismatches
    unresolved_links = link_labels - target_labels
    unused_targets = target_labels - link_labels

    # Check value consistency (same label should have same value)
    target_values = {}
    for t in targets:
        if t.label:
            target_values[t.label] = t.value

    link_values = {}
    for l in links:
        if l.label:
            link_values[l.label] = l.value

    value_mismatches = []
    for label in target_labels & link_labels:
        tv = target_values.get(label, "")
        lv = link_values.get(label, "")
        if tv and lv and tv != lv:
            value_mismatches.append({
                "label": label,
                "target_value": tv,
                "link_value": lv,
            })

    # Check against code output if provided
    code_values = {}
    if code_output:
        for line in code_output.splitlines():
            m = re.search(get_hyperlink_pattern(is_target=True), line)
            if m:
                code_values[m.group('reference')] = m.group('value')

    code_mismatches = []
    if code_values:
        for label, code_val in code_values.items():
            tex_val = target_values.get(label)
            if tex_val and tex_val != code_val:
                code_mismatches.append({
                    "label": label,
                    "code_value": code_val,
                    "tex_value": tex_val,
                })

    result = {
        "total_targets": len(targets),
        "total_links": len(links),
        "unresolved_links": sorted(unresolved_links),
        "unused_targets": sorted(unused_targets),
        "value_mismatches": value_mismatches,
        "code_mismatches": code_mismatches,
        "integrity_ok": (
            len(unresolved_links) == 0
            and len(value_mismatches) == 0
            and len(code_mismatches) == 0
        ),
    }
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Scan and verify hypertarget/hyperlink references in LaTeX"
    )
    parser.add_argument("tex_file", help="LaTeX file to analyze")
    parser.add_argument("--scan", action="store_true",
                        help="Scan mode: report all hypertarget/hyperlink usage")
    parser.add_argument("--verify", action="store_true",
                        help="Verify mode: check cross-reference integrity")
    parser.add_argument("--code-output", help="Code output file for cross-referencing")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    if not args.scan and not args.verify:
        args.scan = True  # Default to scan mode

    if not os.path.exists(args.tex_file):
        print(f"Error: {args.tex_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.tex_file, encoding="utf-8", errors="replace") as f:
        tex_content = f.read()

    code_output = ""
    if args.code_output and os.path.exists(args.code_output):
        with open(args.code_output, encoding="utf-8", errors="replace") as f:
            code_output = f.read()

    if args.scan:
        result = scan_file(tex_content)
        print(f"Targets: {result['target_count']}, Links: {result['link_count']}, "
              f"Unreferenced numbers: {result['unreferenced_count']}", file=sys.stderr)
    else:
        result = verify_integrity(tex_content, code_output)
        status = "OK" if result["integrity_ok"] else "ISSUES FOUND"
        print(f"Integrity: {status}", file=sys.stderr)
        if result["unresolved_links"]:
            print(f"  Unresolved links: {result['unresolved_links']}", file=sys.stderr)
        if result["value_mismatches"]:
            print(f"  Value mismatches: {len(result['value_mismatches'])}", file=sys.stderr)
        if result["code_mismatches"]:
            print(f"  Code mismatches: {len(result['code_mismatches'])}", file=sys.stderr)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.verify and not result["integrity_ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
