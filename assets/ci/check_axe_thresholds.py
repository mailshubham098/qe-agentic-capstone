#!/usr/bin/env python3
"""
check_axe_thresholds.py — enforce the accessibility quality gates (WF14).

Reads an axe-core JSON report (as written by `axe --save`, which may be a single
object or an array of per-URL results) and enforces:

    NFR-017  critical-impact violations  == 0    (blocking)
    NFR-020  controls without a name     == 0    (blocking, via the 'label' rule)
    NFR-018  serious-impact violations   <= 5    (warn)

A violation in axe carries `nodes`; one rule can fail on many nodes. This script
counts NODES, not rules, because five unlabelled inputs are five defects, not one.

Usage
    python3 check_axe_thresholds.py --report evidence/WF14/axe_report.json \
        --max-critical 0 --max-serious 5
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

BLOCKING_RULES = {"label", "image-alt", "button-name", "link-name", "aria-input-field-name"}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", required=True)
    ap.add_argument("--max-critical", type=int, default=0)
    ap.add_argument("--max-serious", type=int, default=5)
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    path = pathlib.Path(args.report)

    if not path.exists():
        print(
            f"::error title=NFR-017::axe report not found at {path} — the scan did not run",
            file=sys.stderr,
        )
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error title=NFR-017::axe report is not valid JSON: {exc}", file=sys.stderr)
        return 2

    runs = data if isinstance(data, list) else [data]
    if not runs:
        print("::error title=NFR-017::axe report contained no results", file=sys.stderr)
        return 2

    by_impact: collections.Counter[str] = collections.Counter()
    by_rule: collections.Counter[str] = collections.Counter()
    detail: list[tuple[str, str, str, int]] = []
    pages_scanned = 0

    for run in runs:
        if not isinstance(run, dict):
            continue
        pages_scanned += 1
        url = run.get("url", "unknown")
        for violation in run.get("violations", []):
            rule = violation.get("id", "unknown")
            impact = (violation.get("impact") or "unknown").lower()
            node_count = len(violation.get("nodes", [])) or 1
            by_impact[impact] += node_count
            by_rule[rule] += node_count
            detail.append((url, rule, impact, node_count))

    if pages_scanned == 0:
        print("::error title=NFR-017::no page results present in the axe report", file=sys.stderr)
        return 2

    critical = by_impact.get("critical", 0)
    serious = by_impact.get("serious", 0)
    moderate = by_impact.get("moderate", 0)
    minor = by_impact.get("minor", 0)
    blocking_rule_hits = sum(count for rule, count in by_rule.items() if rule in BLOCKING_RULES)

    print(f"pages scanned : {pages_scanned}")
    print(f"critical      : {critical}   (NFR-017 threshold <= {args.max_critical})")
    print(f"serious       : {serious}   (NFR-018 threshold <= {args.max_serious}, warn)")
    print(f"moderate      : {moderate}")
    print(f"minor         : {minor}")
    print(f"naming rules  : {blocking_rule_hits}   (NFR-020 threshold <= 0)")

    if detail:
        print("\nviolations by page and rule:")
        for url, rule, impact, count in sorted(detail, key=lambda r: (-r[3], r[1])):
            print(f"  {impact:9s} {rule:32s} {count:3d} node(s)  {url}")

    failed = False

    if critical > args.max_critical:
        print(
            f"::error title=NFR-017::{critical} critical accessibility violation node(s); "
            f"threshold is {args.max_critical}",
            file=sys.stderr,
        )
        failed = True

    if blocking_rule_hits > 0:
        offending = ", ".join(f"{r}={c}" for r, c in by_rule.items() if r in BLOCKING_RULES)
        print(
            f"::error title=NFR-020::accessible-name violations must be zero ({offending})",
            file=sys.stderr,
        )
        failed = True

    if serious > args.max_serious:
        # Warn only — recorded, does not fail the build.
        print(
            f"::warning title=NFR-018::{serious} serious violation node(s) exceeds the "
            f"tolerance of {args.max_serious} and must not increase",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
