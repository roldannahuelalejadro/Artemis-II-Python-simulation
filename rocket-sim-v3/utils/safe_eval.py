"""Restricted math expression evaluator for thrust functions."""

from __future__ import annotations

import math
from typing import Any, Dict

ALLOWED_NAMES = {
    "abs": abs,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan2,
    "ceil": math.ceil,
    "cos": math.cos,
    "degrees": math.degrees,
    "exp": math.exp,
    "floor": math.floor,
    "log": math.log,
    "max": max,
    "min": min,
    "pi": math.pi,
    "pow": pow,
    "radians": math.radians,
    "sin": math.sin,
    "sqrt": math.sqrt,
    "tan": math.tan,
}


def safe_eval(expr: str, context: Dict[str, Any] | None = None) -> float:
    """Evaluate a numeric expression with a constrained namespace."""
    if expr is None:
        return 0.0

    text = expr.strip()
    if not text:
        return 0.0

    names = dict(ALLOWED_NAMES)
    if context:
        names.update(context)

    try:
        value = eval(text, {"__builtins__": {}}, names)
    except Exception as exc:
        raise ValueError(f"Invalid expression '{expr}': {exc}") from exc

    if not isinstance(value, (int, float)):
        raise ValueError(f"Expression '{expr}' did not return a number")

    return float(value)
