"""One-off extractor: workbook → data/python_metrics.json (Python-focused rows)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

WORKBOOK = Path(
    r"c:\Users\HP\Downloads\Testable_Strategy_Metrics_Mapping_v0.2_19_may_2026 2.xlsx"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "data" / "python_metrics.json"
PKG_OUT = REPO_ROOT / "src" / "strategy_metrics" / "python_metrics.json"

LANG_BLOCKS = {
    "python": {"primary": 6, "secondary": 7, "direct_col": 8, "derivation_shared": 9},
    "c": {"primary": 10, "secondary": 11, "direct_col": None, "derivation_shared": 9},
    "cpp": {"primary": 12, "secondary": 13, "direct_col": None, "derivation_shared": 9},
    "java": {"primary": 14, "secondary": 15, "direct_col": 16, "derivation": 17},
    "csharp": {"primary": 18, "secondary": 19, "direct_col": 20, "derivation": 21},
    "javascript": {"primary": 22, "secondary": 23, "direct_col": 24, "derivation": 25},
    "typescript": {"primary": 26, "secondary": 27, "direct_col": 28, "derivation": 29},
}

COMMON = {
    "l1_strategy": 0,
    "l2_testing_type": 1,
    "l3_technique": 2,
    "l4_classification": 3,
    "l5_metric": 4,
    "description": 5,
    "raw_formula": 30,
    "threshold": 31,
    "normalization": 32,
    "execution_frequency": 33,
}


def clean(v: object) -> str | None:
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s if s else None


def slug(*parts: str | None) -> str:
    s = "_".join(p for p in parts if p)
    return re.sub(r"[^a-zA-Z0-9]+", "_", s.lower()).strip("_")[:120]


def extract_white_box(df: pd.DataFrame) -> list[dict]:
    records: list[dict] = []
    for i in range(5, len(df)):
        row = df.iloc[i]
        l5 = clean(row[COMMON["l5_metric"]])
        if not l5 or l5.startswith("▶"):
            continue
        rec: dict = {
            "sheet": "White Box",
            "id": slug(clean(row[COMMON["l2_testing_type"]]), clean(row[COMMON["l3_technique"]]), l5),
            "l1_strategy": clean(row[COMMON["l1_strategy"]]),
            "l2_testing_type": clean(row[COMMON["l2_testing_type"]]),
            "l3_technique": clean(row[COMMON["l3_technique"]]),
            "l4_classification": clean(row[COMMON["l4_classification"]]),
            "l5_metric": l5,
            "description": clean(row[COMMON["description"]]),
            "derivation": clean(row[9]),
            "raw_measurement_formula": clean(row[COMMON["raw_formula"]]),
            "expected_threshold": clean(row[COMMON["threshold"]]),
            "normalization_formula": clean(row[COMMON["normalization"]]),
            "execution_frequency": clean(row[COMMON["execution_frequency"]]),
            "languages": {},
        }
        for lang, cols in LANG_BLOCKS.items():
            prim = clean(row[cols["primary"]])
            sec = clean(row[cols["secondary"]])
            if not prim and not sec:
                continue
            deriv_col = cols["derivation"] if "derivation" in cols else cols["derivation_shared"]
            deriv = clean(row[deriv_col])
            direct = clean(row[cols["direct_col"]]) if cols.get("direct_col") is not None else None
            rec["languages"][lang] = {
                "primary_tool": prim,
                "secondary_tool": sec,
                "metric_emitted_directly": direct,
                "derivation": deriv,
            }
        if rec["languages"].get("python"):
            records.append(rec)
    return records


def main() -> None:
    if not WORKBOOK.is_file():
        raise SystemExit(f"Workbook not found: {WORKBOOK}")

    records = extract_white_box(pd.read_excel(WORKBOOK, sheet_name="White Box", header=None))
    data = {
        "workbook": WORKBOOK.name,
        "version": "0.2",
        "python_metric_count": len(records),
        "metrics": records,
    }
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload, encoding="utf-8")
    PKG_OUT.write_text(payload, encoding="utf-8")
    print(f"Wrote {len(records)} Python White Box metrics → {OUT}")

    import sys

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from build_primary_tools_data import build  # noqa: WPS433

    build()


if __name__ == "__main__":
    main()
