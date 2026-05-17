<<<<<<< HEAD
"""
Project EcoCode AI — sustainability analysis platform (Streamlit).

Measured runs use `energy_runner.py` + CodeCarbon in a subprocess.
Static analysis uses `ai_analysis` (AST, Radon, Pylint hooks).
Gemini AI integration added for sustainability optimization.
"""

from __future__ import annotations

import ast
import logging
import os
from typing import Any
from urllib.parse import urlparse

import ecocode_ai_analysis as ka
import ecocode_ai_leaderboard
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import pdf_generator
import refactor_engine
import repo_analyzer
import sandbox

# =========================================
# GEMINI AI
# =========================================

from gemini_analyzer import analyze_code, optimize_code


# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    filename="sustainability_dashboard.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

LOG_PATH = os.path.join(
    os.getcwd(),
    "sustainability_dashboard.log"
)


# =========================================
# SESSION STATE
# =========================================

def init_session_state() -> None:

    for k, v in {
        "user_code": "",
        "last_analysis_ok": False,
        "sandbox_results": None,
        "complexity_metrics": None,
        "suggestions": [],
        "green_score": 0,
        "measure_history": [],
        "last_repo_path": "",
        "ecocode_ai_stdin_line": "12",
    }.items():

        st.session_state.setdefault(k, v)

    if "editor_code" not in st.session_state:

        st.session_state.editor_code = (
            st.session_state.get("user_code", "")
        )

    st.session_state.setdefault("editor_desc", "")


# =========================================
# GIT VALIDATION
# =========================================

def _is_valid_git_url(url: str) -> bool:

    u = urlparse(url.strip())

    return bool(
        u.scheme in ("http", "https")
        and u.netloc
    )


# =========================================
# THEME
# =========================================

def inject_theme_css() -> None:

    st.markdown(
        """<style>
        h1, h2, h3 { color: #22c55e !important; font-weight: 800; }
        .stApp { background: radial-gradient(circle at top left, #1e293b 0%, #020617 45%, #000000 100%); color: white; }
        section[data-testid="stSidebar"] { background: rgba(2,6,23,0.95); border-right: 1px solid rgba(255,255,255,0.06); }
        div[data-testid="metric-container"] { background: rgba(17,24,39,0.8); border-radius: 22px; border: 1px solid rgba(255,255,255,0.06); padding: 24px; box-shadow: 0 6px 18px rgba(0,0,0,0.22); }
        .stButton > button { background: linear-gradient(90deg, #16a34a, #22c55e); color: white; border: none; border-radius: 16px; padding: 14px 18px; font-size: 16px; font-weight: 700; width: 100%; box-shadow: 0 6px 20px rgba(34,197,94,0.2); }
        .stButton > button:hover { transform: scale(1.03); box-shadow: 0 10px 28px rgba(34,197,94,0.32); }
        button[data-baseweb="tab"] { background: rgba(17,24,39,0.7); border-radius: 16px; margin-right: 10px; padding: 12px 20px; color: #cbd5e1; font-weight: 700; }
        button[data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(90deg, #16a34a, #22c55e); color: white; }
        .stTextArea textarea { background: rgba(17,24,39,0.75) !important; color: white !important; border-radius: 20px !important; border: 1px solid rgba(255,255,255,0.06) !important; }
        .streamlit-expanderHeader { background: rgba(17,24,39,0.75); border-radius: 16px; color: white !important; }
        </style>""",
        unsafe_allow_html=True,
    )


# =========================================
# FULL ANALYSIS
# =========================================

def analyze_code_full(code: str) -> None:

    with st.spinner(
        "Running sandbox + sustainability analysis..."
    ):

        sandbox_res = sandbox.run_code_sandbox(
            code,
            timeout=28,
            stdin_default=str(
                st.session_state.get(
                    "ecocode_ai_stdin_line",
                    "12"
                )
            ).strip()
            or "12",
        )

        st.session_state.sandbox_results = sandbox_res

        measured = sandbox_res.get("measured") or {}

        try:

            tree = ast.parse(code)

        except SyntaxError as e:

            st.session_state.last_analysis_ok = False

            st.error(
                f"⚠️ **Syntax error in your code** — line {e.lineno}: {e.msg}\n\n"
                "Please fix the error in the Editor and try again."
            )

            return

        stats = ka.compute_code_stats(tree, code)

        rad = ka.radon_average_complexity(code)

        use_measured = (
            measured
            if isinstance(measured, dict)
            and measured.get("ok")
            else None
        )

        st.session_state.green_score = (
            ka.compute_green_score(
                stats,
                rad,
                use_measured
            )
        )

        st.session_state.code_stats = stats

        st.session_state.difficulty = (
            ka.classify_difficulty(
                code,
                stats,
                rad
            )
        )

        st.session_state.complexity_metrics = (
            refactor_engine.analyze_complexity(code)
        )

        st.session_state.suggestions = (
            refactor_engine.get_ml_assisted_suggestions(code)
        )

        st.session_state.last_analysis_ok = True

        st.session_state.user_code = code

        st.success(
            "Analysis complete."
        )


# =========================================
# REFACTOR
# =========================================

def refactor_code(code: str) -> None:

    st.markdown(
        "#### Refactored output"
    )

    try:

        new_code, notes, changed = (
            ka.heuristic_refactor(code)
        )

    except SyntaxError as e:

        st.error(f"Invalid Python: {e}")

        return

    for n in notes:

        st.caption(n)

    # =========================================
    # COMPLEXITY ANALYSIS (refactor_engine)
    # =========================================

    complexity = refactor_engine.analyze_complexity(code)

    st.json(complexity)

    # =========================================
    # OPTIMIZED CODE (refactor_engine)
    # =========================================

    opt = refactor_engine.generate_optimized_code(code)

    # =========================================
    # ML SUGGESTIONS (refactor_engine)
    # =========================================

    suggestions = refactor_engine.get_ml_assisted_suggestions(code)

    for s in suggestions:

        st.info(
            f"[{s['level']}] {s['message']}"
        )

    if opt != code:

        st.code(
            opt,
            language="python"
        )

    else:

        st.code(
            code,
            language="python"
        )


# =========================================
# WORKSPACE
# =========================================

def render_workspace() -> None:

    st.markdown(
        "## 🧪 Workspace"
    )

    user_code = st.text_area(
        "Editor",
        height=300,
        placeholder="Paste Python code here..."
    )

    # ── Live syntax check while typing ───────────────────────────────────────
    if user_code.strip():
        try:
            ast.parse(user_code.strip())
            st.success("✅ Syntax OK")
        except SyntaxError as _syn:
            st.error(
                f"⚠️ **Syntax error in your code** — line {_syn.lineno}: {_syn.msg}\n\n"
                f"```\n{_syn.text or ''}\n{'~' * max(0, (_syn.offset or 1) - 1)}^\n```\n\n"
                "Fix the error above before running analysis."
            )

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "Analyze (measured + static)",
            type="primary",
            use_container_width=True
        ):

            if user_code.strip():

                analyze_code_full(
                    user_code.strip()
                )

            else:

                st.error(
                    "Add code first."
                )

    with b2:

        if st.button(
            "Refactor (safe transforms)",
            use_container_width=True
        ):

            if user_code.strip():

                refactor_code(
                    user_code.strip()
                )

            else:

                st.error(
                    "Nothing to refactor."
                )


# =========================================
# GEMINI TAB
# =========================================

def render_gemini_tab() -> None:

    st.markdown(
        "## ✨ Gemini AI Sustainability Engine"
    )

    st.caption(
        "Analyze inefficient code and generate greener optimized implementations using Gemini AI."
    )

    gemini_code = st.text_area(
        "Paste Python code for Gemini analysis",
        height=260,
        key="gemini_code_input"
    )

    c1, c2 = st.columns(2)

    # =========================================
    # ANALYSIS
    # =========================================

    with c1:

        if st.button(
            "🔍 Gemini Sustainability Analysis",
            use_container_width=True
        ):

            if gemini_code.strip() == "":

                st.warning(
                    "Please paste Python code."
                )

            else:

                with st.spinner(
                    "Gemini analyzing sustainability..."
                ):

                    analysis = analyze_code(
                        gemini_code
                    )

                st.success(
                    "Gemini analysis complete."
                )

                with st.expander(
                    "🧠 Gemini Sustainability Report",
                    expanded=True
                ):

                    st.markdown(
                        analysis
                    )

    # =========================================
    # OPTIMIZATION
    # =========================================

    with c2:

        if st.button(
            "⚡ Generate Green Optimized Code",
            use_container_width=True
        ):

            if gemini_code.strip() == "":

                st.warning(
                    "Please paste Python code."
                )

            else:

                with st.spinner(
                    "Generating optimized code..."
                ):

                    optimized = optimize_code(
                        gemini_code
                    )

                st.success(
                    "Optimization complete."
                )

                with st.expander(
                    "♻ Gemini Optimized Code",
                    expanded=True
                ):

                    st.markdown(
                        optimized
                    )


# =========================================
# METRICS TAB
# =========================================

def render_metrics_tab() -> None:

    if not st.session_state.get(
        "last_analysis_ok"
    ):

        st.info(
            "Run analysis first."
        )

        return

    sb = st.session_state.sandbox_results or {}

    st.markdown(
        f"## 🌿 Green Score: {st.session_state.get('green_score', 0)} / 100"
    )

    st.progress(
        int(
            st.session_state.get(
                "green_score",
                0
            )
        ) / 100.0
    )

    # =========================================
    # GREEN SCORE GAUGE (Feature 4)
    # =========================================

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=st.session_state.get(
                "green_score",
                0
            ),
            title={"text": "Green Sustainability Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#22c55e"},
                "steps": [
                    {"range": [0, 40], "color": "#7f1d1d"},
                    {"range": [40, 70], "color": "#78350f"},
                    {"range": [70, 100], "color": "#14532d"},
                ],
            },
        )
    )

    fig.update_layout(
        template="plotly_dark",
        height=350,
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =========================================
    # SANDBOX METRICS
    # =========================================

    if sb.get("success"):

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Runtime",
            f"{sb.get('runtime', 0):.4f} s"
        )

        m2.metric(
            "Memory",
            f"{sb.get('memory_mb', 0):.2f} MB"
        )

        m3.metric(
            "CPU %",
            f"{sb.get('cpu_percent', 0):.1f}"
        )

        m4.metric(
            "CO₂",
            f"{float(sb.get('emissions') or 0):.8f} kg"
        )

    # =========================================
    # PDF REPORT (Feature 1)
    # =========================================

    st.markdown("---")

    if st.button(
        "📄 Generate Sustainability Report"
    ):

        metrics = {

            "Green Score": st.session_state.get(
                "green_score",
                0
            ),

            "Runtime": sb.get(
                "runtime",
                0
            ),

            "Memory MB": sb.get(
                "memory_mb",
                0
            ),

            "CPU Percent": sb.get(
                "cpu_percent",
                0
            ),

            "CO2 Emissions": sb.get(
                "emissions",
                0
            ),
        }

        pdf_bytes = (
            pdf_generator.generate_pdf_report(
                metrics,
                st.session_state.get(
                    "suggestions",
                    []
                )
            )
        )

        st.download_button(

            label="⬇ Download PDF Report",

            data=pdf_bytes,

            file_name="ecocode_ai_report.pdf",

            mime="application/pdf"
        )


# =========================================
# SIMULATOR
# =========================================

def render_simulator_tab() -> None:

    from plotly.subplots import make_subplots

    st.markdown("## ⚡ Before vs After Simulator")

    st.caption(
        "Paste a short Python snippet. The simulator runs it, auto-optimizes it, "
        "then runs the optimized version and compares runtime and CO₂ side-by-side.  \n"
        "⚠️ Keep snippets **fast** (< 5 s) — slow/infinite loops will be killed by the timeout."
    )

    code = st.text_area(
        "Code (before)",
        height=160,
        key="sim_code",
        placeholder="# Paste a short Python snippet here\nfor i in range(1000):\n    x = i * i",
    )

    if st.button("Run comparison", type="primary"):

        if not code.strip():
            st.warning("Paste some Python code first.")
            return

        # ── Syntax check before wasting time running ──────────────────────
        try:
            ast.parse(code)
        except SyntaxError as e:
            st.error(f"⚠️ Syntax error on line {e.lineno}: {e.msg} — fix it before running.")
            return

        TIMEOUT = 60  # seconds — tight so timeouts are obvious not silent

        # ── Helper: extract normalised metrics from sandbox result dict ──────
        def _extract(res: dict) -> tuple[float, float, float, bool]:
            """
            Returns (runtime_s, co2_ukg, memory_mb, timed_out).
            sandbox.py sets success=False and error="Timed out …" on timeout,
            and also sets runtime = float(timeout) as a sentinel — we detect
            EITHER signal so we never plot the meaningless ceiling value.
            """
            ok        = bool(res.get("success") or res.get("ok"))
            err_str   = str(res.get("error") or "").lower()
            timed_out = (not ok) and ("timed out" in err_str or "timeout" in err_str)

            rt    = max(0.0, float(res.get("runtime") or 0))
            em_kg = max(0.0, float(res.get("emissions") or 0))
            co2   = em_kg * 1_000_000          # convert kg → µkg for display
            mem   = max(0.0, float(res.get("memory_mb") or 0))

            return rt, co2, mem, timed_out

        # ── Run BEFORE ─────────────────────────────────────────────────────
        with st.spinner("⏳ Running original code…"):
            try:
                before = sandbox.run_code_sandbox(code, timeout=TIMEOUT)
            except Exception as exc:
                st.error(f"Sandbox error: {exc}")
                return

        runtime_before, co2_before, mem_before, before_timed_out = _extract(before)

        if before_timed_out:
            st.error(
                f"⏱ **Original code timed out** (>{TIMEOUT} s).  \n\n"
                f"Sandbox message: `{before.get('error', '')}`  \n\n"
                "The chart would show meaningless flat bars — paste a "
                "**shorter / faster snippet** and try again."
            )
            return

        if not before.get("success"):
            err = before.get("error") or "Unknown sandbox error"
            st.error(f"❌ Original code failed to run:\n```\n{err}\n```")
            return

        # ── Optimize ────────────────────────────────────────────────────────
        after_code = refactor_engine.generate_optimized_code(code)

        # ── Run AFTER ──────────────────────────────────────────────────────
        with st.spinner("⚡ Running optimized code…"):
            try:
                after = sandbox.run_code_sandbox(after_code, timeout=TIMEOUT)
            except Exception as exc:
                st.error(f"Sandbox error (after): {exc}")
                return

        runtime_after, co2_after, mem_after, after_timed_out = _extract(after)

        if after_timed_out:
            st.warning(
                f"⏱ Optimized code also timed out (>{TIMEOUT} s). "
                "Runtime capped at timeout; CO₂ shown as 0."
            )
            runtime_after = float(TIMEOUT)
            co2_after     = 0.0
            mem_after     = 0.0

        # ── Show optimized code ─────────────────────────────────────────────
        with st.expander("🔧 Optimized code (After)", expanded=False):
            st.code(after_code, language="python")

        # ── Compute improvement % ───────────────────────────────────────────
        def pct_change(before_val: float, after_val: float) -> str:
            if before_val == 0:
                return "N/A"
            pct = (before_val - after_val) / before_val * 100
            sign = "↓" if pct >= 0 else "↑"
            return f"{sign} {abs(pct):.1f}%"

        # ── Metric cards ────────────────────────────────────────────────────
        st.markdown("### 📊 Results")

        m1, m2, m3, m4, m5, m6 = st.columns(6)

        m1.metric("⏱ Runtime Before",  f"{runtime_before:.4f} s")
        m2.metric("⏱ Runtime After",   f"{runtime_after:.4f} s",
                  delta=f"{runtime_after - runtime_before:+.4f} s",
                  delta_color="inverse")
        m3.metric("🌍 CO₂ Before (µkg)", f"{co2_before:.6f}")
        m4.metric("🌍 CO₂ After (µkg)",  f"{co2_after:.6f}",
                  delta=f"{co2_after - co2_before:+.6f}",
                  delta_color="inverse")
        m5.metric("💾 Mem Before",  f"{mem_before:.2f} MB")
        m6.metric("💾 Mem After",   f"{mem_after:.2f} MB",
                  delta=f"{mem_after - mem_before:+.2f} MB",
                  delta_color="inverse")

        # ── Improvement summary banner ───────────────────────────────────────
        rt_pct  = pct_change(runtime_before, runtime_after)
        co2_pct = pct_change(co2_before, co2_after)
        st.info(
            f"**Runtime improvement:** {rt_pct}  |  "
            f"**CO₂ improvement:** {co2_pct}"
        )

        st.markdown("---")

        # ── Subplot chart ────────────────────────────────────────────────────
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("⏱ Runtime (seconds)", "🌍 CO₂ Emissions (µkg)")
        )

        fig.add_trace(go.Bar(
            name="Runtime Before", x=["Before"], y=[runtime_before],
            marker_color="#6366f1",
            text=[f"{runtime_before:.4f}s"], textposition="outside"
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            name="Runtime After", x=["After"], y=[runtime_after],
            marker_color="#22c55e",
            text=[f"{runtime_after:.4f}s"], textposition="outside"
        ), row=1, col=1)

        # CO₂ chart — only render if we have real data, else show a note
        if co2_before == 0 and co2_after == 0:
            fig.add_annotation(
                text="CO₂ data unavailable<br>(CodeCarbon returned 0)",
                xref="x2", yref="y2", x=0.5, y=0.5,
                showarrow=False, font=dict(color="#94a3b8", size=13),
                xanchor="center"
            )
            # Still add invisible bars so axes render cleanly
            fig.add_trace(go.Bar(
                name="CO₂ Before", x=["Before"], y=[0.001],
                marker_color="#f97316", opacity=0,
                text=["0.000000"], textposition="outside"
            ), row=1, col=2)
            fig.add_trace(go.Bar(
                name="CO₂ After", x=["After"], y=[0.001],
                marker_color="#22c55e", opacity=0,
                text=["0.000000"], textposition="outside"
            ), row=1, col=2)
        else:
            fig.add_trace(go.Bar(
                name="CO₂ Before", x=["Before"], y=[co2_before],
                marker_color="#f97316",
                text=[f"{co2_before:.6f}"], textposition="outside"
            ), row=1, col=2)
            fig.add_trace(go.Bar(
                name="CO₂ After", x=["After"], y=[co2_after],
                marker_color="#22c55e",
                text=[f"{co2_after:.6f}"], textposition="outside"
            ), row=1, col=2)

        fig.update_layout(
            title="⚡ Before vs After Sustainability Comparison",
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="white"),
            height=500,
            showlegend=True,
            legend_title="Comparison",
        )

        # Force y-axes to start at 0 — no negative values
        fig.update_yaxes(title_text="Seconds",         rangemode="tozero", row=1, col=1)
        fig.update_yaxes(title_text="Micrograms CO₂",  rangemode="tozero", row=1, col=2)

        st.plotly_chart(fig, use_container_width=True)


# =========================================
# LEARN TAB
# =========================================

def render_learn_tab() -> None:

    st.markdown(
        "## 📘 Learn Optimization"
    )

    st.info(
        "Learn how greener software reduces energy consumption and digital waste."
    )


# =========================================
# LEADERBOARD
# =========================================

def render_leaderboard_tab() -> None:

    st.markdown(
        "## 🏆 Green Leaderboard"
    )

    # =========================================
    # SUBMIT SCORE (Feature 5)
    # =========================================

    name = st.text_input(
        "Name"
    )

    if st.button(
        "Submit Green Score"
    ):

        ecocode_ai_leaderboard.add_entry(

            name=name,

            green_score=st.session_state.get(
                "green_score",
                0
            ),

            reduction_pct=20,

            note="Optimized with Project EcoCode AI"
        )

        st.success(
            "Leaderboard updated."
        )

    st.markdown("---")

    entries = (
        ecocode_ai_leaderboard.load_entries()
    )

    if entries:

        df = pd.DataFrame(entries)

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.caption(
            "No entries yet."
        )


# =========================================
# REPO TAB (Feature 3)
# =========================================

def _is_github_url(s: str) -> bool:
    """Return True if the string looks like a GitHub/Git URL."""
    s = s.strip()
    return (
        s.startswith("https://github.com")
        or s.startswith("http://github.com")
        or s.startswith("git@github.com")
        or s.endswith(".git")
    )


def _display_scan_results(results: dict, label: str) -> None:
    """Shared helper — renders metrics + report for a completed scan."""
    raw = results.get("raw", {})

    if results["python_files"] == 0 and results["total_size_mb"] == 0.0:
        st.warning(
            "⚠️ Scan completed but found **0 Python files** and 0 bytes.\n\n"
            f"Directory scanned: `{label}`\n"
            "Possible causes:\n"
            "- The folder is empty\n"
            "- All sub-folders are excluded (`.git`, `venv`, `__pycache__`)\n"
            "- No `.py` files exist in this tree\n\n"
            "Try pointing to the root of your Python project."
        )
        return

    st.success(f"✅ Repository scan complete — `{label}`")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🐍 Python Files",        results["python_files"])
    c2.metric("♊ Duplicate Blocks",     results["duplicate_code_blocks"])
    c3.metric("⚡ Potential Savings",    f"{results['potential_energy_savings_percent']}%")
    c4.metric("📦 Total Size",           f"{results['total_size_mb']} MB")
    c5.metric("🏋 Heavy Scripts",        results["heavy_scripts"])

    d1, d2 = st.columns(2)
    d1.metric("📋 Unused Dependencies (est.)", results["unused_dependencies"])
    d2.metric("📁 Large Files (>350 KB)",       results["large_file_count"])

    st.markdown("---")
    st.text_area("📄 Repository Report", results["report_text"], height=300)

    dup_examples = raw.get("duplicate_examples", [])
    if dup_examples:
        with st.expander(f"♊ Duplicate Block Locations ({len(dup_examples)} shown)"):
            for ex in dup_examples:
                st.caption(f"• {ex}")

    large_files = raw.get("large_files", [])
    if large_files:
        with st.expander(f"📁 Large Files ({len(large_files)} found)"):
            st.dataframe(pd.DataFrame(large_files), use_container_width=True)

    heavy = raw.get("heavy_python", [])
    if heavy:
        with st.expander(f"🏋 Heavy Python Scripts ({len(heavy)} found)"):
            for h in heavy:
                st.caption(f"• {h}")


def render_repo_tab() -> None:

    st.markdown("## 🔗 Repository Scan")

    st.caption(
        "Paste a **GitHub URL** to clone & scan, "
        "or enter an **absolute local path** to scan directly."
    )

    col_a, col_b = st.columns([3, 1])

    with col_a:
        repo_input = st.text_input(
            "GitHub URL or Local Path",
            placeholder="https://github.com/user/repo  OR  C:\\Users\\you\\myproject",
            label_visibility="collapsed",
        )

    with col_b:
        scan_clicked = st.button("🔍 Scan", type="primary", use_container_width=True)

    # ── Live feedback while user types ───────────────────────────────────────
    if repo_input.strip():
        val = repo_input.strip()
        if _is_github_url(val):
            st.info(f"🌐 Detected GitHub URL — will clone and scan: `{val}`")
        else:
            resolved = os.path.abspath(val)
            if not os.path.exists(resolved):
                st.error(
                    f"❌ Local path not found: `{resolved}`  \n"
                    "Tip: if you want to scan a GitHub repo, paste the full `https://github.com/...` URL instead."
                )
            elif not os.path.isdir(resolved):
                st.error(f"❌ That path is a file, not a folder: `{resolved}`")
            else:
                try:
                    n = len(os.listdir(resolved))
                    st.success(f"✅ Local path found — {n} items at top level.")
                except PermissionError:
                    st.error("❌ Permission denied reading that directory.")

    # ── Scan button logic ─────────────────────────────────────────────────────
    if scan_clicked:

        val = repo_input.strip()

        if not val:
            st.warning("Enter a GitHub URL or local path first.")
            return

        # ── Branch A: GitHub URL ──────────────────────────────────────────────
        if _is_github_url(val):

            import shutil
            import tempfile

            # Make sure it ends with .git for GitPython
            clone_url = val if val.endswith(".git") else val

            tmp_dir = tempfile.mkdtemp(prefix="ecocode_ai_clone_")

            try:
                with st.spinner(f"Cloning `{clone_url}` …"):
                    try:
                        Repo.clone_from(clone_url, tmp_dir)
                    except GitCommandError as e:
                        st.error(
                            f"❌ Git clone failed.\n\n"
                            f"Error: `{e}`\n\n"
                            "Make sure the URL is public and correct."
                        )
                        return

                with st.spinner("Scanning cloned repository …"):
                    try:
                        results = repo_analyzer.scan_repository(tmp_dir)
                    except Exception as e:
                        st.error(f"❌ Scan error: {e}")
                        return

                _display_scan_results(results, clone_url)

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        # ── Branch B: Local path ──────────────────────────────────────────────
        else:

            resolved = os.path.abspath(val)

            if not os.path.exists(resolved):
                st.error(
                    f"❌ Path does not exist: `{resolved}`\n\n"
                    "If you meant to scan a GitHub repo, paste the full `https://github.com/…` URL."
                )
                return

            if not os.path.isdir(resolved):
                st.error(f"❌ Not a directory: `{resolved}`")
                return

            with st.spinner(f"Scanning `{resolved}` …"):
                try:
                    results = repo_analyzer.scan_repository(resolved)
                except ValueError as e:
                    st.error(f"❌ Scan error: {e}")
                    return
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
                    return

            _display_scan_results(results, resolved)
# =========================================
# MAIN
# =========================================

def main() -> None:

    st.set_page_config(
        page_title="Project EcoCode AI",
        page_icon="🌿",
        layout="wide",
    )

    inject_theme_css()

    init_session_state()

    # =========================================
    # HERO SECTION
    # =========================================

    st.markdown("# Project EcoCode AI")

    st.markdown(
        "### AI-Powered Sustainable Software Engineering Platform"
    )

    st.markdown(
        "Analyze inefficient code, estimate carbon emissions, "
        "optimize runtime performance, and reduce digital waste "
        "using intelligent AI sustainability engineering."
    )

    st.divider()

    # =========================================
    # FEATURE CARDS
    # =========================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(label="⚡ AI Optimization", value="Gemini AI")
        st.caption("Generate greener optimized code using Gemini AI.")

    with c2:
        st.metric(label="🌍 Carbon Tracking", value="CodeCarbon")
        st.caption("Measure software emissions and sustainability.")

    with c3:
        st.metric(label="📊 Benchmarking", value="Runtime & Memory")
        st.caption("Compare runtime, memory, and energy usage.")

    with c4:
        st.metric(label="🏆 Leaderboard", value="Rankings")
        st.caption("Gamified green software engineering rankings.")

    st.divider()

    tw, tg, ts, tm, tl, tbl, trp = st.tabs(
        [
            "Workspace",
            "Gemini AI",
            "Simulator",
            "Metrics",
            "Learn",
            "Leaderboard",
            "Repo",
        ]
    )

    with tw:
        render_workspace()

    with tg:
        render_gemini_tab()

    with ts:
        render_simulator_tab()

    with tm:
        render_metrics_tab()

    with tl:
        render_learn_tab()

    with tbl:
        render_leaderboard_tab()

    with trp:
        render_repo_tab()


main()
=======
"""
Project EcoCode AI — sustainability analysis platform (Streamlit).

Measured runs use `energy_runner.py` + CodeCarbon in a subprocess.
Static analysis uses `ai_analysis` (AST, Radon, Pylint hooks).
Gemini AI integration added for sustainability optimization.
"""

from __future__ import annotations

import ast
import logging
import os
from typing import Any
from urllib.parse import urlparse

import ecocode_ai_analysis as ka
import ecocode_ai_leaderboard
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import pdf_generator
import refactor_engine
import repo_analyzer
import sandbox

# =========================================
# GEMINI AI
# =========================================

from gemini_analyzer import analyze_code, optimize_code


# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    filename="sustainability_dashboard.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

LOG_PATH = os.path.join(
    os.getcwd(),
    "sustainability_dashboard.log"
)


# =========================================
# SESSION STATE
# =========================================

def init_session_state() -> None:

    for k, v in {
        "user_code": "",
        "last_analysis_ok": False,
        "sandbox_results": None,
        "complexity_metrics": None,
        "suggestions": [],
        "green_score": 0,
        "measure_history": [],
        "last_repo_path": "",
        "ecocode_ai_stdin_line": "12",
    }.items():

        st.session_state.setdefault(k, v)

    if "editor_code" not in st.session_state:

        st.session_state.editor_code = (
            st.session_state.get("user_code", "")
        )

    st.session_state.setdefault("editor_desc", "")


# =========================================
# GIT VALIDATION
# =========================================

def _is_valid_git_url(url: str) -> bool:

    u = urlparse(url.strip())

    return bool(
        u.scheme in ("http", "https")
        and u.netloc
    )


# =========================================
# THEME
# =========================================

def inject_theme_css() -> None:

    st.markdown(
        """<style>
        h1, h2, h3 { color: #22c55e !important; font-weight: 800; }
        .stApp { background: radial-gradient(circle at top left, #1e293b 0%, #020617 45%, #000000 100%); color: white; }
        section[data-testid="stSidebar"] { background: rgba(2,6,23,0.95); border-right: 1px solid rgba(255,255,255,0.06); }
        div[data-testid="metric-container"] { background: rgba(17,24,39,0.8); border-radius: 22px; border: 1px solid rgba(255,255,255,0.06); padding: 24px; box-shadow: 0 6px 18px rgba(0,0,0,0.22); }
        .stButton > button { background: linear-gradient(90deg, #16a34a, #22c55e); color: white; border: none; border-radius: 16px; padding: 14px 18px; font-size: 16px; font-weight: 700; width: 100%; box-shadow: 0 6px 20px rgba(34,197,94,0.2); }
        .stButton > button:hover { transform: scale(1.03); box-shadow: 0 10px 28px rgba(34,197,94,0.32); }
        button[data-baseweb="tab"] { background: rgba(17,24,39,0.7); border-radius: 16px; margin-right: 10px; padding: 12px 20px; color: #cbd5e1; font-weight: 700; }
        button[data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(90deg, #16a34a, #22c55e); color: white; }
        .stTextArea textarea { background: rgba(17,24,39,0.75) !important; color: white !important; border-radius: 20px !important; border: 1px solid rgba(255,255,255,0.06) !important; }
        .streamlit-expanderHeader { background: rgba(17,24,39,0.75); border-radius: 16px; color: white !important; }
        </style>""",
        unsafe_allow_html=True,
    )


# =========================================
# FULL ANALYSIS
# =========================================

def analyze_code_full(code: str) -> None:

    with st.spinner(
        "Running sandbox + sustainability analysis..."
    ):

        sandbox_res = sandbox.run_code_sandbox(
            code,
            timeout=28,
            stdin_default=str(
                st.session_state.get(
                    "ecocode_ai_stdin_line",
                    "12"
                )
            ).strip()
            or "12",
        )

        st.session_state.sandbox_results = sandbox_res

        measured = sandbox_res.get("measured") or {}

        try:

            tree = ast.parse(code)

        except SyntaxError as e:

            st.session_state.last_analysis_ok = False

            st.error(
                f"⚠️ **Syntax error in your code** — line {e.lineno}: {e.msg}\n\n"
                "Please fix the error in the Editor and try again."
            )

            return

        stats = ka.compute_code_stats(tree, code)

        rad = ka.radon_average_complexity(code)

        use_measured = (
            measured
            if isinstance(measured, dict)
            and measured.get("ok")
            else None
        )

        st.session_state.green_score = (
            ka.compute_green_score(
                stats,
                rad,
                use_measured
            )
        )

        st.session_state.code_stats = stats

        st.session_state.difficulty = (
            ka.classify_difficulty(
                code,
                stats,
                rad
            )
        )

        st.session_state.complexity_metrics = (
            refactor_engine.analyze_complexity(code)
        )

        st.session_state.suggestions = (
            refactor_engine.get_ml_assisted_suggestions(code)
        )

        st.session_state.last_analysis_ok = True

        st.session_state.user_code = code

        st.success(
            "Analysis complete."
        )


# =========================================
# REFACTOR
# =========================================

def refactor_code(code: str) -> None:

    st.markdown(
        "#### Refactored output"
    )

    try:

        new_code, notes, changed = (
            ka.heuristic_refactor(code)
        )

    except SyntaxError as e:

        st.error(f"Invalid Python: {e}")

        return

    for n in notes:

        st.caption(n)

    # =========================================
    # COMPLEXITY ANALYSIS (refactor_engine)
    # =========================================

    complexity = refactor_engine.analyze_complexity(code)

    st.json(complexity)

    # =========================================
    # OPTIMIZED CODE (refactor_engine)
    # =========================================

    opt = refactor_engine.generate_optimized_code(code)

    # =========================================
    # ML SUGGESTIONS (refactor_engine)
    # =========================================

    suggestions = refactor_engine.get_ml_assisted_suggestions(code)

    for s in suggestions:

        st.info(
            f"[{s['level']}] {s['message']}"
        )

    if opt != code:

        st.code(
            opt,
            language="python"
        )

    else:

        st.code(
            code,
            language="python"
        )


# =========================================
# WORKSPACE
# =========================================

def render_workspace() -> None:

    st.markdown(
        "## 🧪 Workspace"
    )

    user_code = st.text_area(
        "Editor",
        height=300,
        placeholder="Paste Python code here..."
    )

    # ── Live syntax check while typing ───────────────────────────────────────
    if user_code.strip():
        try:
            ast.parse(user_code.strip())
            st.success("✅ Syntax OK")
        except SyntaxError as _syn:
            st.error(
                f"⚠️ **Syntax error in your code** — line {_syn.lineno}: {_syn.msg}\n\n"
                f"```\n{_syn.text or ''}\n{'~' * max(0, (_syn.offset or 1) - 1)}^\n```\n\n"
                "Fix the error above before running analysis."
            )

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "Analyze (measured + static)",
            type="primary",
            use_container_width=True
        ):

            if user_code.strip():

                analyze_code_full(
                    user_code.strip()
                )

            else:

                st.error(
                    "Add code first."
                )

    with b2:

        if st.button(
            "Refactor (safe transforms)",
            use_container_width=True
        ):

            if user_code.strip():

                refactor_code(
                    user_code.strip()
                )

            else:

                st.error(
                    "Nothing to refactor."
                )


# =========================================
# GEMINI TAB
# =========================================

def render_gemini_tab() -> None:

    st.markdown(
        "## ✨ Gemini AI Sustainability Engine"
    )

    st.caption(
        "Analyze inefficient code and generate greener optimized implementations using Gemini AI."
    )

    gemini_code = st.text_area(
        "Paste Python code for Gemini analysis",
        height=260,
        key="gemini_code_input"
    )

    c1, c2 = st.columns(2)

    # =========================================
    # ANALYSIS
    # =========================================

    with c1:

        if st.button(
            "🔍 Gemini Sustainability Analysis",
            use_container_width=True
        ):

            if gemini_code.strip() == "":

                st.warning(
                    "Please paste Python code."
                )

            else:

                with st.spinner(
                    "Gemini analyzing sustainability..."
                ):

                    analysis = analyze_code(
                        gemini_code
                    )

                st.success(
                    "Gemini analysis complete."
                )

                with st.expander(
                    "🧠 Gemini Sustainability Report",
                    expanded=True
                ):

                    st.markdown(
                        analysis
                    )

    # =========================================
    # OPTIMIZATION
    # =========================================

    with c2:

        if st.button(
            "⚡ Generate Green Optimized Code",
            use_container_width=True
        ):

            if gemini_code.strip() == "":

                st.warning(
                    "Please paste Python code."
                )

            else:

                with st.spinner(
                    "Generating optimized code..."
                ):

                    optimized = optimize_code(
                        gemini_code
                    )

                st.success(
                    "Optimization complete."
                )

                with st.expander(
                    "♻ Gemini Optimized Code",
                    expanded=True
                ):

                    st.markdown(
                        optimized
                    )


# =========================================
# METRICS TAB
# =========================================

def render_metrics_tab() -> None:

    if not st.session_state.get(
        "last_analysis_ok"
    ):

        st.info(
            "Run analysis first."
        )

        return

    sb = st.session_state.sandbox_results or {}

    st.markdown(
        f"## 🌿 Green Score: {st.session_state.get('green_score', 0)} / 100"
    )

    st.progress(
        int(
            st.session_state.get(
                "green_score",
                0
            )
        ) / 100.0
    )

    # =========================================
    # GREEN SCORE GAUGE (Feature 4)
    # =========================================

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=st.session_state.get(
                "green_score",
                0
            ),
            title={"text": "Green Sustainability Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#22c55e"},
                "steps": [
                    {"range": [0, 40], "color": "#7f1d1d"},
                    {"range": [40, 70], "color": "#78350f"},
                    {"range": [70, 100], "color": "#14532d"},
                ],
            },
        )
    )

    fig.update_layout(
        template="plotly_dark",
        height=350,
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =========================================
    # SANDBOX METRICS
    # =========================================

    if sb.get("success"):

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Runtime",
            f"{sb.get('runtime', 0):.4f} s"
        )

        m2.metric(
            "Memory",
            f"{sb.get('memory_mb', 0):.2f} MB"
        )

        m3.metric(
            "CPU %",
            f"{sb.get('cpu_percent', 0):.1f}"
        )

        m4.metric(
            "CO₂",
            f"{float(sb.get('emissions') or 0):.8f} kg"
        )

    # =========================================
    # PDF REPORT (Feature 1)
    # =========================================

    st.markdown("---")

    if st.button(
        "📄 Generate Sustainability Report"
    ):

        metrics = {

            "Green Score": st.session_state.get(
                "green_score",
                0
            ),

            "Runtime": sb.get(
                "runtime",
                0
            ),

            "Memory MB": sb.get(
                "memory_mb",
                0
            ),

            "CPU Percent": sb.get(
                "cpu_percent",
                0
            ),

            "CO2 Emissions": sb.get(
                "emissions",
                0
            ),
        }

        pdf_bytes = (
            pdf_generator.generate_pdf_report(
                metrics,
                st.session_state.get(
                    "suggestions",
                    []
                )
            )
        )

        st.download_button(

            label="⬇ Download PDF Report",

            data=pdf_bytes,

            file_name="ecocode_ai_report.pdf",

            mime="application/pdf"
        )


# =========================================
# SIMULATOR
# =========================================

def render_simulator_tab() -> None:

    from plotly.subplots import make_subplots

    st.markdown("## ⚡ Before vs After Simulator")

    st.caption(
        "Paste a short Python snippet. The simulator runs it, auto-optimizes it, "
        "then runs the optimized version and compares runtime and CO₂ side-by-side.  \n"
        "⚠️ Keep snippets **fast** (< 5 s) — slow/infinite loops will be killed by the timeout."
    )

    code = st.text_area(
        "Code (before)",
        height=160,
        key="sim_code",
        placeholder="# Paste a short Python snippet here\nfor i in range(1000):\n    x = i * i",
    )

    if st.button("Run comparison", type="primary"):

        if not code.strip():
            st.warning("Paste some Python code first.")
            return

        # ── Syntax check before wasting time running ──────────────────────
        try:
            ast.parse(code)
        except SyntaxError as e:
            st.error(f"⚠️ Syntax error on line {e.lineno}: {e.msg} — fix it before running.")
            return

        TIMEOUT = 60  # seconds — tight so timeouts are obvious not silent

        # ── Helper: extract normalised metrics from sandbox result dict ──────
        def _extract(res: dict) -> tuple[float, float, float, bool]:
            """
            Returns (runtime_s, co2_ukg, memory_mb, timed_out).
            sandbox.py sets success=False and error="Timed out …" on timeout,
            and also sets runtime = float(timeout) as a sentinel — we detect
            EITHER signal so we never plot the meaningless ceiling value.
            """
            ok        = bool(res.get("success") or res.get("ok"))
            err_str   = str(res.get("error") or "").lower()
            timed_out = (not ok) and ("timed out" in err_str or "timeout" in err_str)

            rt    = max(0.0, float(res.get("runtime") or 0))
            em_kg = max(0.0, float(res.get("emissions") or 0))
            co2   = em_kg * 1_000_000          # convert kg → µkg for display
            mem   = max(0.0, float(res.get("memory_mb") or 0))

            return rt, co2, mem, timed_out

        # ── Run BEFORE ─────────────────────────────────────────────────────
        with st.spinner("⏳ Running original code…"):
            try:
                before = sandbox.run_code_sandbox(code, timeout=TIMEOUT)
            except Exception as exc:
                st.error(f"Sandbox error: {exc}")
                return

        runtime_before, co2_before, mem_before, before_timed_out = _extract(before)

        if before_timed_out:
            st.error(
                f"⏱ **Original code timed out** (>{TIMEOUT} s).  \n\n"
                f"Sandbox message: `{before.get('error', '')}`  \n\n"
                "The chart would show meaningless flat bars — paste a "
                "**shorter / faster snippet** and try again."
            )
            return

        if not before.get("success"):
            err = before.get("error") or "Unknown sandbox error"
            st.error(f"❌ Original code failed to run:\n```\n{err}\n```")
            return

        # ── Optimize ────────────────────────────────────────────────────────
        after_code = refactor_engine.generate_optimized_code(code)

        # ── Run AFTER ──────────────────────────────────────────────────────
        with st.spinner("⚡ Running optimized code…"):
            try:
                after = sandbox.run_code_sandbox(after_code, timeout=TIMEOUT)
            except Exception as exc:
                st.error(f"Sandbox error (after): {exc}")
                return

        runtime_after, co2_after, mem_after, after_timed_out = _extract(after)

        if after_timed_out:
            st.warning(
                f"⏱ Optimized code also timed out (>{TIMEOUT} s). "
                "Runtime capped at timeout; CO₂ shown as 0."
            )
            runtime_after = float(TIMEOUT)
            co2_after     = 0.0
            mem_after     = 0.0

        # ── Show optimized code ─────────────────────────────────────────────
        with st.expander("🔧 Optimized code (After)", expanded=False):
            st.code(after_code, language="python")

        # ── Compute improvement % ───────────────────────────────────────────
        def pct_change(before_val: float, after_val: float) -> str:
            if before_val == 0:
                return "N/A"
            pct = (before_val - after_val) / before_val * 100
            sign = "↓" if pct >= 0 else "↑"
            return f"{sign} {abs(pct):.1f}%"

        # ── Metric cards ────────────────────────────────────────────────────
        st.markdown("### 📊 Results")

        m1, m2, m3, m4, m5, m6 = st.columns(6)

        m1.metric("⏱ Runtime Before",  f"{runtime_before:.4f} s")
        m2.metric("⏱ Runtime After",   f"{runtime_after:.4f} s",
                  delta=f"{runtime_after - runtime_before:+.4f} s",
                  delta_color="inverse")
        m3.metric("🌍 CO₂ Before (µkg)", f"{co2_before:.6f}")
        m4.metric("🌍 CO₂ After (µkg)",  f"{co2_after:.6f}",
                  delta=f"{co2_after - co2_before:+.6f}",
                  delta_color="inverse")
        m5.metric("💾 Mem Before",  f"{mem_before:.2f} MB")
        m6.metric("💾 Mem After",   f"{mem_after:.2f} MB",
                  delta=f"{mem_after - mem_before:+.2f} MB",
                  delta_color="inverse")

        # ── Improvement summary banner ───────────────────────────────────────
        rt_pct  = pct_change(runtime_before, runtime_after)
        co2_pct = pct_change(co2_before, co2_after)
        st.info(
            f"**Runtime improvement:** {rt_pct}  |  "
            f"**CO₂ improvement:** {co2_pct}"
        )

        st.markdown("---")

        # ── Subplot chart ────────────────────────────────────────────────────
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("⏱ Runtime (seconds)", "🌍 CO₂ Emissions (µkg)")
        )

        fig.add_trace(go.Bar(
            name="Runtime Before", x=["Before"], y=[runtime_before],
            marker_color="#6366f1",
            text=[f"{runtime_before:.4f}s"], textposition="outside"
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            name="Runtime After", x=["After"], y=[runtime_after],
            marker_color="#22c55e",
            text=[f"{runtime_after:.4f}s"], textposition="outside"
        ), row=1, col=1)

        # CO₂ chart — only render if we have real data, else show a note
        if co2_before == 0 and co2_after == 0:
            fig.add_annotation(
                text="CO₂ data unavailable<br>(CodeCarbon returned 0)",
                xref="x2", yref="y2", x=0.5, y=0.5,
                showarrow=False, font=dict(color="#94a3b8", size=13),
                xanchor="center"
            )
            # Still add invisible bars so axes render cleanly
            fig.add_trace(go.Bar(
                name="CO₂ Before", x=["Before"], y=[0.001],
                marker_color="#f97316", opacity=0,
                text=["0.000000"], textposition="outside"
            ), row=1, col=2)
            fig.add_trace(go.Bar(
                name="CO₂ After", x=["After"], y=[0.001],
                marker_color="#22c55e", opacity=0,
                text=["0.000000"], textposition="outside"
            ), row=1, col=2)
        else:
            fig.add_trace(go.Bar(
                name="CO₂ Before", x=["Before"], y=[co2_before],
                marker_color="#f97316",
                text=[f"{co2_before:.6f}"], textposition="outside"
            ), row=1, col=2)
            fig.add_trace(go.Bar(
                name="CO₂ After", x=["After"], y=[co2_after],
                marker_color="#22c55e",
                text=[f"{co2_after:.6f}"], textposition="outside"
            ), row=1, col=2)

        fig.update_layout(
            title="⚡ Before vs After Sustainability Comparison",
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="white"),
            height=500,
            showlegend=True,
            legend_title="Comparison",
        )

        # Force y-axes to start at 0 — no negative values
        fig.update_yaxes(title_text="Seconds",         rangemode="tozero", row=1, col=1)
        fig.update_yaxes(title_text="Micrograms CO₂",  rangemode="tozero", row=1, col=2)

        st.plotly_chart(fig, use_container_width=True)


# =========================================
# LEARN TAB
# =========================================

def render_learn_tab() -> None:

    st.markdown(
        "## 📘 Learn Optimization"
    )

    st.info(
        "Learn how greener software reduces energy consumption and digital waste."
    )


# =========================================
# LEADERBOARD
# =========================================

def render_leaderboard_tab() -> None:

    st.markdown(
        "## 🏆 Green Leaderboard"
    )

    # =========================================
    # SUBMIT SCORE (Feature 5)
    # =========================================

    name = st.text_input(
        "Name"
    )

    if st.button(
        "Submit Green Score"
    ):

        ecocode_ai_leaderboard.add_entry(

            name=name,

            green_score=st.session_state.get(
                "green_score",
                0
            ),

            reduction_pct=20,

            note="Optimized with Project EcoCode AI"
        )

        st.success(
            "Leaderboard updated."
        )

    st.markdown("---")

    entries = (
        ecocode_ai_leaderboard.load_entries()
    )

    if entries:

        df = pd.DataFrame(entries)

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.caption(
            "No entries yet."
        )


# =========================================
# REPO TAB (Feature 3)
# =========================================

def _is_github_url(s: str) -> bool:
    """Return True if the string looks like a GitHub/Git URL."""
    s = s.strip()
    return (
        s.startswith("https://github.com")
        or s.startswith("http://github.com")
        or s.startswith("git@github.com")
        or s.endswith(".git")
    )


def _display_scan_results(results: dict, label: str) -> None:
    """Shared helper — renders metrics + report for a completed scan."""
    raw = results.get("raw", {})

    if results["python_files"] == 0 and results["total_size_mb"] == 0.0:
        st.warning(
            "⚠️ Scan completed but found **0 Python files** and 0 bytes.\n\n"
            f"Directory scanned: `{label}`\n"
            "Possible causes:\n"
            "- The folder is empty\n"
            "- All sub-folders are excluded (`.git`, `venv`, `__pycache__`)\n"
            "- No `.py` files exist in this tree\n\n"
            "Try pointing to the root of your Python project."
        )
        return

    st.success(f"✅ Repository scan complete — `{label}`")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🐍 Python Files",        results["python_files"])
    c2.metric("♊ Duplicate Blocks",     results["duplicate_code_blocks"])
    c3.metric("⚡ Potential Savings",    f"{results['potential_energy_savings_percent']}%")
    c4.metric("📦 Total Size",           f"{results['total_size_mb']} MB")
    c5.metric("🏋 Heavy Scripts",        results["heavy_scripts"])

    d1, d2 = st.columns(2)
    d1.metric("📋 Unused Dependencies (est.)", results["unused_dependencies"])
    d2.metric("📁 Large Files (>350 KB)",       results["large_file_count"])

    st.markdown("---")
    st.text_area("📄 Repository Report", results["report_text"], height=300)

    dup_examples = raw.get("duplicate_examples", [])
    if dup_examples:
        with st.expander(f"♊ Duplicate Block Locations ({len(dup_examples)} shown)"):
            for ex in dup_examples:
                st.caption(f"• {ex}")

    large_files = raw.get("large_files", [])
    if large_files:
        with st.expander(f"📁 Large Files ({len(large_files)} found)"):
            st.dataframe(pd.DataFrame(large_files), use_container_width=True)

    heavy = raw.get("heavy_python", [])
    if heavy:
        with st.expander(f"🏋 Heavy Python Scripts ({len(heavy)} found)"):
            for h in heavy:
                st.caption(f"• {h}")


def render_repo_tab() -> None:

    st.markdown("## 🔗 Repository Scan")

    st.caption(
        "Paste a **GitHub URL** to clone & scan, "
        "or enter an **absolute local path** to scan directly."
    )

    col_a, col_b = st.columns([3, 1])

    with col_a:
        repo_input = st.text_input(
            "GitHub URL or Local Path",
            placeholder="https://github.com/user/repo  OR  C:\\Users\\you\\myproject",
            label_visibility="collapsed",
        )

    with col_b:
        scan_clicked = st.button("🔍 Scan", type="primary", use_container_width=True)

    # ── Live feedback while user types ───────────────────────────────────────
    if repo_input.strip():
        val = repo_input.strip()
        if _is_github_url(val):
            st.info(f"🌐 Detected GitHub URL — will clone and scan: `{val}`")
        else:
            resolved = os.path.abspath(val)
            if not os.path.exists(resolved):
                st.error(
                    f"❌ Local path not found: `{resolved}`  \n"
                    "Tip: if you want to scan a GitHub repo, paste the full `https://github.com/...` URL instead."
                )
            elif not os.path.isdir(resolved):
                st.error(f"❌ That path is a file, not a folder: `{resolved}`")
            else:
                try:
                    n = len(os.listdir(resolved))
                    st.success(f"✅ Local path found — {n} items at top level.")
                except PermissionError:
                    st.error("❌ Permission denied reading that directory.")

    # ── Scan button logic ─────────────────────────────────────────────────────
    if scan_clicked:

        val = repo_input.strip()

        if not val:
            st.warning("Enter a GitHub URL or local path first.")
            return

        # ── Branch A: GitHub URL ──────────────────────────────────────────────
        if _is_github_url(val):

            import shutil
            import tempfile

            # Make sure it ends with .git for GitPython
            clone_url = val if val.endswith(".git") else val

            tmp_dir = tempfile.mkdtemp(prefix="ecocode_ai_clone_")

            try:
                with st.spinner(f"Cloning `{clone_url}` …"):
                    try:
                        Repo.clone_from(clone_url, tmp_dir)
                    except GitCommandError as e:
                        st.error(
                            f"❌ Git clone failed.\n\n"
                            f"Error: `{e}`\n\n"
                            "Make sure the URL is public and correct."
                        )
                        return

                with st.spinner("Scanning cloned repository …"):
                    try:
                        results = repo_analyzer.scan_repository(tmp_dir)
                    except Exception as e:
                        st.error(f"❌ Scan error: {e}")
                        return

                _display_scan_results(results, clone_url)

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        # ── Branch B: Local path ──────────────────────────────────────────────
        else:

            resolved = os.path.abspath(val)

            if not os.path.exists(resolved):
                st.error(
                    f"❌ Path does not exist: `{resolved}`\n\n"
                    "If you meant to scan a GitHub repo, paste the full `https://github.com/…` URL."
                )
                return

            if not os.path.isdir(resolved):
                st.error(f"❌ Not a directory: `{resolved}`")
                return

            with st.spinner(f"Scanning `{resolved}` …"):
                try:
                    results = repo_analyzer.scan_repository(resolved)
                except ValueError as e:
                    st.error(f"❌ Scan error: {e}")
                    return
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
                    return

            _display_scan_results(results, resolved)
# =========================================
# MAIN
# =========================================

def main() -> None:

    st.set_page_config(
        page_title="Project EcoCode AI",
        page_icon="🌿",
        layout="wide",
    )

    inject_theme_css()

    init_session_state()

    # =========================================
    # HERO SECTION
    # =========================================

    st.markdown("# Project EcoCode AI")

    st.markdown(
        "### AI-Powered Sustainable Software Engineering Platform"
    )

    st.markdown(
        "Analyze inefficient code, estimate carbon emissions, "
        "optimize runtime performance, and reduce digital waste "
        "using intelligent AI sustainability engineering."
    )

    st.divider()

    # =========================================
    # FEATURE CARDS
    # =========================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(label="⚡ AI Optimization", value="Gemini AI")
        st.caption("Generate greener optimized code using Gemini AI.")

    with c2:
        st.metric(label="🌍 Carbon Tracking", value="CodeCarbon")
        st.caption("Measure software emissions and sustainability.")

    with c3:
        st.metric(label="📊 Benchmarking", value="Runtime & Memory")
        st.caption("Compare runtime, memory, and energy usage.")

    with c4:
        st.metric(label="🏆 Leaderboard", value="Rankings")
        st.caption("Gamified green software engineering rankings.")

    st.divider()

    tw, tg, ts, tm, tl, tbl, trp = st.tabs(
        [
            "Workspace",
            "Gemini AI",
            "Simulator",
            "Metrics",
            "Learn",
            "Leaderboard",
            "Repo",
        ]
    )

    with tw:
        render_workspace()

    with tg:
        render_gemini_tab()

    with ts:
        render_simulator_tab()

    with tm:
        render_metrics_tab()

    with tl:
        render_learn_tab()

    with tbl:
        render_leaderboard_tab()

    with trp:
        render_repo_tab()


main()
>>>>>>> 3ca4c4ed1728de16735324a5cc1c660905f89060
