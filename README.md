# Testable Strategy Metrics (Python 3.13)

Simple Python **3.13** library and CLI built from **Testable Strategy Metrics Mapping v0.2** (`Testable_Strategy_Metrics_Mapping_v0.2_19_may_2026 2.xlsx`).

It ships:

- **103 White Box metrics** with **Python primary/secondary tools**, sheet derivations, thresholds, and 0–100 normalization text (`data/python_metrics.json`).
- **16 primary-tool bundles** — full metric rows per workbook primary name (`data/primary_tools/*.json`, index in `data/primary_tools/manifest.json`).
- A small **derivation engine** that evaluates workbook formulas when you supply raw inputs.

## Requirements

- Python **3.13+**
- Dependencies: `pandas`, `openpyxl` (export script only)

## Install

```bash
pip install -e ".[dev]"
```

## Refresh data from the workbook

Place the xlsx at the path in `scripts/extract_workbook.py` (or edit `WORKBOOK`), then:

```bash
python scripts/extract_workbook.py
```

Rebuild primary-tool files only (after editing the catalog JSON):

```bash
python scripts/build_primary_tools_data.py
```

## CLI

```bash
# Python primary tools → metric counts
strategy-metrics list-tools

# Full data for one primary tool (slug or workbook name)
strategy-metrics show-tool Beniget
strategy-metrics show-tool coverage_dot_py

# Inspect one metric (tools + derivation)
strategy-metrics show structural_analysis_cyclomatic_complexity_decision_outcome_verification

# Apply derivation + normalization
strategy-metrics apply structural_analysis_cyclomatic_complexity_decision_outcome_verification "{\"covered_branches\": 8, \"num_branches\": 10}"
```

## Library

```python
from strategy_metrics import load_metrics, apply_metric_pipeline

row = load_metrics()[0]
apply_metric_pipeline(
    derivation=row.derivation,
    normalization_formula=row.normalization_formula,
    variables={"CC": 5},
)
```

## Tests

```bash
pytest
```
