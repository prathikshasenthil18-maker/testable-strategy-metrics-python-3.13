from strategy_metrics.catalog import (
    load_metrics,
    load_primary_tool_bundle,
    load_primary_tools_manifest,
    primary_tools_index,
)
from strategy_metrics.derivations import apply_derivation, apply_metric_pipeline, normalize_score


def test_primary_tool_bundles_cover_workbook() -> None:
    manifest = load_primary_tools_manifest()
    assert manifest["primary_tool_count"] == 16
    assert sum(t["metric_count"] for t in manifest["tools"]) == 103
    beniget = load_primary_tool_bundle(primary_tool="Beniget")
    assert beniget["metric_count"] == 2
    assert all(m["python"]["primary_tool"] == "Beniget" for m in beniget["metrics"])


def test_catalog_has_python_primary_tools() -> None:
    metrics = load_metrics()
    assert len(metrics) >= 100
    tools = primary_tools_index()
    assert "Coverage.py" in tools or "Lizard" in tools
    assert all(m.python.primary_tool for m in metrics)


def test_decision_coverage_derivation() -> None:
    result = apply_derivation(
        "decision_coverage = covered_branches / max(num_branches, 1)",
        {"covered_branches": 8, "num_branches": 10},
    )
    assert result["ok"] is True
    assert result["value"] == 0.8


def test_execution_path_integrity_pipeline() -> None:
    row = next(m for m in load_metrics() if m.id.endswith("execution_path_integrity"))
    out = apply_metric_pipeline(
        derivation=row.derivation,
        normalization_formula=row.normalization_formula,
        variables={
            "functions_without_counterexample": 9,
            "total_functions_checked": 10,
            "CC": 5,
        },
    )
    assert out["derivation"]["ok"] is True
    assert out["derivation"]["value"] == 0.9


def test_max_normalization() -> None:
    score = normalize_score(
        "MAX(0, 100 – (Hotspot_Count × 15))",
        {"Hotspot_Count": 2},
    )
    assert score["ok"] is True
    assert score["score_0_100"] == 70.0
