# Ticket 007: Scripted `startup` And `coverage200` Runs With Progress Logs

## Summary

Create Python entry points for the repo's `startup` and `coverage200` profiles,
and ensure each workflow writes its current status into markdown progress docs
so unfinished work stays visible.

## Goal

- Add `scripts/run_startup.py`
- Add `scripts/run_coverage200.py`
- Persist progress to `progress/startup.md` and `progress/coverage200.md`
- Record incomplete steps instead of hiding them in terminal output

## Acceptance Criteria

- Both scripts support `--dry-run`
- Both scripts can execute the corresponding `harness.py --profile ...` flow
- Each script updates its progress markdown before and after execution
- Pending or blocked items are explicitly listed in the markdown

## Progress Docs

- [progress/startup.md](progress/startup.md)
- [progress/coverage200.md](progress/coverage200.md)

## Status

**Implementation complete.** All code was written and dry-run validated on 2026-05-04.

Delivered files:

- `scripts/run_startup.py` — entry point for the startup profile
- `scripts/run_coverage200.py` — entry point for the coverage200 profile
- `scripts/progress_utils.py` — shared progress-doc utilities
- `progress/startup.md` — auto-generated progress tracker (startup)
- `progress/coverage200.md` — auto-generated progress tracker (coverage200)

Dry-run validation passed for both scripts:

- `python scripts/run_startup.py --dry-run`
- `python scripts/run_coverage200.py --dry-run`

## Operational Follow-Up (not code work)

The following are runtime tasks, not development tasks:

- Run `python scripts/run_startup.py` to execute the full startup benchmark
- Run `python scripts/run_coverage200.py` to execute the full coverage200 benchmark
- Review the generated markdown trackers after each full run
