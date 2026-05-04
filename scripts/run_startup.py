from __future__ import annotations

import argparse
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

PROFILE_NAME = "startup"
TICKET_ID = "TICKET-007"
TITLE = "Startup Profile Progress"
PROGRESS_PATH = PROGRESS_DIR / "startup.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the startup profile and update progress docs")
    parser.add_argument("--concurrency", type=int, default=3, help="Max concurrent model calls")
    parser.add_argument("--dry-run", action="store_true", help="Validate the profile only")
    parser.add_argument("--output", type=str, default=None, help="Optional JSON result path")
    args = parser.parse_args()

    steps = [
        {"label": "Dry-run validation", "status": "pending", "detail": ""},
        {"label": "Benchmark execution", "status": "pending", "detail": ""},
        {"label": "Result summary", "status": "pending", "detail": ""},
        {"label": "Progress document refresh", "status": "pending", "detail": ""},
    ]
    commands: list[dict] = []
    notes = [
        "This script is the repo-standard entry point for the startup profile.",
        "Use --dry-run when API keys or local Ollama are not ready yet.",
    ]

    write_progress_doc(
        path=PROGRESS_PATH,
        title=TITLE,
        ticket_id=TICKET_ID,
        profile_name=PROFILE_NAME,
        status="running",
        steps=steps,
        commands=commands,
        pending_items=["Dry-run has not been executed yet."],
        notes=notes,
    )

    dry_run_cmd = python_cmd("harness.py", "--profile", PROFILE_NAME, "--dry-run")
    dry_run_result = run_command(dry_run_cmd)
    commands.append(
        {
            "command": " ".join(dry_run_cmd[1:]),
            "status": "ok" if dry_run_result.returncode == 0 else "failed",
        }
    )
    if dry_run_result.returncode != 0:
        steps[0]["status"] = "failed"
        steps[0]["detail"] = "Profile validation failed."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Failure recorded."
        write_progress_doc(
            path=PROGRESS_PATH,
            title=TITLE,
            ticket_id=TICKET_ID,
            profile_name=PROFILE_NAME,
            status="blocked",
            steps=steps,
            commands=commands,
            pending_items=["Fix the startup profile before running the benchmark."],
            notes=notes + [dry_run_result.stderr.strip() or dry_run_result.stdout.strip()],
        )
        return dry_run_result.returncode

    steps[0]["status"] = "completed"
    steps[0]["detail"] = "Profile expands successfully."

    if args.dry_run:
        steps[1]["status"] = "skipped"
        steps[1]["detail"] = "Skipped because --dry-run was requested."
        steps[2]["status"] = "pending"
        steps[2]["detail"] = "No result JSON available yet."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Dry-run state recorded."
        write_progress_doc(
            path=PROGRESS_PATH,
            title=TITLE,
            ticket_id=TICKET_ID,
            profile_name=PROFILE_NAME,
            status="dry-run-only",
            steps=steps,
            commands=commands,
            pending_items=[
                "Run the full startup benchmark.",
                "Capture and review the result JSON.",
            ],
            notes=notes,
        )
        return 0

    output_path = Path(args.output) if args.output else default_output_path(PROFILE_NAME)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    run_cmd = python_cmd(
        "harness.py",
        "--profile",
        PROFILE_NAME,
        "--concurrency",
        str(args.concurrency),
        "--output",
        str(output_path.relative_to(REPO_ROOT)),
    )
    run_result = run_command(run_cmd)
    commands.append(
        {
            "command": " ".join(run_cmd[1:]),
            "status": "ok" if run_result.returncode == 0 else "failed",
        }
    )
    if run_result.returncode != 0:
        steps[1]["status"] = "failed"
        steps[1]["detail"] = "Benchmark execution failed."
        steps[3]["status"] = "completed"
        steps[3]["detail"] = "Failure recorded."
        write_progress_doc(
            path=PROGRESS_PATH,
            title=TITLE,
            ticket_id=TICKET_ID,
            profile_name=PROFILE_NAME,
            status="blocked",
            steps=steps,
            commands=commands,
            pending_items=["Investigate the benchmark failure and rerun the startup profile."],
            notes=notes + [run_result.stderr.strip() or run_result.stdout.strip()],
        )
        return run_result.returncode

    steps[1]["status"] = "completed"
    steps[1]["detail"] = f"Benchmark output saved to {output_path.relative_to(REPO_ROOT)}."

    summary = summarize_results(output_path)
    steps[2]["status"] = "completed"
    steps[2]["detail"] = "Summary generated from the latest JSON file."
    steps[3]["status"] = "completed"
    steps[3]["detail"] = "Progress tracker refreshed."
    write_progress_doc(
        path=PROGRESS_PATH,
        title=TITLE,
        ticket_id=TICKET_ID,
        profile_name=PROFILE_NAME,
        status="completed",
        steps=steps,
        commands=commands,
        pending_items=[],
        result_path=output_path,
        summary=summary,
        notes=notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
