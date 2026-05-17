<<<<<<< HEAD
"""Repository scan — delegates to `ecocode_ai_repo_scan` with dashboard-friendly keys."""

from __future__ import annotations

from ecocode_ai_repo_scan import format_repo_report, scan_repository as _deep_scan


def scan_repository(repo_path: str) -> dict:
    s = _deep_scan(repo_path)
    req_lines = int(s.get("requirements_lines") or 0)
    return {
        "total_size_mb": round(float(s.get("total_bytes") or 0) / (1024 * 1024), 2),
        "python_files": int(s.get("py_files") or 0),
        "heavy_scripts": len(s.get("heavy_python") or []),
        "duplicate_code_blocks": int(s.get("duplicate_blocks") or 0),
        "unused_dependencies": min(40, max(0, req_lines // 5)),
        "potential_energy_savings_percent": int(s.get("potential_savings_pct") or 0),
        "large_file_count": len(s.get("large_files") or []),
        "report_text": format_repo_report(s),
        "raw": s,
    }
=======
"""Repository scan — delegates to `ecocode_ai_repo_scan` with dashboard-friendly keys."""

from __future__ import annotations

from ecocode_ai_repo_scan import format_repo_report, scan_repository as _deep_scan


def scan_repository(repo_path: str) -> dict:
    s = _deep_scan(repo_path)
    req_lines = int(s.get("requirements_lines") or 0)
    return {
        "total_size_mb": round(float(s.get("total_bytes") or 0) / (1024 * 1024), 2),
        "python_files": int(s.get("py_files") or 0),
        "heavy_scripts": len(s.get("heavy_python") or []),
        "duplicate_code_blocks": int(s.get("duplicate_blocks") or 0),
        "unused_dependencies": min(40, max(0, req_lines // 5)),
        "potential_energy_savings_percent": int(s.get("potential_savings_pct") or 0),
        "large_file_count": len(s.get("large_files") or []),
        "report_text": format_repo_report(s),
        "raw": s,
    }
>>>>>>> 3ca4c4ed1728de16735324a5cc1c660905f89060
