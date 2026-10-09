"""Split ``python_metrics.json`` into one JSON bundle per Python primary tool."""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "data" / "python_metrics.json"
OUT_DIR = REPO_ROOT / "data" / "primary_tools"
PKG_DIR = REPO_ROOT / "src" / "strategy_metrics" / "primary_tools"

# Allow import when run as script
sys.path.insert(0, str(REPO_ROOT / "src"))
from strategy_metrics.tool_ids import (  # noqa: E402
    assign_primary_tool_slugs,
    normalize_primary_tool_name,
)


def metric_payload(raw: dict) -> dict:
    py = raw.get("languages", {}).get("python", {})
    return {
        "id": raw["id"],
        "sheet": raw.get("sheet"),
        "l1_strategy": raw.get("l1_strategy"),
        "l2_testing_type": raw.get("l2_testing_type"),
        "l3_technique": raw.get("l3_technique"),
        "l4_classification": raw.get("l4_classification"),
        "l5_metric": raw.get("l5_metric"),
        "description": raw.get("description"),
        "derivation": raw.get("derivation"),
        "raw_measurement_formula": raw.get("raw_measurement_formula"),
        "expected_threshold": raw.get("expected_threshold"),
        "normalization_formula": raw.get("normalization_formula"),
        "execution_frequency": raw.get("execution_frequency"),
        "python": {
            "primary_tool": py.get("primary_tool"),
            "secondary_tool": py.get("secondary_tool"),
            "metric_emitted_directly": py.get("metric_emitted_directly"),
            "derivation": py.get("derivation"),
        },
    }


def build() -> dict:
    if not CATALOG.is_file():
        raise SystemExit(f"Missing catalog: {CATALOG}. Run scripts/extract_workbook.py first.")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_primary: dict[str, list[dict]] = defaultdict(list)

    for raw in catalog["metrics"]:
        py = raw.get("languages", {}).get("python", {})
        primary = py.get("primary_tool")
        if not primary or not str(primary).strip():
            continue
        key = normalize_primary_tool_name(str(primary))
        by_primary[key].append(metric_payload(raw))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True)

    slug_map = assign_primary_tool_slugs(list(by_primary.keys()))
    manifest_tools: list[dict] = []
    for primary_name in sorted(by_primary, key=str.lower):
        metrics = by_primary[primary_name]
        slug = slug_map[primary_name]
        secondaries = sorted(
            {
                normalize_primary_tool_name(m["python"]["secondary_tool"])
                for m in metrics
                if m["python"].get("secondary_tool")
            },
            key=str.lower,
        )
        bundle = {
            "workbook": catalog.get("workbook"),
            "workbook_version": catalog.get("version"),
            "primary_tool": primary_name,
            "primary_tool_id": slug,
            "metric_count": len(metrics),
            "secondary_tools": secondaries,
            "metrics": metrics,
        }
        filename = f"{slug}.json"
        text = json.dumps(bundle, indent=2, ensure_ascii=False)
        (OUT_DIR / filename).write_text(text, encoding="utf-8")
        (PKG_DIR / filename).write_text(text, encoding="utf-8")
        manifest_tools.append(
            {
                "primary_tool": primary_name,
                "primary_tool_id": slug,
                "metric_count": len(metrics),
                "secondary_tools": secondaries,
                "file": filename,
            }
        )

    manifest = {
        "workbook": catalog.get("workbook"),
        "workbook_version": catalog.get("version"),
        "python_metric_count": catalog.get("python_metric_count"),
        "primary_tool_count": len(manifest_tools),
        "tools": manifest_tools,
    }
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False)
    (OUT_DIR / "manifest.json").write_text(manifest_text, encoding="utf-8")
    (PKG_DIR / "manifest.json").write_text(manifest_text, encoding="utf-8")

    return manifest


def main() -> None:
    manifest = build()
    print(
        f"Wrote {manifest['primary_tool_count']} primary-tool bundles -> {OUT_DIR} "
        f"and {PKG_DIR}"
    )


if __name__ == "__main__":
    main()
