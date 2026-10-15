"""PDF sustainability report (ReportLab)."""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_pdf_report(metrics: dict[str, Any], suggestions: list[Any]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Project EcoCode AI — Sustainability Report")
    y -= 36
    c.setFont("Helvetica", 10)
    c.drawString(
        50,
        y,
        "Combines measured subprocess run (CodeCarbon) with static AST / Radon heuristics.",
    )
    y -= 28
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Execution metrics")
    y -= 20
    c.setFont("Helvetica", 10)
    for key, val in metrics.items():
        c.drawString(60, y, f"• {key}: {val}")
        y -= 16
        if y < 120:
            c.showPage()
            y = 750
    y -= 12
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Optimization suggestions (by tier)")
    y -= 20
    c.setFont("Helvetica", 9)
    for sug in suggestions:
        if isinstance(sug, dict):
            line = f"[{sug.get('level', 'Info')}] {sug.get('message', '')}"
        else:
            line = str(sug)
        for chunk in [line[i : i + 95] for i in range(0, len(line), 95)]:
            c.drawString(60, y, chunk)
            y -= 14
            if y < 80:
                c.showPage()
                y = 750
    c.showPage()
    c.save()
    out = buffer.getvalue()
    buffer.close()
    return out
