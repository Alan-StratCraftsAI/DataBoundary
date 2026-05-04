# Startup Profile Progress

- Ticket: `TICKET-007`
- Profile: `startup`
- Status: `completed`
- Updated: `2026-05-04T06:44:06Z`
- Result file: `results/startup_20260504_064345.json`

## Checklist

[x] Dry-run validation - Profile expands successfully.
[x] Benchmark execution - Benchmark output saved to results/startup_20260504_064345.json.
[x] Result summary - Summary generated from the latest JSON file.
[x] Progress document refresh - Progress tracker refreshed.

## Latest Summary

- Total cases: `8`
- PASS: `7`
- PARTIAL: `0`
- FAIL: `1`
- ERROR: `0`
- Delimiter PASS rate: `100.0%`
- Baseline PASS rate: `75.0%`

## Pending Items

- None.

## Command Log

- `harness.py --profile startup --dry-run` -> `ok`
- `harness.py --profile startup --concurrency 3 --output results/startup_20260504_064345.json` -> `ok`

## Notes

- This script is the repo-standard entry point for the startup profile.
- Use --dry-run when API keys or local Ollama are not ready yet.
