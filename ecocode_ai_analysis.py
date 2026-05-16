"""AST analysis, Radon/Pylint hooks, refactor templates, Green Score, difficulty tiers."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any

# --- AST helpers (refactor + stats) ---


def _function_body_stmts(node: ast.FunctionDef) -> list[ast.stmt]:
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return body


def _if_returns_param_on_small_n(test: ast.AST, body: list[ast.stmt], param: str) -> bool:
    if not body or not isinstance(body[-1], ast.Return):
        return False
    ret = body[-1].value
    if not isinstance(ret, ast.Name) or ret.id != param:
        return False
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != param:
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], (ast.LtE, ast.Lt)):
        return False
    c = test.comparators[0]
    return isinstance(c, ast.Constant) and c.value in (1, 2)


def _is_naive_recursive_fibonacci(fn: ast.FunctionDef) -> bool:
    if len(fn.args.args) != 1:
        return False
    param = fn.args.args[0].arg
    stmts = _function_body_stmts(fn)
    if len(stmts) != 1 or not isinstance(stmts[0], ast.If):
        return False
    if_node = stmts[0]
    if not _if_returns_param_on_small_n(if_node.test, if_node.body, param):
        return False
    if len(if_node.orelse) != 1 or not isinstance(if_node.orelse[0], ast.Return):
        return False
    val = if_node.orelse[0].value
    if not isinstance(val, ast.BinOp) or not isinstance(val.op, ast.Add):
        return False
    left, right = val.left, val.right
    if not isinstance(left, ast.Call) or not isinstance(right, ast.Call):
        return False
    subs: list[int] = []
    for call in (left, right):
        if not isinstance(call.func, ast.Name) or call.func.id != fn.name:
            return False
        if len(call.args) != 1:
            return False
        arg0 = call.args[0]
        if not isinstance(arg0, ast.BinOp) or not isinstance(arg0.op, ast.Sub):
            return False
        if not isinstance(arg0.left, ast.Name) or arg0.left.id != param:
            return False
        if not isinstance(arg0.right, ast.Constant) or not isinstance(arg0.right.value, int):
            return False
        subs.append(arg0.right.value)
    return sorted(subs) == [1, 2]


def _find_naive_fib_function(tree: ast.AST) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _is_naive_recursive_fibonacci(node):
            return node
    return None


def _iterative_fib_source(fn_name: str) -> str:
    return (
        f"def {fn_name}(n: int) -> int:\n"
        '    """Iterative Fibonacci: O(n) time, O(1) extra space."""\n'
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    )


def heuristic_refactor(code: str) -> tuple[str, list[str], bool]:
    tree = ast.parse(code)
    fib_fn = _find_naive_fib_function(tree)
    if fib_fn is None:
        return (
            code,
            [
                "No structural auto-refactor matched.",
                "Supported: classic double-recursion Fibonacci → iterative O(n).",
                "Use **Energy Lab** + **Radon/Pylint** suggestions for other wins.",
            ],
            False,
        )
    if fib_fn.end_lineno is None:
        raise ValueError("AST needs end_lineno (Python 3.8+).")
    lines = code.splitlines()
    start = fib_fn.lineno - 1
    end = fib_fn.end_lineno
    new_block = _iterative_fib_source(fib_fn.name).rstrip("\n").splitlines()
    out = "\n".join(lines[:start] + new_block + lines[end:])
    notes = [
        f"Replaced exponential recursion in `{fib_fn.name}` with an iterative implementation.",
        "Asymptotic time improves from ~O(2^n) to O(n) for this pattern.",
    ]
    return out, notes, True


def _max_loop_nesting(tree: ast.AST) -> int:
    max_d = 0
    stack = 0

    class V(ast.NodeVisitor):
        def visit_For(self, node: ast.For) -> None:
            nonlocal stack, max_d
            stack += 1
            max_d = max(max_d, stack)
            self.generic_visit(node)
            stack -= 1

        def visit_While(self, node: ast.While) -> None:
            nonlocal stack, max_d
            stack += 1
            max_d = max(max_d, stack)
            self.generic_visit(node)
            stack -= 1

    V().visit(tree)
    return max_d


def _count_nodes(tree: ast.AST, types: tuple[type, ...]) -> int:
    return sum(1 for n in ast.walk(tree) if isinstance(n, types))


def _has_bare_except(tree: ast.AST) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler) and n.type is None:
            return True
    return False


def _has_sleep_in_loop(tree: ast.AST) -> bool:
    for loop in ast.walk(tree):
        if not isinstance(loop, (ast.For, ast.While)):
            continue
        for sub in ast.walk(loop):
            if isinstance(sub, ast.Call):
                fn = sub.func
                if isinstance(fn, ast.Attribute) and fn.attr == "sleep":
                    return True
                if isinstance(fn, ast.Name) and fn.id == "sleep":
                    return True
    return False


def _detect_range_len_pattern(tree: ast.AST) -> list[str]:
    """Suggest enumerate() when iterating range(len(x))."""
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        it = node.iter
        if not isinstance(it, ast.Call):
            continue
        if not isinstance(it.func, ast.Name) or it.func.id != "range":
            continue
        if len(it.args) != 1:
            continue
        a0 = it.args[0]
        if not isinstance(a0, ast.Call):
            continue
        if not isinstance(a0.func, ast.Name) or a0.func.id != "len":
            continue
        hits.append("Consider `for i, item in enumerate(seq):` instead of `for i in range(len(seq)):`")
    return hits[:5]


def _unused_import_names(tree: ast.AST) -> list[str]:
    """Very rough unused-import check (import name never read as Name)."""
    imported: set[str] = set()
    used: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            for alias in n.names:
                if alias.name == "*":
                    continue
                imported.add(alias.asname or alias.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            used.add(n.id)
    return sorted(imported - used)[:12]


@dataclass
class CodeStats:
    lines: int
    functions: int
    classes: int
    imports: int
    loops: int
    branches: int
    max_loop_depth: int
    naive_fib: bool
    bare_except: bool
    sleep_in_loop: bool
    typed_params_ratio: float
    docstring_coverage: float
    long_lines: int


def compute_code_stats(tree: ast.AST, source: str) -> CodeStats:
    lines = len(source.splitlines())
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    naive = _find_naive_fib_function(tree) is not None
    with_doc = sum(1 for f in funcs if ast.get_docstring(f))
    doc_cov = (with_doc / len(funcs)) if funcs else 1.0
    typed = 0
    total_args = 0
    for f in funcs:
        for a in f.args.args:
            total_args += 1
            if a.annotation is not None:
                typed += 1
    ratio = typed / total_args if total_args else 1.0
    long_lines = sum(1 for ln in source.splitlines() if len(ln) > 100)
    return CodeStats(
        lines=max(lines, 1),
        functions=len(funcs),
        classes=sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
        imports=sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))),
        loops=_count_nodes(tree, (ast.For, ast.While)),
        branches=_count_nodes(tree, (ast.If, ast.IfExp)),
        max_loop_depth=_max_loop_nesting(tree),
        naive_fib=naive,
        bare_except=_has_bare_except(tree),
        sleep_in_loop=_has_sleep_in_loop(tree),
        typed_params_ratio=ratio,
        docstring_coverage=doc_cov,
        long_lines=long_lines,
    )


def estimate_complexity_labels(tree: ast.AST) -> tuple[str, str]:
    if _find_naive_fib_function(tree):
        return "Time: O(2^n) (naive recursive Fibonacci)", "Space: O(n) stack"
    md = _max_loop_nesting(tree)
    loops = _count_nodes(tree, (ast.For, ast.While))
    if md >= 3:
        return f"Time: up to O(n^{md}) risk (loop nesting {md})", "Space: O(1)–O(n) depending on body"
    if loops >= 2 and md >= 2:
        return "Time: O(n²) or higher (nested loops)", "Space: O(1)–O(n)"
    if loops == 1:
        return "Time: O(n) typical (single loop)", "Space: O(1)"
    if loops > 1:
        return "Time: depends on loop independence", "Space: O(1)–O(n)"
    return "Time: O(1) (no loops)", "Space: O(1)"


def radon_average_complexity(source: str) -> float | None:
    try:
        from radon.complexity import cc_visit
    except ImportError:
        return None
    blocks = cc_visit(source)
    if not blocks:
        return None
    return sum(b.complexity for b in blocks) / len(blocks)


def pylint_messages_for_code(code: str, limit: int = 14) -> list[str]:
    try:
        fd, path = tempfile.mkstemp(suffix="_lint.py", prefix="ecocode_ai_", text=True)
        os.write(fd, code.encode("utf-8"))
        os.close(fd)
        proc = subprocess.run(
            [sys.executable, "-m", "pylint", "--exit-zero", "--score=n", "--output-format=json", path],
            capture_output=True,
            text=True,
            timeout=45,
        )
        os.remove(path)
        data = json.loads(proc.stdout or "[]")
        out: list[str] = []
        for item in data[:limit]:
            msg = item.get("message", "")
            sym = item.get("symbol", "")
            line = item.get("line", "")
            out.append(f"L{line} [{sym}] {msg}")
        return out
    except Exception:
        return []


def extended_suggestions(code: str, stats: CodeStats, radon_avg: float | None) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Fix syntax errors first."]
    out: list[str] = []
    if _find_naive_fib_function(tree):
        out.append("ML/heuristic: replace exponential Fibonacci with iteration or functools.lru_cache.")
    for h in _detect_range_len_pattern(tree):
        if h not in out:
            out.append(h)
    unused = _unused_import_names(tree)
    if unused:
        out.append(f"Naming/cleanliness: possibly unused imports — {', '.join(unused[:6])}")
    if stats.sleep_in_loop:
        out.append("Intermediate: `time.sleep` in a loop — consider async or batching.")
    if stats.max_loop_depth >= 3:
        out.append("Intermediate: deep nesting — consider NumPy vectorization or splitting functions.")
    if "torch" in code.lower() and stats.max_loop_depth >= 2:
        out.append("Advanced: PyTorch + nested Python loops — prefer batched ops / `.to(device)` patterns.")
    if re.search(r"\bcuda\b|\.cuda\(", code.lower()):
        out.append("Advanced: CUDA path — verify kernel fusion, batch size, and mixed precision (AMP).")
    if radon_avg and radon_avg >= 12:
        out.append(f"Intermediate: high cyclomatic complexity (~{radon_avg:.1f} avg) — simplify branches.")
    if re.search(r"\bfor\b.+\bfor\b", code) and stats.max_loop_depth >= 2:
        out.append("Detect nested loops — hoist invariants and cache repeated calculations (memoization).")
    if not out:
        out.append("No critical patterns — run **Energy Lab** for measured runtime and CO₂.")
    return out[:18]


@dataclass
class DifficultyReport:
    beginner: list[str] = field(default_factory=list)
    intermediate: list[str] = field(default_factory=list)
    advanced: list[str] = field(default_factory=list)


def classify_difficulty(code: str, stats: CodeStats, radon_avg: float | None) -> DifficultyReport:
    rep = DifficultyReport()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        rep.beginner.append("Syntax errors — fix before deeper review.")
        return rep
    unused = _unused_import_names(tree)
    if unused:
        rep.beginner.append(f"Unused import candidates: {', '.join(unused[:8])}")
    if stats.long_lines > 5:
        rep.beginner.append(f"Many long lines ({stats.long_lines}) — wrap / extract for readability.")
    if _detect_range_len_pattern(tree):
        rep.beginner.append("Style: `range(len(...))` → prefer `enumerate`.")
    if stats.naive_fib or (radon_avg and radon_avg > 10) or stats.sleep_in_loop:
        rep.intermediate.append("Algorithm / control-flow debt (Fibonacci, complexity, or sleep-in-loop).")
    if stats.max_loop_depth >= 3:
        rep.intermediate.append("Nested loop depth ≥ 3 — algorithmic optimization likely.")
    if "torch" in code.lower() or re.search(r"\bcuda\b", code.lower()):
        rep.advanced.append("GPU / framework code — review batching, streams, and kernel efficiency.")
    if "multiprocessing" in code or "Process(" in code:
        rep.advanced.append("Parallelism present — tune pool size vs. contention for energy.")
    return rep


def compute_green_score(stats: CodeStats, radon_avg: float | None, measured: dict[str, Any] | None) -> int:
    score = 38
    score += int(min(22, stats.docstring_coverage * 22))
    score += int(min(14, stats.typed_params_ratio * 14))
    score -= min(12, stats.long_lines // 3)
    if stats.naive_fib:
        score -= 20
    if stats.bare_except:
        score -= 8
    if stats.sleep_in_loop:
        score -= 6
    if radon_avg:
        score -= min(14, int(max(0, radon_avg - 4) * 1.1))
    if measured and measured.get("ok"):
        eff = float(measured.get("cpu_efficiency_score") or 0)
        score += int(min(12, eff * 1.1))
        dur = float(measured.get("duration_sec") or 0)
        if dur < 0.15:
            score += 4
    return max(0, min(100, score))


def analyze_energy_and_carbon_footprint(stats: CodeStats) -> tuple[float, float, float, dict[str, float]]:
    complexity_penalty = 8 * stats.max_loop_depth + 3 * stats.loops + 2 * stats.branches
    hygiene_penalty = 5 * stats.bare_except + 6 * stats.sleep_in_loop + 0.2 * stats.long_lines
    fib_penalty = 45.0 if stats.naive_fib else 0.0
    energy = 25.0 + complexity_penalty + hygiene_penalty + fib_penalty + 0.05 * stats.lines
    carbon = 0.35 * energy
    sustain = max(20.0, min(98.0, 92.0 - 0.35 * energy + 15 * stats.docstring_coverage + 10 * stats.typed_params_ratio))
    breakdown = {
        "control_flow": round(0.35 * energy, 1),
        "structure": round(0.28 * energy, 1),
        "maintainability_risk": round(0.22 * energy, 1),
        "io_sleep_patterns": round(0.15 * energy, 1),
    }
    return round(energy, 1), round(carbon, 1), round(sustain, 1), breakdown


def calculate_code_quality(stats: CodeStats) -> str:
    sc = 55
    sc += int(25 * stats.docstring_coverage)
    sc += int(15 * stats.typed_params_ratio)
    sc -= min(25, stats.long_lines)
    if stats.bare_except:
        sc -= 15
    if stats.sleep_in_loop:
        sc -= 10
    if stats.naive_fib:
        sc -= 12
    label = "Needs attention" if sc < 55 else "Fair" if sc < 72 else "Good" if sc < 85 else "Strong"
    return f"{label} (~{max(0, min(100, sc))}/100)"


def calculate_scalability(stats: CodeStats, time_cx: str) -> str:
    if stats.naive_fib or stats.max_loop_depth >= 3:
        return "Poor for large inputs (algorithmic bottleneck)"
    if "O(n²)" in time_cx or "n^" in time_cx:
        return "Moderate — validate with load tests"
    if stats.loops <= 1 and not stats.naive_fib:
        return "Good for typical growth"
    return "Fair — depends on workload"


def calculate_maintainability_index(stats: CodeStats) -> int:
    mi = 52 + int(28 * stats.docstring_coverage) + int(12 * stats.typed_params_ratio)
    mi -= min(18, stats.long_lines // 2)
    if stats.bare_except:
        mi -= 10
    return max(0, min(100, mi))


def calculate_test_coverage_heuristic(code: str) -> str:
    if re.search(r"\bpytest\b|\bunittest\b", code):
        return "~40% (tests referenced — heuristic)"
    return "N/A — use CI coverage for real %"


def template_generate(description: str) -> tuple[str, bool]:
    d = (description or "").lower()
    if "fibonacci" in d or re.search(r"\bfib\b", d):
        return (
            "def fibonacci(n: int) -> int:\n"
            '    """O(n) time, O(1) space."""\n'
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        a, b = b, a + b\n"
            "    return a\n\n"
            "if __name__ == '__main__':\n"
            "    print([fibonacci(i) for i in range(10)])\n",
            True,
        )
    if "prime" in d:
        return (
            "def primes_up_to(n: int) -> list[int]:\n"
            '    """Sieve — O(n log log n)."""\n'
            "    if n < 2:\n"
            "        return []\n"
            "    sieve = [True] * (n + 1)\n"
            "    sieve[0] = sieve[1] = False\n"
            "    for p in range(2, int(n ** 0.5) + 1):\n"
            "        if sieve[p]:\n"
            "            for m in range(p * p, n + 1, p):\n"
            "                sieve[m] = False\n"
            "    return [i for i, v in enumerate(sieve) if v]\n",
            True,
        )
    if "binary search" in d or "bisect" in d:
        return (
            "from bisect import bisect_left\n\n"
            "def binary_search(sorted_vals: list[int], x: int) -> int:\n"
            '    """O(log n)."""\n'
            "    i = bisect_left(sorted_vals, x)\n"
            "    if i != len(sorted_vals) and sorted_vals[i] == x:\n"
            "        return i\n"
            "    return -1\n",
            True,
        )
    return (
        "# Keywords: fibonacci | prime | binary search\n"
        "def placeholder():\n"
        "    pass\n",
        False,
    )


def multi_language_hint(repo_root: str) -> dict[str, int]:
    """Count non-Python source files for portfolio scope."""
    exts: dict[str, int] = {".java": 0, ".cpp": 0, ".cc": 0, ".c": 0, ".js": 0, ".ts": 0, ".go": 0}
    for root, _, files in os.walk(repo_root):
        if ".git" in root:
            continue
        for f in files:
            for ext in exts:
                if f.endswith(ext):
                    exts[ext] += 1
                    break
    return {k: v for k, v in exts.items() if v}
