"""Load Python metric rows exported from the strategy workbook."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

_PKG = "strategy_metrics"
_DATA_FILE = "python_metrics.json"


@dataclass(frozen=True, slots=True)
class PythonToolBinding:
    primary_tool: str | None
    secondary_tool: str | None
    metric_emitted_directly: str | None
    derivation: str | None


@dataclass(frozen=True, slots=True)
class MetricRecord:
    id: str
    sheet: str
    l1_strategy: str | None
    l2_testing_type: str | None
    l3_technique: str | None
    l4_classification: str | None
    l5_metric: str
    description: str | None
    derivation: str | None
    raw_measurement_formula: str | None
    expected_threshold: str | None
    normalization_formula: str | None
    execution_frequency: str | None
    python: PythonToolBinding

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MetricRecord:
        py = raw.get("languages", {}).get("python", {})
        return cls(
            id=raw["id"],
            sheet=raw["sheet"],
            l1_strategy=raw.get("l1_strategy"),
            l2_testing_type=raw.get("l2_testing_type"),
            l3_technique=raw.get("l3_technique"),
            l4_classification=raw.get("l4_classification"),
            l5_metric=raw["l5_metric"],
            description=raw.get("description"),
            derivation=raw.get("derivation"),
            raw_measurement_formula=raw.get("raw_measurement_formula"),
            expected_threshold=raw.get("expected_threshold"),
            normalization_formula=raw.get("normalization_formula"),
            execution_frequency=raw.get("execution_frequency"),
            python=PythonToolBinding(
                primary_tool=py.get("primary_tool"),
                secondary_tool=py.get("secondary_tool"),
                metric_emitted_directly=py.get("metric_emitted_directly"),
                derivation=py.get("derivation"),
            ),
        )


def _repo_data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / _DATA_FILE


def load_catalog_json() -> dict[str, Any]:
    path = _repo_data_path()
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    with resources.files(_PKG).joinpath(_DATA_FILE).open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_metrics() -> tuple[MetricRecord, ...]:
    payload = load_catalog_json()
    return tuple(MetricRecord.from_dict(m) for m in payload["metrics"])


def primary_tools_index() -> dict[str, list[str]]:
    """Map primary tool name → metric ids (Python column only)."""
    index: dict[str, list[str]] = {}
    for row in load_metrics():
        tool = row.python.primary_tool
        if not tool:
            continue
        key = tool.strip()
        index.setdefault(key, []).append(row.id)
    return index
