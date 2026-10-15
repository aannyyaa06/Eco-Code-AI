"""
Isolated worker: executes a user .py file under CodeCarbon + tracemalloc + psutil.

Emits machine-readable output on stdout:
  <<<ECOCODE_AI_JSON>>>
  { ... one json object ... }

So parent parsers survive stray library logs on stdout/stderr.

Run: python energy_runner.py <path_to_snippet.py>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback

# Reduce noisy C++/TF-style logs leaking into streams when optional deps load
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("CODECARBON_LOG_LEVEL", "error")

BLOCK_PARTS = (
    "__import__",
    "importlib",
    "subprocess",
    "os.system",
    "socket.",
    "ctypes",
    "multiprocessing",
    "pickle.loads",
    "pty.",
    "commands.",
    "shell=True",
)


def check_source_safety(src: str) -> str | None:
    low = src.lower()
    for b in BLOCK_PARTS:
        if b.lower() in low:
            return f"Blocked for sandbox safety: {b!r}"
    # Avoid false positives from open("http...") in strings — only block obvious file open abuse
    if "open('/etc/" in low or 'open("/etc/' in low:
        return "Blocked: suspicious file open pattern"
    return None


def _emit(payload: dict) -> None:
    """Write protocol on stderr so user prints to stdout cannot corrupt JSON."""
    sys.stdout.flush()
    sys.stderr.flush()
    print("<<<ECOCODE_AI_JSON>>>", file=sys.stderr, flush=True)
    print(json.dumps(payload), file=sys.stderr, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to .py file to execute")
    args = ap.parse_args()
    path = args.path
    with open(path, encoding="utf-8") as f:
        src = f.read()
    err = check_source_safety(src)
    if err:
        _emit(
            {
                "ok": False,
                "error": err,
                "duration_sec": 0.0,
                "emissions_kg": 0.0,
                "memory_peak_bytes": 0,
                "rss_peak_bytes": 0,
                "cpu_percent": 0.0,
                "cpu_efficiency_score": 0.0,
            }
        )
        sys.exit(0)

    import tracemalloc

    tracemalloc.start()
    t0 = time.perf_counter()
    exec_err: str | None = None
    emissions = 0.0
    rss_peak = 0
    cpu_p = 0.0

    try:
        import psutil

        proc = psutil.Process()
        rss_start = proc.memory_info().rss
    except Exception:
        proc = None
        rss_start = 0

    def _sandbox_input(prompt: str = "") -> str:
        """Non-interactive runs: return a default so `int(input())` demos work."""
        return os.environ.get("ECOCODE_AI_STDIN_LINE", "12")

    try:
        from codecarbon import EmissionsTracker

        tracker = EmissionsTracker(
            project_name="ecocode_ai_sandbox",
            save_to_api=False,
            save_to_file=False,
        )
        tracker.start()
        try:
            code = compile(src, path, "exec")
            glob_ns: dict = {
                "__name__": "__main__",
                "__file__": path,
                "input": _sandbox_input,
            }
            exec(code, glob_ns, glob_ns)
        except Exception:
            exec_err = traceback.format_exc(limit=12)
        try:
            out = tracker.stop()
            emissions = float(out) if out is not None else 0.0
        except (TypeError, ValueError):
            emissions = 0.0
    except ImportError:
        exec_err = exec_err or "codecarbon not installed in worker environment"

    t1 = time.perf_counter()
    duration = round(t1 - t0, 6)

    try:
        _cur, tr_peak = tracemalloc.get_traced_memory()
    except ValueError:
        tr_peak = 0
    tracemalloc.stop()

    if proc is not None:
        try:
            rss_peak = max(rss_start, proc.memory_info().rss)
            cpu_p = float(proc.cpu_percent(interval=0.12))
        except Exception:
            rss_peak = rss_start
            cpu_p = 0.0

    mem_peak_bytes = int(max(tr_peak, rss_peak))
    eff = 10.0
    eff -= min(5.0, math.log1p(duration * 50.0))
    eff -= min(3.0, math.log1p(max(emissions, 1e-15) * 1e9))
    eff -= min(2.0, mem_peak_bytes / (200.0 * 1024 * 1024))
    eff = max(0.0, min(10.0, round(eff, 2)))

    _emit(
        {
            "ok": exec_err is None,
            "error": exec_err,
            "duration_sec": duration,
            "emissions_kg": round(emissions, 12),
            "memory_peak_bytes": mem_peak_bytes,
            "rss_peak_bytes": int(rss_peak),
            "cpu_percent": round(cpu_p, 2),
            "cpu_efficiency_score": eff,
        }
    )
    sys.exit(0 if exec_err is None else 1)


if __name__ == "__main__":
    main()
