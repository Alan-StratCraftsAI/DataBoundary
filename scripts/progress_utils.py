from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROGRESS_DIR = REPO_ROOT / "progress"
PROGRESS_DIR.mkdir(exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_output_path(profile_name: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "results" / f"{profile_name}_{stamp}.json"


def run_command(args: list[str], quiet: bool = False) -> subprocess.CompletedProcess[str]:
    if quiet:
        return subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    # Stream stdout/stderr to terminal in real time
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        check=False,
    )


def summarize_results(path: Path) -> dict:
    with open(path) as f:
        results = json.load(f)

    counts = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "ERROR": 0}
    delim_total = 0
    delim_pass = 0
    baseline_total = 0
    baseline_pass = 0
    for row in results:
        judgment = row.get("judgment", "ERROR")
        counts[judgment] = counts.get(judgment, 0) + 1
        if row.get("use_delimiter"):
            delim_total += 1
            if judgment == "PASS":
                delim_pass += 1
        else:
            baseline_total += 1
            if judgment == "PASS":
                baseline_pass += 1

    def pct(numerator: int, denominator: int) -> str:
        if not denominator:
            return "n/a"
        return f"{100 * numerator / denominator:.1f}%"

    return {
        "total": len(results),
        "counts": counts,
        "delimiter_pass_rate": pct(delim_pass, delim_total),
        "baseline_pass_rate": pct(baseline_pass, baseline_total),
    }


def write_progress_doc(
    *,
    path: Path,
    title: str,
    ticket_id: str,
    profile_name: str,
    status: str,
    steps: list[dict],
    commands: list[dict],
    pending_items: list[str],
    result_path: Path | None = None,
    summary: dict | None = None,
    notes: list[str] | None = None,
) -> None:
    icons = {
        "pending": "[ ]",
        "completed": "[x]",
        "failed": "[!]",
        "skipped": "[-]",
    }
    lines = [
        f"# {title}",
        "",
        f"- Ticket: `{ticket_id}`",
        f"- Profile: `{profile_name}`",
        f"- Status: `{status}`",
        f"- Updated: `{utc_now()}`",
    ]

    if result_path:
        lines.append(f"- Result file: `{result_path.relative_to(REPO_ROOT)}`")

    lines.extend(["", "## Checklist", ""])
    for step in steps:
        prefix = icons.get(step["status"], "[ ]")
        detail = f" - {step['detail']}" if step.get("detail") else ""
        lines.append(f"{prefix} {step['label']}{detail}")

    if summary:
        counts = summary["counts"]
        lines.extend(
            [
                "",
                "## Latest Summary",
                "",
                f"- Total cases: `{summary['total']}`",
                f"- PASS: `{counts.get('PASS', 0)}`",
                f"- PARTIAL: `{counts.get('PARTIAL', 0)}`",
                f"- FAIL: `{counts.get('FAIL', 0)}`",
                f"- ERROR: `{counts.get('ERROR', 0)}`",
                f"- Delimiter PASS rate: `{summary['delimiter_pass_rate']}`",
                f"- Baseline PASS rate: `{summary['baseline_pass_rate']}`",
            ]
        )

    lines.extend(["", "## Pending Items", ""])
    if pending_items:
        for item in pending_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Command Log", ""])
    if commands:
        for entry in commands:
            lines.append(f"- `{entry['command']}` -> `{entry['status']}`")
    else:
        lines.append("- No commands run yet.")

    if notes:
        lines.extend(["", "## Notes", ""])
        for note in notes:
            lines.append(f"- {note}")

    path.write_text("\n".join(lines) + "\n")


def python_cmd(*args: str) -> list[str]:
    return [sys.executable, *args]
