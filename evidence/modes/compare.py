"""Compare the 24 and 29 September cohorts after running study.py for both."""
import collections
import gzip
import json
from pathlib import Path

from study import FEATURES, OPEN_DAYS

OUT = Path("evaluation/modes")


def rows(cohort):
    path = OUT / cohort / "opening_tiles.jsonl.gz"
    return [json.loads(line) for line in gzip.open(path, "rt", encoding="utf-8")]


def mean(values):
    return round(sum(values) / len(values), 3) if values else None


def main():
    data = {cohort: rows(cohort) for cohort in ("24-sept", "29-sept")}
    result = {}
    for cohort, cohort_rows in data.items():
        result[cohort] = {}
        for team in sorted({r["team"] for r in cohort_rows}):
            result[cohort][team] = {}
            for day in OPEN_DAYS:
                subset = [r for r in cohort_rows if r["team"] == team and r["day"] == day]
                result[cohort][team][str(day)] = {
                    "games": len(subset),
                    "plots": mean([r["plots"] for r in subset]),
                    "hands": mean([r["hands"] for r in subset]),
                    "money": mean([r["money"] for r in subset]),
                    "features": {f: mean([r["features"][f] / r["plots"] for r in subset]) for f in FEATURES},
                    "shops": {shop: mean([r["shops"].get(shop, 0) for r in subset])
                              for shop in sorted({shop for r in subset for shop in r["shops"]})},
                }
        result[cohort]["ALL"] = {}
        for day in OPEN_DAYS:
            subset = [r for r in cohort_rows if r["day"] == day]
            result[cohort]["ALL"][str(day)] = {
                "games": len(subset), "plots": mean([r["plots"] for r in subset]),
                "hands": mean([r["hands"] for r in subset]),
                "features": {f: mean([r["features"][f] / r["plots"] for r in subset]) for f in FEATURES},
                "clusters": dict(collections.Counter(str(r["cluster"]) for r in subset)),
            }
    (OUT / "comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for day in (6, 12, 18, 24):
        a, b = (result[c]["ALL"][str(day)] for c in ("24-sept", "29-sept"))
        print(day, "plots", a["plots"], b["plots"],
              "shares", {f: (a["features"][f], b["features"][f]) for f in FEATURES})


if __name__ == "__main__":
    main()
