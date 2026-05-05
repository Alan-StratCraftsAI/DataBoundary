"""Generic profile runner with progress tracking.

Usage:
    python scripts/run_profile.py <profile_name> [--dry-run] [--concurrency N] [--output PATH]

Examples:
    python scripts/run_profile.py startup --dry-run
    python scripts/run_profile.py coverage200 --concurrency 2
    python scripts/run_profile.py coverage200_qwen_plus
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from progress_utils import (
    PROGRESS_DIR,
    REPO_ROOT,
    default_output_path,
    python_cmd,
    run_command,
    summarize_results,
    write_progress_doc,
)

# Allow importing RUN_PROFILES from config.py at repo root.
sys.path.insert(0, str(REPO_ROOT))
from config import RUN_PROFILES  # noqa: E402


def run_profile(
    profile_name: str,
    *,
    dry_run: bool = False,
    concurrency: int = 3,
    output: str | None = None,
) -> int:
    """Run a named profile with dry-run validation and progress tracking.

    Returns the process exit code (0 = success).
    """
    if profile_name not in RUN_PROFILES:
        available = ", ".join(sorted(RUN_PROFILES))
        print(f"Unknown profile '{profile_name}'. Available: {available}", file=sys.stderr)
        return 1

    title = f"{profile_name} Profile Progress"
    progress_path = PROGRESS_DIR / f"{profile_name}.md"

    steps = [
        {"label": "Dry-run validation", "status": "pending", "detail": ""},
        {"label": "Benchmark execution", "status": "pending", "detail": ""},
        {"label": "Result summary", "status": "pending", "detail": ""},
        {"label": "Progress document refresh", "status": "pending", "detail": ""},
    ]
    commands: list[dict] = []
    notes = [
        f"Profile: {profile_name}",
        f"Description: {RUN_PROFILES[profile_name].get('description', '')}",
    ]

    def save(status: str, pending: list[str] | None = None, **kwargs):
        write_progress_doc(
            path=progress_path,
            title=title,
            ticket_id="",
            profile_name=profile_name,
            status=status,
            steps=steps,
            commands=commands,
            pending_items=pending or [],
            notes=notes,
            **kwargs,
        )

    save("running", pending=["Dry-run has not been executed yet."])

    # --- Step 1: dry-run validation ---
    dry_run_cmd = python_cmd("harness.py", "--profile", profile_name, "--dry-run")
    dry_run_result = run_command(dry_run_cmd, quiet=True)
    commands.append({
        "command": " ".join(dry_run_cmd[1:]),
        "status": "ok" if dry_run_result.returncode == 0 else "failed",
    })

    if dry_run_result.returncode != 0:
        steps[0]["status"] = "failed"
        steps[0]["detail"] = "Profile validation failed."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Failure recorded."
        full_err = (dry_run_result.stderr or "").strip() or (dry_run_result.stdout or "").strip() or ""
        if full_err:
            lines = full_err.splitlines()
            summary_line = next(
                (l for l in reversed(lines) if l and not l.startswith(" ")),
                lines[-1],
            )
        else:
            summary_line = "Unknown error (no output captured)"
        notes.append(full_err or summary_line)
        print(f"[FAIL] Dry-run validation failed: {summary_line}", file=sys.stderr)
        print(f"       Details saved to: {progress_path}", file=sys.stderr)
        save("blocked", pending=[f"Fix the {profile_name} profile before running the benchmark."])
        return dry_run_result.returncode

    steps[0]["status"] = "completed"
    steps[0]["detail"] = "Profile expands successfully."
    print(f"[OK] Dry-run validation passed for '{profile_name}'.")

    # --- Dry-run only: stop here ---
    if dry_run:
        steps[1]["status"] = "skipped"
        steps[1]["detail"] = "Skipped because --dry-run was requested."
        steps[2]["status"] = "pending"
        steps[2]["detail"] = "No result JSON available yet."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Dry-run state recorded."
        save("dry-run-only", pending=[
            f"Run the full {profile_name} benchmark.",
            "Capture and review the result JSON.",
        ])
        return 0

    # --- Step 2: benchmark execution ---
    output_path = Path(output) if output else default_output_path(profile_name)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    run_cmd = python_cmd(
        "harness.py",
        "--profile", profile_name,
        "--concurrency", str(concurrency),
        "--output", str(output_path.relative_to(REPO_ROOT)),
    )
    run_result = run_command(run_cmd)
    commands.append({
        "command": " ".join(run_cmd[1:]),
        "status": "ok" if run_result.returncode == 0 else "failed",
    })

    if run_result.returncode != 0:
        steps[1]["status"] = "failed"
        steps[1]["detail"] = "Benchmark execution failed."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Failure recorded."
        full_err = (run_result.stderr or "").strip() or (run_result.stdout or "").strip() or ""
        # Extract a one-line summary: last non-indented line (typically the Exception)
        if full_err:
            lines = full_err.splitlines()
            summary_line = next(
                (l for l in reversed(lines) if l and not l.startswith(" ")),
                lines[-1],
            )
        else:
            summary_line = "Unknown error (no output captured)"
        notes.append(full_err or summary_line)
        print(f"[FAIL] Benchmark execution failed: {summary_line}", file=sys.stderr)
        print(f"       Details saved to: {progress_path}", file=sys.stderr)
        save("blocked", pending=[f"Investigate the benchmark failure and rerun {profile_name}."])
        return run_result.returncode

    steps[1]["status"] = "completed"
    steps[1]["detail"] = f"Benchmark output saved to {output_path.relative_to(REPO_ROOT)}."
    print(f"[OK] Benchmark completed. Output: {output_path.relative_to(REPO_ROOT)}")

    # --- Step 3: result summary ---
    summary = summarize_results(output_path)
    steps[2]["status"] = "completed"
    steps[2]["detail"] = "Summary generated from the latest JSON file."
    steps[3]["status"] = "completed"
    steps[3]["detail"] = "Progress tracker refreshed."
    save("completed", result_path=output_path, summary=summary)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run any benchmark profile with progress tracking",
    )
    parser.add_argument("profile", help="Profile name defined in config.RUN_PROFILES")
    parser.add_argument("--concurrency", type=int, default=3, help="Max concurrent model calls")
    parser.add_argument("--dry-run", action="store_true", help="Validate the profile only")
    parser.add_argument("--output", type=str, default=None, help="Optional JSON result path")
    args = parser.parse_args()

    return run_profile(
        args.profile,
        dry_run=args.dry_run,
        concurrency=args.concurrency,
        output=args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
