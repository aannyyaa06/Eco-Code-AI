"""Repository-wide sustainability heuristics."""

from __future__ import annotations

import hashlib
import os
from collections import defaultdict


def _norm_block(lines: list[str]) -> str:
    return "\n".join(l.strip() for l in lines if l.strip())


def scan_repository(repo_root: str, max_files: int = 400) -> dict:
    """
    Heuristic scan: large files, duplicate 5-line blocks, heavy scripts,
    requirements size, dead-code hints.

    Always resolves repo_root to an absolute path so relative paths
    (e.g. "." or "../myproject") work correctly.

    Raises ValueError if the path does not exist or is not a directory.
    """

    # ── Resolve and validate path ──────────────────────────────────────────
    repo_root = os.path.abspath(repo_root)

    if not os.path.exists(repo_root):
        raise ValueError(f"Path does not exist: {repo_root!r}")

    if not os.path.isdir(repo_root):
        raise ValueError(f"Path is not a directory: {repo_root!r}")

    # ── Initialise report ──────────────────────────────────────────────────
    report: dict = {
        "large_files": [],
        "heavy_python": [],
        "duplicate_blocks": 0,
        "duplicate_examples": [],
        "requirements_lines": 0,
        "py_files": 0,
        "total_bytes": 0,
        "potential_savings_pct": 0,
        # debug helpers exposed to the dashboard
        "_scanned_root": repo_root,
        "_files_walked": 0,
    }

    block_hashes: dict[str, list[str]] = defaultdict(list)

    # ── Requirements size ──────────────────────────────────────────────────
    req_paths = ["requirements.txt", "pyproject.toml", "Pipfile"]
    for rp in req_paths:
        p = os.path.join(repo_root, rp)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    report["requirements_lines"] = max(
                        report["requirements_lines"], len(f.readlines())
                    )
            except OSError:
                pass

    # ── Walk the tree ──────────────────────────────────────────────────────
    EXCLUDED_DIRS = {
        ".git", "__pycache__", "node_modules",
        ".venv", "venv", "dist", "build", ".tox",
        ".mypy_cache", ".pytest_cache", "htmlcov",
    }

    count = 0
    for root, dirs, files in os.walk(repo_root, followlinks=False):

        # Prune excluded directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for name in files:

            if count >= max_files:
                break

            path = os.path.join(root, name)

            try:
                st = os.stat(path)
            except OSError:
                continue

            report["total_bytes"] += st.st_size
            report["_files_walked"] += 1
            rel = os.path.relpath(path, repo_root)

            if st.st_size > 350_000:
                report["large_files"].append(
                    {"path": rel, "kb": round(st.st_size / 1024, 1)}
                )

            if name.endswith(".py"):
                report["py_files"] += 1

                if st.st_size > 80_000:
                    report["heavy_python"].append(rel)

                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except OSError:
                    continue

                # Hash every 5-line sliding window to find duplicates
                for i in range(0, max(0, len(lines) - 4)):
                    chunk = lines[i: i + 5]
                    if not any(l.strip() for l in chunk):
                        continue
                    h = hashlib.sha256(
                        _norm_block(chunk).encode()
                    ).hexdigest()[:16]
                    block_hashes[h].append(f"{rel}:{i + 1}")

            count += 1

    # ── Duplicate block summary ────────────────────────────────────────────
    dup_total = 0
    examples: list[str] = []

    for h, locs in block_hashes.items():
        if len(locs) > 1:
            dup_total += len(locs) - 1
            if len(examples) < 6:
                examples.append(
                    f"{len(locs)}× similar block @ {locs[0]}"
                )

    report["duplicate_blocks"] = dup_total
    report["duplicate_examples"] = examples

    # ── Heuristic savings estimate ─────────────────────────────────────────
    savings = 5
    savings += min(25, len(report["large_files"]) * 4)
    savings += min(20, dup_total // 3)
    savings += min(15, len(report["heavy_python"]) * 5)
    if report["requirements_lines"] > 40:
        savings += 8
    report["potential_savings_pct"] = min(55, savings)

    return report


def format_repo_report(scan: dict) -> str:
    lines = [
        "Repository Sustainability Report",
        "----------------------------------",
        f"Scanned root   : {scan.get('_scanned_root', 'unknown')}",
        f"Files walked   : {scan.get('_files_walked', 0)}",
        f"Python files   : {scan.get('py_files', 0)}",
        f"Large files (>350 KB): {len(scan.get('large_files', []))}",
        f"Heavy .py (>80 KB)   : {len(scan.get('heavy_python', []))}",
        f"Duplicate logic blocks (5-line): {scan.get('duplicate_blocks', 0)}",
        f"Requirements-ish file lines    : {scan.get('requirements_lines', 0)}",
        f"Heuristic potential energy savings: {scan.get('potential_savings_pct', 0)}%",
        "",
        "Duplicate examples:",
    ]

    for ex in scan.get("duplicate_examples", [])[:5]:
        lines.append(f"  • {ex}")

    lines.append("")
    lines.append("Large files:")

    for lf in scan.get("large_files", [])[:5]:
        lines.append(f"  • {lf['path']} ({lf['kb']} KB)")

    lines.append("")
    lines.append("Heavy Python scripts:")

    for hp in scan.get("heavy_python", [])[:5]:
        lines.append(f"  • {hp}")

    return "\n".join(lines)