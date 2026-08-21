#!/usr/bin/env python3
"""
build_gate_payload.py — assemble the consolidated release-gate payload.

Collects the measured outcome of every stage from the evidence directory, joins
it to the declared thresholds in nfr_catalog.csv, and hands the ReleaseGateAgent
a single structured view of the build.

The agent explains and recommends. This script — and the pipeline step that
follows it — is what actually enforces. That separation is deliberate: a gate
whose outcome depends on a model's prose is not a gate.

Usage
    python3 build_gate_payload.py --evidence-dir evidence \
        --nfr-catalog assets/sample_data/nfr_catalog.csv \
        --output payload.json
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--nfr-catalog", required=True)
    ap.add_argument("--output", required=True)
    return ap.parse_args()


def load_nfr_catalog(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        print(f"warning: NFR catalogue not found at {path}", file=sys.stderr)
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def summarise_junit(root: pathlib.Path) -> dict:
    total = failures = errors = skipped = 0
    p1_total = p1_failed = 0
    failed_tests: list[str] = []

    for xml_path in sorted(root.rglob("TEST-*.xml")):
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue
        for case in tree.iter("testcase"):
            total += 1
            name = f"{case.get('classname', '')}#{case.get('name', '')}"
            # P1 cases are tagged in the method name by convention (see §1 of the
            # standards: tc<n>_<behaviour>, with P1 cases listed in the context).
            is_p1 = "p1" in name.lower()
            if is_p1:
                p1_total += 1
            failed = case.find("failure") is not None or case.find("error") is not None
            if failed:
                if case.find("error") is not None:
                    errors += 1
                else:
                    failures += 1
                failed_tests.append(name)
                if is_p1:
                    p1_failed += 1
            if case.find("skipped") is not None:
                skipped += 1

    executed = total - skipped
    pass_rate = ((executed - failures - errors) / executed * 100.0) if executed else 0.0
    p1_pass_rate = ((p1_total - p1_failed) / p1_total * 100.0) if p1_total else 100.0

    return {
        "totalTests": total,
        "executed": executed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passRatePct": round(pass_rate, 2),
        "p1Total": p1_total,
        "p1Failed": p1_failed,
        "p1PassRatePct": round(p1_pass_rate, 2),
        "failedTests": failed_tests[:50],
    }


def read_json(path: pathlib.Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def read_csv_rows(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.evidence_dir)

    functional = summarise_junit(root)

    requirement_report = read_json(root / "WF02/requirement_quality_report.json")
    triage_report = read_json(root / "WF08/triage_report.json")
    prediction_report = read_json(root / "WF09/prediction_report.json")
    chaos_journal = read_json(root / "WF13/chaos_journal.json")
    axe_report = read_json(root / "WF14/axe_report.json")
    jmeter_rows = read_csv_rows(root / "WF12/jmeter_summary.csv")

    # Requirement quality
    req_summary = None
    if isinstance(requirement_report, dict):
        reqs = requirement_report.get("requirements", [])
        scores = [r.get("qualityScore", 0) for r in reqs]
        untestable = sum(
            1
            for r in reqs
            for c in r.get("criteria", [])
            if c.get("testabilityVerdict") == "UNTESTABLE"
        )
        req_summary = {
            "requirementsAssessed": len(reqs),
            "meanQualityScore": round(sum(scores) / len(scores), 1) if scores else None,
            "untestableCriteria": untestable,
        }

    # Accessibility
    a11y_summary = None
    if axe_report is not None:
        runs = axe_report if isinstance(axe_report, list) else [axe_report]
        counts: dict[str, int] = {}
        for run in runs:
            if not isinstance(run, dict):
                continue
            for violation in run.get("violations", []):
                impact = (violation.get("impact") or "unknown").lower()
                counts[impact] = counts.get(impact, 0) + (len(violation.get("nodes", [])) or 1)
        a11y_summary = {
            "pagesScanned": len([r for r in runs if isinstance(r, dict)]),
            "critical": counts.get("critical", 0),
            "serious": counts.get("serious", 0),
            "moderate": counts.get("moderate", 0),
            "minor": counts.get("minor", 0),
        }

    # Performance
    perf_summary = None
    if jmeter_rows:
        perf_summary = {
            row["gate"]: {
                "metric": row.get("metric"),
                "actual": row.get("actual"),
                "threshold": row.get("threshold"),
                "result": row.get("result"),
            }
            for row in jmeter_rows
            if row.get("gate", "").startswith("NFR")
        }

    # Resilience
    resilience_summary = None
    if isinstance(chaos_journal, dict):
        resilience_summary = {
            "status": chaos_journal.get("status"),
            "deviated": chaos_journal.get("deviated"),
            "duration": chaos_journal.get("duration"),
        }

    # Open S1 defects, as classified by the triage agent
    open_s1 = 0
    triage_summary = None
    if isinstance(triage_report, dict):
        defects = triage_report.get("defects", triage_report.get("findings", []))
        if isinstance(defects, list):
            open_s1 = sum(
                1
                for d in defects
                if str(d.get("severity", "")).upper() == "S1"
                and str(d.get("status", "NEW")).upper() not in {"CLOSED", "VERIFIED"}
                # A broken test script is suite maintenance, not a product defect.
                and str(d.get("rootCauseCategory", "")).upper() != "TEST_SCRIPT"
            )
            triage_summary = {
                "defectsTriaged": len(defects),
                "openS1": open_s1,
                "bySeverity": {
                    sev: sum(1 for d in defects if str(d.get("severity", "")).upper() == sev)
                    for sev in ("S1", "S2", "S3", "S4")
                },
            }

    payload = {
        "task": (
            "Evaluate every declared quality gate against the measured evidence. "
            "For each gate state PASS, FAIL or WARN with the actual value, the "
            "threshold and the evidence artefact you relied on. Then give one "
            "consolidated verdict and a recommendation to the Quality Engineer. "
            "Return openS1Defects as an integer field."
        ),
        "declaredGates": [
            {
                "gateId": row.get("gate_id"),
                "gateName": row.get("gate_name"),
                "dimension": row.get("dimension"),
                "metric": row.get("metric"),
                "threshold": row.get("threshold"),
                "operator": row.get("threshold_operator"),
                "blocking": row.get("blocking"),
                "stage": row.get("pipeline_stage"),
            }
            for row in load_nfr_catalog(pathlib.Path(args.nfr_catalog))
        ],
        "measured": {
            "functional": functional,
            "requirementQuality": req_summary,
            "performance": perf_summary,
            "accessibility": a11y_summary,
            "resilience": resilience_summary,
            "triage": triage_summary,
        },
        "openS1Defects": open_s1,
        "advisory": {
            "defectPrediction": prediction_report,
        },
    }

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"gate payload written to {out}")
    print(
        f"functional: {functional['executed']} executed, "
        f"{functional['failures'] + functional['errors']} failed, "
        f"pass rate {functional['passRatePct']}%"
    )
    print(f"open S1 defects: {open_s1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
