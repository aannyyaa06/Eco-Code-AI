"""AST + Radon + Pylint + ecocode_ai_analysis heuristics — no circular imports."""

from __future__ import annotations

import ast
import re

import ecocode_ai_analysis as ka


def analyze_complexity(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "cyclomatic_complexity": 0.0,
            "maintainability_index": 0.0,
            "time_complexity_estimate": "N/A (syntax error)",
            "space_complexity_estimate": "N/A",
            "syntax_error": True,
        }
    t, sp = ka.estimate_complexity_labels(tree)
    rad = ka.radon_average_complexity(code)
    avg_cc = float(rad) if rad is not None else 1.0
    mi_val = 72.0
    try:
        from radon.metrics import mi_visit

        mi_val = float(mi_visit(code, multi=False))
    except Exception:
        pass
    return {
        "cyclomatic_complexity": round(avg_cc, 2),
        "maintainability_index": round(mi_val, 1),
        "time_complexity_estimate": t,
        "space_complexity_estimate": sp,
    }


def get_ml_assisted_suggestions(code: str) -> list[dict[str, str]]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [{"level": "Beginner", "message": "Fix syntax errors before deeper suggestions."}]
    stats = ka.compute_code_stats(tree, code)
    rad = ka.radon_average_complexity(code)
    diff = ka.classify_difficulty(code, stats, rad)
    out: list[dict[str, str]] = []
    for m in diff.beginner:
        out.append({"level": "Beginner", "message": m})
    for m in diff.intermediate:
        out.append({"level": "Intermediate", "message": m})
    for m in diff.advanced:
        out.append({"level": "Advanced", "message": m})
    seen: set[str] = {d["message"] for d in out}
    for s in ka.pylint_messages_for_code(code, limit=10):
        if s not in seen:
            out.append({"level": "Beginner", "message": f"Pylint: {s}"})
            seen.add(s)
    for s in ka.extended_suggestions(code, stats, rad):
        if s not in seen:
            out.append({"level": "Intermediate", "message": s})
            seen.add(s)
    return out[:28]


def generate_optimized_code(code: str) -> str:
    """Best-effort transforms for the Before/After simulator (safe patterns only)."""
    try:
        new_code, _notes, changed = ka.heuristic_refactor(code)
        if changed:
            return new_code
    except SyntaxError:
        return code

    optimized = code
    if "for i in range(len(" in optimized:
        lines = optimized.split("\n")
        for idx, line in enumerate(lines):
            match = re.search(r"for\s+(\w+)\s+in\s+range\(len\((.*?)\)\)\s*:", line)
            if match:
                var_name, arr_name = match.group(1), match.group(2)
                lines[idx] = line.replace(
                    f"for {var_name} in range(len({arr_name})):",
                    f"for {var_name}, _item in enumerate({arr_name}):",
                )
        optimized = "\n".join(lines)

    if re.search(r"\bdef\s+(fib|fibonacci)", optimized) and "lru_cache" not in optimized:
        optimized = "from functools import lru_cache\n\n@lru_cache(maxsize=None)\n" + optimized

    return optimized
