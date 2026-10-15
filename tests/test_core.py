"""
Test suite for EcoCode AI core modules (runs with both unittest and pytest).
"""

import ast
import os
import tempfile
import unittest
from unittest.mock import patch

import ecocode_ai_analysis as ka
import gemini_analyzer
import refactor_engine
from energy_runner import check_source_safety
import pdf_generator
import ecocode_ai_leaderboard


class TestEcoCodeCore(unittest.TestCase):

    def test_gemini_key_loads_from_streamlit_secrets(self):
        with patch("gemini_analyzer.os.getenv", return_value=None):
            with patch.object(
                gemini_analyzer.st,
                "secrets",
                {"GEMINI_API_KEY": "test-key"},
            ):
                self.assertEqual(gemini_analyzer._get_api_key(), "test-key")

    def test_gemini_key_is_optional_without_secrets(self):
        with patch("gemini_analyzer.os.getenv", return_value=None):
            with patch.object(gemini_analyzer.st, "secrets", {}):
                self.assertIsNone(gemini_analyzer._get_api_key())

    def test_safety_check_blocks_dangerous_code(self):
        unsafe_samples = [
            "import os; os.system('echo dangerous')",
            "import subprocess",
            "__import__('os').system('ls')",
            "import socket; s = socket.socket()",
            "import ctypes",
        ]
        for code in unsafe_samples:
            self.assertIsNotNone(
                check_source_safety(code),
                f"Expected block for: {code}",
            )

    def test_safety_check_allows_safe_code(self):
        safe_samples = [
            "def add(a, b):\n    return a + b\nprint(add(2, 3))",
            "total = sum(x * x for x in range(100))\nprint(total)",
        ]
        for code in safe_samples:
            self.assertIsNone(
                check_source_safety(code),
                f"Unexpected block for: {code}",
            )

    def test_heuristic_refactor_fibonacci(self):
        naive_fib = (
            "def fib(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    else:\n"
            "        return fib(n - 1) + fib(n - 2)\n"
        )
        refactored, notes, changed = ka.heuristic_refactor(naive_fib)
        self.assertTrue(changed)
        self.assertIn("Iterative Fibonacci", refactored)
        self.assertIn("O(n)", refactored)

    def test_compute_code_stats(self):
        code = (
            "def process(items: list[int]) -> int:\n"
            '    """Process list and return sum."""\n'
            "    res = 0\n"
            "    for x in items:\n"
            "        res += x\n"
            "    return res\n"
        )
        tree = ast.parse(code)
        stats = ka.compute_code_stats(tree, code)
        self.assertEqual(stats.functions, 1)
        self.assertEqual(stats.loops, 1)
        self.assertEqual(stats.docstring_coverage, 1.0)
        self.assertEqual(stats.typed_params_ratio, 1.0)

    def test_compute_green_score_range(self):
        code = "def f(x):\n    return x * 2\n"
        tree = ast.parse(code)
        stats = ka.compute_code_stats(tree, code)
        score = ka.compute_green_score(stats, radon_avg=2.0, measured=None)
        self.assertTrue(0 <= score <= 100)

    def test_analyze_complexity(self):
        code = (
            "for i in range(10):\n"
            "    for j in range(10):\n"
            "        print(i, j)\n"
        )
        cx = refactor_engine.analyze_complexity(code)
        self.assertIn("time_complexity_estimate", cx)
        self.assertIn("space_complexity_estimate", cx)
        cx_lower = cx["time_complexity_estimate"].lower()
        self.assertTrue("nested loops" in cx_lower or "o(n" in cx_lower)

    def test_pdf_generation(self):
        metrics = {
            "Green Score": 85,
            "Runtime": 0.05,
            "Memory MB": 14.2,
            "CPU Percent": 12.0,
            "CO2 Emissions": 0.00001,
        }
        suggestions = [
            {"level": "Info", "message": "Consider using list comprehensions."},
            "General cleanliness recommendation.",
        ]
        pdf_bytes = pdf_generator.generate_pdf_report(metrics, suggestions)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_leaderboard_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        old_path = ecocode_ai_leaderboard.PATH
        try:
            ecocode_ai_leaderboard.PATH = temp_path

            initial = ecocode_ai_leaderboard.load_entries()
            self.assertEqual(len(initial), 0)

            ecocode_ai_leaderboard.add_entry("Alice", 92, 45.0, "Optimized loops")
            entries = ecocode_ai_leaderboard.load_entries()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["name"], "Alice")
            self.assertEqual(entries[0]["green_score"], 92)
        finally:
            ecocode_ai_leaderboard.PATH = old_path
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
