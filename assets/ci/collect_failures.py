#!/usr/bin/env python3
"""
collect_failures.py — build the triage payload for the DefectTriageAgent (WF08).

Walks the evidence directory, parses every JUnit XML report, and emits one JSON
payload describing each failure with a NORMALISED failure signature.

Why normalise?
    Duplicate detection (qe_standards_and_dod.md §5) compares failure signatures.
    Raw stack traces contain timestamps, object hashes, ports, build numbers and
    generated identifiers, so two instances of the same defect never match
    literally. Stripping that volatile detail is what makes duplicate detection
    work at all.

Usage
    python3 collect_failures.py --evidence-dir evidence --output payload.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

# Volatile fragments replaced before comparison, in order.
NORMALISERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"), "<TIMESTAMP>"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"0x[0-9a-fA-F]+"), "<ADDR>"),
    (re.compile(r"@[0-9a-fA-F]{6,}"), "@<HASH>"),
    (re.compile(r"\blocalhost:\d+\b"), "localhost:<PORT>"),
    (re.compile(r"https?://[^\s\"')]+"), "<URL>"),
    (re.compile(r"\bbuild[- _]?#?\d+\b", re.IGNORECASE), "build <N>"),
    (re.compile(r"\b\d{6,}\b"), "<BIGNUM>"),
    (re.compile(r"(?<=Session ID: )\S+"), "<SESSION>"),
    (re.compile(r"\s+"), " "),
]

# Maps a test's package/class hints to the component vocabulary used by the
# squad routing table in qe_standards_and_dod.md §5.
COMPONENT_HINTS: list[tuple[str, str]] = [
    ("transfer", "transfer"),
    ("payee", "payee"),
    ("billpay", "payee"),
    ("statement", "statement"),
    ("loan", "loan"),
    ("checkout", "checkout"),
    ("cart", "checkout"),
    ("basket", "checkout"),
    ("catalog", "catalogue"),
    ("catalogue", "catalogue"),
    ("login", "login"),
    ("auth", "login"),
    ("session", "login"),
    ("visit", "visit"),
    ("owner", "owner"),
    ("pet", "pet"),
    ("vet", "vet"),
    ("leave", "leave"),
    ("employee", "pim"),
    ("a11y", "checkout"),
    ("accessib", "checkout"),
    ("perf", "api-owners"),
    ("resilience", "visit"),
    ("chaos", "visit"),
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--output", required=True)
    return ap.parse_args()


def normalise(text: str) -> str:
    out = text.strip()
    for pattern, replacement in NORMALISERS:
        out = pattern.sub(replacement, out)
    return out.strip()[:400]


def infer_component(classname: str, testname: str) -> str:
    haystack = f"{classname} {testname}".lower()
    for needle, component in COMPONENT_HINTS:
        if needle in haystack:
            return component
    return "unknown"


def infer_test_type(classname: str) -> str:
    lowered = classname.lower()
    if "a11y" in lowered or "accessib" in lowered:
        return "ACCESSIBILITY"
    if "perf" in lowered or "jmeter" in lowered:
        return "PERFORMANCE"
    if "resilience" in lowered or "chaos" in lowered:
        return "RESILIENCE"
    if ".api." in lowered or "restassured" in lowered:
        return "INTEGRATION"
    return "FUNCTIONAL"


def extract_zephyr_key(testname: str) -> str | None:
    # Convention: tc204_transferRejectsNegativeAmount -> QEC-T204
    match = re.match(r"tc(\d+)_", testname)
    return f"QEC-T{match.group(1)}" if match else None


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.evidence_dir)

    if not root.exists():
        print(f"warning: evidence directory {root} not found", file=sys.stderr)

    failures: list[dict] = []
    reports_seen = 0

    for xml_path in sorted(root.rglob("TEST-*.xml")):
        reports_seen += 1
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError as exc:
            print(f"warning: unparseable report {xml_path}: {exc}", file=sys.stderr)
            continue

        for case in tree.iter("testcase"):
            classname = case.get("classname", "")
            testname = case.get("name", "")
            for tag in ("failure", "error"):
                node = case.find(tag)
                if node is None:
                    continue
                raw = (node.get("message") or "") + "\n" + (node.text or "")
                failures.append(
                    {
                        "testClass": classname,
                        "testMethod": testname,
                        "zephyrKey": extract_zephyr_key(testname),
                        "outcome": tag.upper(),
                        "exceptionType": node.get("type", "unknown"),
                        "rawMessage": raw.strip()[:2000],
                        "failureSignature": normalise(raw),
                        "component": infer_component(classname, testname),
                        "testType": infer_test_type(classname),
                        "durationSeconds": case.get("time"),
                        "source": str(xml_path.relative_to(root)) if xml_path.is_relative_to(root) else str(xml_path),
                    }
                )

    # Group identical normalised signatures so the agent sees the true cardinality.
    grouped: dict[str, dict] = {}
    for failure in failures:
        key = f"{failure['component']}::{failure['failureSignature']}"
        if key in grouped:
            grouped[key]["occurrences"] += 1
            grouped[key]["affectedTests"].append(
                f"{failure['testClass']}#{failure['testMethod']}"
            )
        else:
            entry = dict(failure)
            entry["occurrences"] = 1
            entry["affectedTests"] = [f"{failure['testClass']}#{failure['testMethod']}"]
            grouped[key] = entry

    payload = {
        "task": "triage each failure: classify severity, priority, defectType, "
                "rootCauseCategory, assign a squad, and propose duplicates",
        "reportsParsed": reports_seen,
        "totalFailures": len(failures),
        "distinctSignatures": len(grouped),
        "failures": list(grouped.values()),
    }

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        f"parsed {reports_seen} report(s); {len(failures)} failure(s) "
        f"collapsed into {len(grouped)} distinct signature(s) -> {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
