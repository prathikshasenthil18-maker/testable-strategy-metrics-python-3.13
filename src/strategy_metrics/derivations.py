"""Evaluate workbook derivation and normalization expressions."""

from __future__ import annotations

import ast
import math
import re
from typing import Any

_ASSIGN_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$",
    re.DOTALL,
)


def _normalize_formula_text(text: str) -> str:
    s = text.strip()
    for ch in ("–", "−", "—"):
        s = s.replace(ch, "-")
    s = s.replace("×", "*").replace("÷", "/")
    s = re.sub(r"\bcapped\s+0\s*-\s*100\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[.*?\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.upper().startswith("SCORE ="):
        s = s.split("=", 1)[1].strip()
    return s


def parse_derivation(derivation: str | None) -> tuple[str | None, str | None]:
    """Return (output_variable, expression) from a sheet derivation line."""
    if not derivation or not derivation.strip():
        return None, None
    collapsed = re.sub(r"\s*\n\s*", " ", derivation.strip())
    m = _ASSIGN_RE.match(collapsed)
    if not m:
        return None, collapsed
    return m.group(1), m.group(2).strip()


class _SafeEval(ast.NodeVisitor):
    __slots__ = ("_names",)

    def __init__(self, names: dict[str, float]) -> None:
        self._names = names

    def visit(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in self._names:
                raise ValueError(f"Unknown variable: {node.id}")
            return float(self._names[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            val = self.visit(node.operand)
            return val if isinstance(node.op, ast.UAdd) else -val
        if isinstance(node, ast.BinOp):
            left, right = self.visit(node.left), self.visit(node.right)
            op = node.op
            if isinstance(op, ast.Add):
                return left + right
            if isinstance(op, ast.Sub):
                return left - right
            if isinstance(op, ast.Mult):
                return left * right
            if isinstance(op, ast.Div):
                return left / right
            if isinstance(op, ast.Pow):
                return left**right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = node.func.id
            args = [self.visit(a) for a in node.args]
            if fn == "max" and len(args) >= 1:
                return float(max(args))
            if fn == "min" and len(args) >= 1:
                return float(min(args))
            if fn == "abs" and len(args) == 1:
                return float(abs(args[0]))
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def evaluate_expression(expression: str, variables: dict[str, float | int]) -> float:
    """Evaluate a arithmetic expression with ``max`` / ``min`` / ``abs``."""
    expr = _normalize_formula_text(expression)
    expr = re.sub(r"\bMAX\s*\(", "max(", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bMIN\s*\(", "min(", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bABS\s*\(", "abs(", expr, flags=re.IGNORECASE)
    tree = ast.parse(expr, mode="eval")
    names = {k: float(v) for k, v in variables.items()}
    return _SafeEval(names).visit(tree)


def apply_derivation(
    derivation: str | None,
    variables: dict[str, float | int],
) -> dict[str, Any]:
    """Apply sheet derivation; returns raw value and metadata."""
    out_name, expr = parse_derivation(derivation)
    if expr is None:
        return {"ok": False, "reason": "empty_derivation"}
    try:
        value = evaluate_expression(expr, variables)
    except (ValueError, SyntaxError, ZeroDivisionError) as exc:
        return {"ok": False, "reason": str(exc), "expression": expr, "output": out_name}
    return {
        "ok": True,
        "output": out_name,
        "expression": expr,
        "value": value,
    }


def normalize_score(
    normalization_formula: str | None,
    variables: dict[str, float | int],
) -> dict[str, Any]:
    """Apply workbook normalisation formula (0–100) when evaluable."""
    if not normalization_formula or not normalization_formula.strip():
        return {"ok": False, "reason": "empty_normalization"}
    expr = _normalize_formula_text(normalization_formula)
    try:
        score = evaluate_expression(expr, variables)
        score = max(0.0, min(100.0, score))
    except (ValueError, SyntaxError, ZeroDivisionError) as exc:
        return {"ok": False, "reason": str(exc), "expression": expr}
    return {"ok": True, "expression": expr, "score_0_100": score}


def apply_metric_pipeline(
    *,
    derivation: str | None,
    normalization_formula: str | None,
    variables: dict[str, float | int],
) -> dict[str, Any]:
    """Run derivation then normalization using the same variable bag."""
    derived = apply_derivation(derivation, variables)
    norm_vars = dict(variables)
    if derived.get("ok") and derived.get("output"):
        norm_vars[derived["output"]] = derived["value"]
    normalized = normalize_score(normalization_formula, norm_vars)
    return {"derivation": derived, "normalization": normalized}
