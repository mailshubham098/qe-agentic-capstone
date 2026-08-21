#!/usr/bin/env python3
"""
check_jmeter_thresholds.py — enforce the performance quality gates (WF12).

Reads the JJTL/CSV result file produced by a JMeter run, computes p95 latency,
error rate and throughput, writes a summary CSV as evidence, and exits non-zero
when a blocking threshold is breached.

Gates enforced (see assets/sample_data/nfr_catalog.csv):
    NFR-008  p95 response time      <= 1200 ms
    NFR-009  error rate             <= 1 %
    NFR-010  throughput             >= 40 req/s

Why compute this here rather than trust JMeter's own assertion?
    The jmeter-maven-plugin can fail on error rate, but does not gate p95 or
    throughput. Deriving all three from the raw samples keeps one definition of
    "pass" and produces the evidence artefact the demo requires.

Usage
    python3 check_jmeter_thresholds.py \
        --results-dir target/jmeter/results \
        --p95-ms 1200 --error-rate-pct 1 --min-throughput 40 \
        --output evidence/WF12/jmeter_summary.csv
"""
from __future__ import annotations

import argparse
import csv
import math
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--p95-ms", type=float, default=1200.0)
    ap.add_argument("--error-rate-pct", type=float, default=1.0)
    ap.add_argument("--min-throughput", type=float, default=40.0)
    ap.add_argument("--output", required=True)
    ap.add_argument(
        "--label",
        default=None,
        help="Only evaluate samples with this JMeter label (default: all samples)",
    )
    return ap.parse_args()


def find_result_files(results_dir: pathlib.Path) -> list[pathlib.Path]:
    if not results_dir.exists():
        return []
    files = sorted(
        [p for p in results_dir.rglob("*.csv") if p.is_file()]
        + [p for p in results_dir.rglob("*.jtl") if p.is_file()]
    )
    return files


def percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile, matching how JMeter reports p95."""
    if not sorted_values:
        return float("nan")
    rank = math.ceil(pct / 100.0 * len(sorted_values))
    rank = max(1, min(rank, len(sorted_values)))
    return sorted_values[rank - 1]


def load_samples(paths: list[pathlib.Path], label: str | None):
    elapsed: list[float] = []
    timestamps: list[int] = []
    total = 0
    errors = 0

    for path in paths:
        with path.open(newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or "elapsed" not in reader.fieldnames:
                # Not a raw sample file (could be an aggregate report) — skip.
                continue
            for row in reader:
                if label and row.get("label") != label:
                    continue
                try:
                    elapsed.append(float(row["elapsed"]))
                    timestamps.append(int(row["timeStamp"]))
                except (KeyError, TypeError, ValueError):
                    continue
                total += 1
                if str(row.get("success", "true")).strip().lower() != "true":
                    errors += 1

    return elapsed, timestamps, total, errors


def main() -> int:
    args = parse_args()
    results_dir = pathlib.Path(args.results_dir)
    files = find_result_files(results_dir)

    if not files:
        print(
            f"::error title=NFR-008::no JMeter result file found under {results_dir}",
            file=sys.stderr,
        )
        return 2

    elapsed, timestamps, total, errors = load_samples(files, args.label)

    if total == 0:
        # An empty result set must never read as a pass.
        print(
            "::error title=NFR-008::JMeter produced zero samples — the run did not "
            "exercise the application under test",
            file=sys.stderr,
        )
        return 2

    elapsed.sort()
    p95 = percentile(elapsed, 95.0)
    p99 = percentile(elapsed, 99.0)
    mean = sum(elapsed) / len(elapsed)
    error_rate = errors / total * 100.0

    span_ms = (max(timestamps) - min(timestamps)) if len(timestamps) > 1 else 0
    duration_s = span_ms / 1000.0
    throughput = (total / duration_s) if duration_s > 0 else float("nan")

    checks = [
        ("NFR-008", "p95 response time (ms)", p95, "<=", args.p95_ms),
        ("NFR-009", "error rate (%)", error_rate, "<=", args.error_rate_pct),
        ("NFR-010", "throughput (req/s)", throughput, ">=", args.min_throughput),
    ]

    failed: list[str] = []
    rows = []
    for gate, metric, actual, op, threshold in checks:
        if math.isnan(actual):
            ok = False
        elif op == "<=":
            ok = actual <= threshold
        else:
            ok = actual >= threshold
        rows.append(
            {
                "gate": gate,
                "metric": metric,
                "actual": f"{actual:.2f}",
                "operator": op,
                "threshold": f"{threshold:.2f}",
                "result": "PASS" if ok else "FAIL",
            }
        )
        status = "PASS" if ok else "FAIL"
        print(f"{gate}  {metric:26s} actual={actual:10.2f} {op} {threshold:<8.2f} {status}")
        if not ok:
            failed.append(gate)
            print(
                f"::error title={gate}::{metric} was {actual:.2f}, "
                f"threshold {op} {threshold:.2f}",
                file=sys.stderr,
            )

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["gate", "metric", "actual", "operator", "threshold", "result"]
        )
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "gate": "INFO",
                "metric": "samples / errors / mean ms / p99 ms / duration s",
                "actual": f"{total} / {errors} / {mean:.0f} / {p99:.0f} / {duration_s:.0f}",
                "operator": "",
                "threshold": "",
                "result": "",
            }
        )

    print(f"\nSummary written to {out}")
    print(f"samples={total} errors={errors} mean={mean:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
