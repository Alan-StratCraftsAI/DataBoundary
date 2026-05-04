"""
Run a harness profile with progress monitoring and auto-analysis.

Usage:
    python scripts/run_profile.py llama31_8b_startup
    python scripts/run_profile.py llama31_8b_coverage
    python scripts/run_profile.py llama31_8b_coverage --dry-run
    python scripts/run_profile.py llama31_8b_coverage --concurrency 1 --interval 60
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RESULTS_DIR = REPO_ROOT / "results"
LOG_DIR = RESULTS_DIR / "run_logs"

def log(message: str, transcript_path: Path) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
    print(line)
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_subprocess(cmd: list[str], transcript_path: Path) -> int:
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    for line in (proc.stdout + proc.stderr).splitlines():
        log(line, transcript_path)
    return proc.returncode


def run_with_progress(
    cmd: list[str],
    transcript_path: Path,
    expected: int,
    interval: int,
) -> int:
    import threading

    proc = subprocess.Popen(
        cmd, cwd=REPO_ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8",
    )
    lock = threading.Lock()
    done_count = [0]

    def log_line(message: str) -> None:
        line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
        with lock:
            print(line)
            with open(transcript_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def drain():
        for line in proc.stdout:
            stripped = line.rstrip()
            if stripped:
                if "Progress saved:" in stripped:
                    done_count[0] += 1
                log_line(stripped)

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()

    deadline = time.monotonic()
    while proc.poll() is None:
        time.sleep(1)
        if time.monotonic() >= deadline:
            deadline = time.monotonic() + interval
            done = done_count[0]
            pct = 100 * done / expected if expected else 0
            log_line(f"--- harness progress: {done}/{expected} ({pct:.1f}%) ---")

    reader.join()
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a harness profile with progress and analysis.")
    parser.add_argument("profile", help="Profile name from config.py RUN_PROFILES")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--expected", type=int, default=200,
                        help="Expected number of Ollama requests for progress display")
    parser.add_argument("--interval", type=int, default=60,
                        help="Progress report interval in seconds")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only print test cases, do not call APIs")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{args.profile}_{timestamp}"
    transcript_path = LOG_DIR / f"{run_name}.transcript.log"
    analysis_path = LOG_DIR / f"{run_name}.analysis.log"
    manifest_path = LOG_DIR / f"{run_name}.manifest.json"

    log(f"Profile:     {args.profile}", transcript_path)
    log(f"Concurrency: {args.concurrency}", transcript_path)
    log(f"Python:      {args.python}", transcript_path)
    log(f"Transcript:  {transcript_path}", transcript_path)

    base_cmd = [
        args.python, "-u", "harness.py",
        "--profile", args.profile,
        "--concurrency", str(args.concurrency),
    ]

    # Dry-run check
    log("Dry-run check...", transcript_path)
    dry_exit = run_subprocess(base_cmd + ["--dry-run"], transcript_path)
    log(f"Dry-run exit: {dry_exit}", transcript_path)
    if dry_exit != 0:
        sys.exit(f"Dry-run failed (exit {dry_exit})")

    if args.dry_run:
        log("--dry-run requested; stopping here.", transcript_path)
        return

    # Full run
    log("Starting harness run...", transcript_path)
    started_at = datetime.now()
    harness_exit = run_with_progress(
        base_cmd, transcript_path,
        expected=args.expected,
        interval=args.interval,
    )
    log(f"Harness exit: {harness_exit}", transcript_path)

    finished_at = datetime.now()

    # Find result file
    result_file = None
    for f in sorted(RESULTS_DIR.glob("results_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.stat().st_mtime >= started_at.timestamp():
            result_file = f
            break

    # Analysis
    analysis_exit = None
    if result_file:
        log(f"Result file: {result_file}", transcript_path)
        analysis_exit = run_subprocess(
            [args.python, "analyze.py", str(result_file)], analysis_path
        )
        log(f"Analysis exit: {analysis_exit}", transcript_path)
    else:
        log("No new result file found.", transcript_path)

    manifest = {
        "profile": args.profile,
        "concurrency": args.concurrency,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "harness_exit_code": harness_exit,
        "analysis_exit_code": analysis_exit,
        "result_file": str(result_file) if result_file else None,
        "transcript": str(transcript_path),
        "analysis": str(analysis_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"Manifest: {manifest_path}", transcript_path)

    if harness_exit != 0:
        sys.exit(f"Harness failed (exit {harness_exit})")
    if analysis_exit is not None and analysis_exit != 0:
        sys.exit(f"Analysis failed (exit {analysis_exit})")


if __name__ == "__main__":
    main()
