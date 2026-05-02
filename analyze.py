"""
Analyze test results and generate reports.

Usage:
    python analyze.py results/results_YYYYMMDD_HHMMSS.json
    python analyze.py results/results_*.json   # merge multiple runs
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_results(paths: list[str]) -> list[dict]:
    results = []
    for p in paths:
        for match in Path(".").glob(p) if "*" in p else [Path(p)]:
            with open(match) as f:
                results.extend(json.load(f))
    return results


def print_table(headers: list[str], rows: list[list], col_widths: list[int] | None = None):
    if not col_widths:
        col_widths = [max(len(str(r[i])) for r in [headers] + rows) + 2 for i in range(len(headers))]
    header_line = "".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("".join(str(c).ljust(w) for c, w in zip(row, col_widths)))


def analyze(results: list[dict]):
    # Filter out errors
    valid = [r for r in results if r["judgment"] != "ERROR"]
    errors = [r for r in results if r["judgment"] == "ERROR"]

    if not valid:
        print("No valid results to analyze.")
        return

    print(f"Total results: {len(results)} ({len(valid)} valid, {len(errors)} errors)\n")

    # ----- 1. Overall pass rate by delimiter vs no-delimiter -----
    print("=" * 70)
    print("1. DELIMITER vs NO-DELIMITER OVERALL PASS RATE")
    print("=" * 70)

    for use_delim in [True, False]:
        subset = [r for r in valid if r["use_delimiter"] == use_delim]
        if not subset:
            continue
        label = "With Delimiter" if use_delim else "No Delimiter (baseline)"
        total = len(subset)
        pass_count = sum(1 for r in subset if r["judgment"] == "PASS")
        partial = sum(1 for r in subset if r["judgment"] == "PARTIAL")
        fail = sum(1 for r in subset if r["judgment"] == "FAIL")
        print(f"\n  {label} (n={total}):")
        print(f"    PASS:    {pass_count:4d} ({100*pass_count/total:.1f}%)")
        print(f"    PARTIAL: {partial:4d} ({100*partial/total:.1f}%)")
        print(f"    FAIL:    {fail:4d} ({100*fail/total:.1f}%)")

    # ----- 2. Pass rate by model -----
    print(f"\n{'=' * 70}")
    print("2. PASS RATE BY MODEL")
    print("=" * 70)

    headers = ["Model", "Delim PASS%", "Delim n", "Baseline PASS%", "Baseline n", "Delta"]
    rows = []
    models = sorted(set(r["model"] for r in valid))
    for model in models:
        for use_delim, label in [(True, "delim"), (False, "baseline")]:
            subset = [r for r in valid if r["model"] == model and r["use_delimiter"] == use_delim]
            if not subset:
                continue
            pass_pct = 100 * sum(1 for r in subset if r["judgment"] == "PASS") / len(subset)
            if use_delim:
                delim_pct, delim_n = pass_pct, len(subset)
            else:
                base_pct, base_n = pass_pct, len(subset)

        delta = f"+{delim_pct - base_pct:.1f}%" if delim_pct >= base_pct else f"{delim_pct - base_pct:.1f}%"
        rows.append([model, f"{delim_pct:.1f}%", delim_n, f"{base_pct:.1f}%", base_n, delta])

    print()
    print_table(headers, rows)

    # ----- 3. Pass rate by payload type -----
    print(f"\n{'=' * 70}")
    print("3. PASS RATE BY PAYLOAD TYPE (with delimiter)")
    print("=" * 70)

    headers = ["Payload", "PASS", "PARTIAL", "FAIL", "Total", "PASS%"]
    rows = []
    payload_types = sorted(set(r["payload"] for r in valid))
    for payload in payload_types:
        subset = [r for r in valid if r["payload"] == payload and r["use_delimiter"]]
        if not subset:
            continue
        total = len(subset)
        p = sum(1 for r in subset if r["judgment"] == "PASS")
        par = sum(1 for r in subset if r["judgment"] == "PARTIAL")
        f = sum(1 for r in subset if r["judgment"] == "FAIL")
        rows.append([payload, p, par, f, total, f"{100*p/total:.1f}%"])

    print()
    print_table(headers, rows)

    # ----- 4. Pass rate by defense template -----
    print(f"\n{'=' * 70}")
    print("4. PASS RATE BY DEFENSE TEMPLATE")
    print("=" * 70)

    headers = ["Template", "PASS", "PARTIAL", "FAIL", "Total", "PASS%"]
    rows = []
    for template in sorted(set(r["template"] for r in valid)):
        subset = [r for r in valid if r["template"] == template and r["use_delimiter"]]
        if not subset:
            continue
        total = len(subset)
        p = sum(1 for r in subset if r["judgment"] == "PASS")
        par = sum(1 for r in subset if r["judgment"] == "PARTIAL")
        f = sum(1 for r in subset if r["judgment"] == "FAIL")
        rows.append([template, p, par, f, total, f"{100*p/total:.1f}%"])

    print()
    print_table(headers, rows)

    # ----- 5. Pass rate by delimiter length -----
    print(f"\n{'=' * 70}")
    print("5. PASS RATE BY DELIMITER LENGTH")
    print("=" * 70)

    headers = ["Length", "PASS", "PARTIAL", "FAIL", "Total", "PASS%"]
    rows = []
    for length in sorted(set(r["delimiter_length"] for r in valid)):
        subset = [r for r in valid if r["delimiter_length"] == length and r["use_delimiter"]]
        if not subset:
            continue
        total = len(subset)
        p = sum(1 for r in subset if r["judgment"] == "PASS")
        par = sum(1 for r in subset if r["judgment"] == "PARTIAL")
        f = sum(1 for r in subset if r["judgment"] == "FAIL")
        rows.append([length, p, par, f, total, f"{100*p/total:.1f}%"])

    print()
    print_table(headers, rows)

    # ----- 6. Pass rate by document length -----
    print(f"\n{'=' * 70}")
    print("6. PASS RATE BY DOCUMENT LENGTH")
    print("=" * 70)

    headers = ["Doc Length", "PASS", "PARTIAL", "FAIL", "Total", "PASS%"]
    rows = []
    for doc_len in ["short", "medium", "long"]:
        subset = [r for r in valid if r["doc_length"] == doc_len and r["use_delimiter"]]
        if not subset:
            continue
        total = len(subset)
        p = sum(1 for r in subset if r["judgment"] == "PASS")
        par = sum(1 for r in subset if r["judgment"] == "PARTIAL")
        f = sum(1 for r in subset if r["judgment"] == "FAIL")
        rows.append([doc_len, p, par, f, total, f"{100*p/total:.1f}%"])

    print()
    print_table(headers, rows)

    # ----- 7. Worst cases: all FAILs with delimiter -----
    print(f"\n{'=' * 70}")
    print("7. FAILED CASES (with delimiter)")
    print("=" * 70)

    fails = [r for r in valid if r["judgment"] == "FAIL" and r["use_delimiter"]]
    if fails:
        print(f"\n  {len(fails)} failures:\n")
        for r in fails[:30]:
            output_preview = (r.get("output") or "")[:100].replace("\n", " ")
            print(
                f"    {r['model']:10s} | {r['payload']:20s} | {r['template']:12s} | "
                f"len={r['delimiter_length']} type={r['delimiter_type']} doc={r['doc_length']}"
            )
            print(f"      Output: {output_preview}...")
        if len(fails) > 30:
            print(f"    ... and {len(fails) - 30} more")
    else:
        print("\n  No failures with delimiter! All injections were blocked.")

    # ----- 8. Error summary -----
    if errors:
        print(f"\n{'=' * 70}")
        print(f"8. ERRORS ({len(errors)} total)")
        print("=" * 70)
        error_types = defaultdict(int)
        for e in errors:
            error_types[e.get("error", "unknown")] += 1
        for err, count in sorted(error_types.items(), key=lambda x: -x[1]):
            print(f"  {count:4d}x {err[:100]}")


def main():
    parser = argparse.ArgumentParser(description="Analyze red/blue test results")
    parser.add_argument("files", nargs="+", help="Result JSON files (supports glob)")
    args = parser.parse_args()

    results = load_results(args.files)
    if not results:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    analyze(results)


if __name__ == "__main__":
    main()
