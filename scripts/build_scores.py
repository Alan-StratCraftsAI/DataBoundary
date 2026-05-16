"""Build results/scores.json from results/metadata.json.

scores.json is the stable consumption surface for downstream tools
(notably databoundary-proxy). Schema is documented in results/SCORES_SCHEMA.md.
"""
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(HERE, "results")
METADATA_PATH = os.path.join(RESULTS_DIR, "metadata.json")
SCORES_PATH = os.path.join(RESULTS_DIR, "scores.json")

# Models in the active testing matrix (CLAUDE.md "Model Testing Policy"
# + currently-tested locals). Anything not in this set is excluded.
ACTIVE_MODELS = {
    "claude_haiku",
    "openai_mini",
    "deepseek_v4_flash",
    "deepseek_v4_pro",
    "gemini",
    "grok",
    "kimi",
    "qwen_plus",
    "qwen35_9b_local",
    "qwen25_7b_local",
    "llama31_8b_local",
    "gemma4_e4b",
    "glm4_9b_local",
}

SCHEMA_VERSION = "1.0.0"
LAYER = "layer_0_single_doc"


def main() -> None:
    with open(METADATA_PATH, encoding="utf-8") as f:
        meta = json.load(f)

    dataset_version = meta["version"]
    models_in = meta["models"]

    scores = []
    skipped = []
    for model_id, m in models_in.items():
        if model_id not in ACTIVE_MODELS:
            skipped.append(model_id)
            continue
        total = m["total"]
        pass_ = m["pass"]
        pass_rate = pass_ / total if total else 0.0
        scores.append({
            "model": model_id,
            "display_name": m["display_name"],
            "layer": LAYER,
            "total": total,
            "pass": pass_,
            "fail": m["fail"],
            "errors": m["errors"],
            "pass_rate": round(pass_rate, 4),
        })

    scores.sort(key=lambda r: r["model"])

    out = {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": dataset_version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pass_rate_definition": "pass / total (errors counted in denominator)",
        "scores": scores,
    }

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {SCORES_PATH}")
    print(f"  scored {len(scores)} models")
    if skipped:
        print(f"  skipped (not in active matrix): {', '.join(sorted(skipped))}")


if __name__ == "__main__":
    main()
