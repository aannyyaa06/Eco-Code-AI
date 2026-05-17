<<<<<<< HEAD
"""
Measured execution: runs user Python in a **child process** via `energy_runner.py`.

⚠️ Not a full security sandbox — use Docker for untrusted code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.abspath(__file__))
_RUNNER = os.path.join(_ROOT, "energy_runner.py")


def _parse_ecocode_ai_json(combined: str) -> dict | None:
    """Parse `<<<ECOCODE_AI_JSON>>>` + JSON line protocol from mixed stdout/stderr."""
    lines = combined.replace("\r\n", "\n").split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "<<<ECOCODE_AI_JSON>>>":
            if i + 1 < len(lines):
                raw = lines[i + 1].strip()
                if raw.startswith("{"):
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        return None
    # Fallback: last line that looks like our payload
    for line in reversed(lines):
        s = line.strip()
        if s.startswith("{") and '"duration_sec"' in s:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                continue
    return None


def run_code_sandbox(code: str, timeout: int = 25, stdin_default: str = "12") -> dict:
    """Execute `code` in subprocess; return metrics dict for the dashboard."""
    try:
        from energy_runner import check_source_safety
    except ImportError:

        def check_source_safety(src: str) -> str | None:  # type: ignore[misc]
            return None

    err = check_source_safety(code)
    if err:
        return {
            "success": False,
            "ok": False,
            "error": err,
            "runtime": 0.0,
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }

    fd, path = tempfile.mkstemp(suffix="_ecocode_ai_user.py", prefix="ecocode_ai_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(code)
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
        env["ECOCODE_AI_STDIN_LINE"] = stdin_default

        proc = subprocess.run(
            [sys.executable, _RUNNER, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(8, timeout),
            cwd=_ROOT,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        data = _parse_ecocode_ai_json(blob)
        if data is None:
            tail = (blob.strip() or "(empty)")[-800:]
            return {
                "success": False,
                "ok": False,
                "error": f"No ECOCODE_AI JSON in subprocess output. Exit {proc.returncode}. Tail:\n{tail}",
                "runtime": 0.0,
                "emissions": 0.0,
                "memory_mb": 0.0,
                "cpu_percent": 0.0,
                "cpu_efficiency_score": 0.0,
                "raw": {"stdout": proc.stdout, "stderr": proc.stderr},
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "ok": False,
            "error": f"Timed out after {timeout}s (infinite loop or blocking I/O?)",
            "runtime": float(timeout),
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }
    except (OSError, ValueError) as e:
        return {
            "success": False,
            "ok": False,
            "error": str(e),
            "runtime": 0.0,
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    ok = bool(data.get("ok"))
    duration = float(data.get("duration_sec") or 0.0)
    emissions_kg = float(data.get("emissions_kg") or 0.0)
    mem_bytes = int(data.get("memory_peak_bytes") or data.get("rss_peak_bytes") or 0)
    mem_mb = mem_bytes / (1024 * 1024)

    measured = {
        "ok": ok,
        "duration_sec": duration,
        "emissions_kg": emissions_kg,
        "memory_peak_bytes": mem_bytes,
        "cpu_percent": float(data.get("cpu_percent") or 0.0),
        "cpu_efficiency_score": float(data.get("cpu_efficiency_score") or 0.0),
        "error": data.get("error"),
    }

    return {
        "success": ok,
        "ok": ok,
        "error": data.get("error"),
        "runtime": duration,
        "emissions": emissions_kg,
        "memory_mb": mem_mb,
        "cpu_percent": measured["cpu_percent"],
        "cpu_efficiency_score": measured["cpu_efficiency_score"],
        "raw": data,
        "measured": measured,
=======
"""
Measured execution: runs user Python in a **child process** via `energy_runner.py`.

⚠️ Not a full security sandbox — use Docker for untrusted code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.abspath(__file__))
_RUNNER = os.path.join(_ROOT, "energy_runner.py")


def _parse_ecocode_ai_json(combined: str) -> dict | None:
    """Parse `<<<ECOCODE_AI_JSON>>>` + JSON line protocol from mixed stdout/stderr."""
    lines = combined.replace("\r\n", "\n").split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "<<<ECOCODE_AI_JSON>>>":
            if i + 1 < len(lines):
                raw = lines[i + 1].strip()
                if raw.startswith("{"):
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        return None
    # Fallback: last line that looks like our payload
    for line in reversed(lines):
        s = line.strip()
        if s.startswith("{") and '"duration_sec"' in s:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                continue
    return None


def run_code_sandbox(code: str, timeout: int = 25, stdin_default: str = "12") -> dict:
    """Execute `code` in subprocess; return metrics dict for the dashboard."""
    try:
        from energy_runner import check_source_safety
    except ImportError:

        def check_source_safety(src: str) -> str | None:  # type: ignore[misc]
            return None

    err = check_source_safety(code)
    if err:
        return {
            "success": False,
            "ok": False,
            "error": err,
            "runtime": 0.0,
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }

    fd, path = tempfile.mkstemp(suffix="_ecocode_ai_user.py", prefix="ecocode_ai_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(code)
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
        env["ECOCODE_AI_STDIN_LINE"] = stdin_default

        proc = subprocess.run(
            [sys.executable, _RUNNER, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(8, timeout),
            cwd=_ROOT,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        data = _parse_ecocode_ai_json(blob)
        if data is None:
            tail = (blob.strip() or "(empty)")[-800:]
            return {
                "success": False,
                "ok": False,
                "error": f"No ECOCODE_AI JSON in subprocess output. Exit {proc.returncode}. Tail:\n{tail}",
                "runtime": 0.0,
                "emissions": 0.0,
                "memory_mb": 0.0,
                "cpu_percent": 0.0,
                "cpu_efficiency_score": 0.0,
                "raw": {"stdout": proc.stdout, "stderr": proc.stderr},
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "ok": False,
            "error": f"Timed out after {timeout}s (infinite loop or blocking I/O?)",
            "runtime": float(timeout),
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }
    except (OSError, ValueError) as e:
        return {
            "success": False,
            "ok": False,
            "error": str(e),
            "runtime": 0.0,
            "emissions": 0.0,
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "cpu_efficiency_score": 0.0,
            "raw": {},
        }
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    ok = bool(data.get("ok"))
    duration = float(data.get("duration_sec") or 0.0)
    emissions_kg = float(data.get("emissions_kg") or 0.0)
    mem_bytes = int(data.get("memory_peak_bytes") or data.get("rss_peak_bytes") or 0)
    mem_mb = mem_bytes / (1024 * 1024)

    measured = {
        "ok": ok,
        "duration_sec": duration,
        "emissions_kg": emissions_kg,
        "memory_peak_bytes": mem_bytes,
        "cpu_percent": float(data.get("cpu_percent") or 0.0),
        "cpu_efficiency_score": float(data.get("cpu_efficiency_score") or 0.0),
        "error": data.get("error"),
    }

    return {
        "success": ok,
        "ok": ok,
        "error": data.get("error"),
        "runtime": duration,
        "emissions": emissions_kg,
        "memory_mb": mem_mb,
        "cpu_percent": measured["cpu_percent"],
        "cpu_efficiency_score": measured["cpu_efficiency_score"],
        "raw": data,
        "measured": measured,
>>>>>>> 3ca4c4ed1728de16735324a5cc1c660905f89060
    }