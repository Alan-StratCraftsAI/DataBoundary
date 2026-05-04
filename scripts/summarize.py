import json, collections, os, sys

results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
files = sorted(os.listdir(results_dir))

for f in files:
    path = os.path.join(results_dir, f)
    size = os.path.getsize(path)
    if size < 5000:
        continue
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not data:
            continue
        models = collections.Counter(r["model"] for r in data)
        print(f"{f}  n={len(data)}")
        for m in sorted(models):
            sub = [r for r in data if r["model"] == m]
            j = collections.Counter(r["judgment"] for r in sub)
            p, pa, fa, er = j.get("PASS",0), j.get("PARTIAL",0), j.get("FAIL",0), j.get("ERROR",0)
            print(f"  {m:30s}  PASS={p} PARTIAL={pa} FAIL={fa} ERROR={er}")
    except Exception as e:
        print(f"{f}: ERROR {e}")
