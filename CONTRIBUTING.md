# Contributing to DataBoundary

The most useful contribution right now is simple:

> Run DataBoundary against a model we do not already cover, then submit the result JSON.

This document focuses on that workflow first. It also covers how to add new attack payloads and defense templates.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`
- API access to the model you want to test

DataBoundary writes output files to `results/` as JSON arrays. Those JSON files are sanitized on write so provider keys do not get persisted in saved error messages.

Local key configuration can come from any of these sources:

1. `config.local.json`
2. real environment variables
3. `.env.local`
4. `.env`

Use the bundled JSON example as a starting point:

```bash
cp config.local.json.example config.local.json
```

## Quick Path: Run an Existing Model

If the model is already registered in `config.py`, you only need an API key.

Preferred local setup: add keys to `config.local.json` under `api_keys`.

Environment variables are still supported when you need them:

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export DEEPSEEK_API_KEY=...
export GOOGLE_API_KEY=...
export GROK_API_KEY=...
export QWEN_API_KEY=...
export KIMI_API_KEY=...
```

Check the runner:

```bash
python harness.py --help
python harness.py --dry-run
```

Run one model:

```bash
python harness.py --model openai_mini
```

Analyze the output:

```bash
python analyze.py results/results_*.json
```

If you are contributing data for an already-registered model, that is enough.

## How To Add Your Own Model

There are three moving parts:

1. make the API key available
2. register the model in `config.py`
3. run the harness and submit the JSON result

### 1. Add API key loading

`config.py` loads keys in `_load_keys()`. If your provider is new, add both the local JSON key name and the env-var loader if you want CI compatibility.

Example pattern:

```python
if os.getenv("MYPROVIDER_API_KEY"):
    keys.setdefault("myprovider_api_keys", [os.environ["MYPROVIDER_API_KEY"]])
```

If your provider needs multiple rotating keys, follow the Gemini pattern instead of the single-key pattern.

For local use, add the provider key list under the `api_keys` object in `config.local.json`.

### 2. Register the model in `MODELS`

Add a new entry to `MODELS` in [config.py](config.py).

Each entry needs:

- `name`: human-readable display name
- `provider`: one of the caller types supported in `harness.py`
- `model`: provider-side model identifier
- `api_base`: required for OpenAI-compatible endpoints
- `api_key`: loaded from `_load_keys()`
- `tier`: `T1`, `T2`, or `T3`

Existing provider types:

- `openai_compat`
- `openai`
- `gemini`
- `anthropic`
- `ollama`

`ollama` is intended for local models and does not require an API key. Instead,
declare the model under `local_models` in `config.local.json`.

Example for an OpenAI-compatible endpoint:

```python
if _keys.get("myprovider_api_keys"):
    MODELS["my_model_key"] = {
        "name": "My Model",
        "provider": "openai_compat",
        "model": "my-model-id",
        "api_base": "https://api.example.com/v1",
        "api_key": _keys["myprovider_api_keys"][0],
        "tier": "T2",
    }
```

Choose the tier pragmatically:

- `T1`: cheap enough for broad matrix coverage
- `T2`: medium-cost models
- `T3`: expensive models that should usually run narrower slices

### 3. Run the model

Start with a dry run to confirm the key is recognized and the model key is spelled correctly:

```bash
python harness.py --dry-run --model my_model_key
```

Then run a small validation slice first:

```bash
python harness.py --profile startup --model my_model_key
python scripts/run_startup.py --dry-run
```

If that works, run a fuller pass:

```bash
python harness.py --model my_model_key
```

If the model is expensive or rate-limited, lower concurrency:

```bash
python harness.py --model my_model_key --concurrency 1
```

For the repo-standard benchmark workflows, prefer the helper scripts:

```bash
python scripts/run_startup.py
python scripts/run_coverage200.py --concurrency 2
python scripts/run_profile.py qwen35_9b_coverage
```

Those wrappers run the profile, save a deterministic JSON file when requested,
and refresh the markdown progress logs under `progress/`.

If you only need one-off execution without progress tracking, calling `harness.py`
directly is still fine.

## Which Run To Contribute

The ideal contribution is a clean single-model run that can be compared against the existing matrix.

Recommended order:

1. `--profile startup` to catch auth or formatting errors cheaply
2. `--model <key>` for a default per-tier run
3. optional rerun with lower concurrency if the provider rate-limits heavily

If you cannot afford a full run, partial data is still useful. Open the PR anyway and explain what subset you ran.

## What To Include In The PR

Include:

- the code change in [config.py](config.py) if you added a new provider or model
- the result JSON file under `results/`
- a short note with provider name, exact model ID, run date, and any rate-limit issues

Useful PR summary template:

```text
Added model: my_model_key
Provider: MyProvider
Model ID: my-model-id
Run command: python harness.py --model my_model_key --concurrency 1
Notes: hit 429s at concurrency 3, reran at concurrency 1
```

Do not commit API keys or provider secrets. If you add any custom logging around provider calls, keep the same redaction standard as `harness.py`.

## Adding A New Attack Payload

1. Add a new `.txt` file under [red/payloads](red/payloads)
2. Register the payload name in `config.PAYLOAD_FILES`
3. Re-run at least one model with and without delimiters
4. Explain in the PR what behavior the payload is trying to trigger

Good payload contributions are specific. "More jailbreak text" is weak. A payload targeting a concrete failure mode such as delimiter mimicry, authority laundering, or instruction drift is strong.

## Adding A New Defense Template

1. Add a template file under [blue/templates](blue/templates)
2. Register it in `config.DEFENSE_TEMPLATES`
3. Re-run the matrix or at least a representative subset
4. Compare it against `strict` and `contextual`

If your template requires a multi-step flow rather than one prompt, you will also need to update [blue/defender.py](blue/defender.py) and the template handling in [harness.py](harness.py).

## Result Quality Expectations

Before opening a PR, check:

- the run completed without obvious auth failures
- the JSON file contains structured result entries, not only `ERROR`
- `EMPTY` rows, if any, are explained in the PR note because they are excluded from pass-rate stats
- the model is identified consistently by one `model` key
- your PR notes explain any small sample size or rate-limit distortion

Saved result rows include both `judgment` and `judgment_filtered`. The benchmark headline numbers use `judgment`; the filtered variant is there so reviewers can inspect the optional post-hoc filter layer separately.

## Current Limits

- dependency pinning is not finalized
- key loading currently lives inside `config.py`

Contributions are welcome. Optimize for reproducible data and clear notes rather than polish.
