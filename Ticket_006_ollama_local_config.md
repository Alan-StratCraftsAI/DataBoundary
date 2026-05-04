# Ticket 006: Local Ollama Support In `config.local.json`

## Summary

Add first-class support for registering local Ollama models through
`config.local.json`, without requiring developers to hardcode each local model
in `config.py`.

## Goal

- Allow local models to be declared under `local_models`
- Register those models automatically at startup
- Support `provider="ollama"` in the main benchmark runner
- Document the config shape in repo docs

## Acceptance Criteria

- `config.local.json.example` shows at least one Ollama model example
- `python harness.py --model <local_ollama_key> --profile startup --dry-run`
  works when the key exists in `config.local.json`
- `README.md` and `CONTRIBUTING.md` describe the local-model workflow

## Status

Implemented on 2026-05-04 and validated with a temporary
`DATABOUNDARY_CONFIG` smoke test:

```bash
python harness.py --model ollama_smoke --profile startup --dry-run
```

## Remaining Follow-Up

- Add one real local Ollama model to your own `config.local.json`
- Run a non-dry startup benchmark once the local Ollama service is available
