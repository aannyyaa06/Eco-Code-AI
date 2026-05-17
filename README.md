<div align="center">

<br />

# EcoCode AI

**Your code has a carbon footprint. We measure it. We fix it.**

<br />

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br />

</div>

---

## Overview

EcoCode AI is an **AI-powered sustainable software engineering platform** that makes the invisible cost of inefficient code visible, measurable, and fixable.

Developers paste Python code or link a GitHub repository. The platform runs it in a safe sandbox, measures its real carbon emissions, assigns a **Green Score out of 100**, and returns a fully optimized version — rewritten by Google Gemini AI — with a complete sustainability report.

Green code and good code are the same thing. EcoCode AI makes sustainable software engineering the default, not the exception.

---

## The Problem

Data centers consume an estimated **2–3% of global electricity**, a number that grows every year as the world writes more software. Yet developers have no tools to understand the environmental cost of their code. The damage is invisible — so it goes unfixed.

Every unnecessary nested loop, every brute-force algorithm, every inefficient memory allocation forces a server somewhere to work harder than it needs to. In most of the world, that server still runs on fossil fuels.

Inefficient code is not just a performance problem. It is an environmental one.

---

## What It Does

| Step | Action | Description |
|------|--------|-------------|
| 01 | **Measure** | Runs code in an isolated sandbox and captures real CO₂ emissions, CPU spikes, and memory footprint |
| 02 | **Score** | Combines runtime emissions with structural code analysis to produce a transparent Green Score / 100 |
| 03 | **Fix** | Rewrites code using rule-based refactoring and Google Gemini AI, with a full explanation of every change |

---

## Features

- **Green Score Dashboard** — A single, transparent sustainability score broken down by emissions, complexity, and code smell penalties
- **Sandboxed Carbon Measurement** — Live CO₂ tracking during actual code execution, fully isolated from the host environment
- **Before vs After Simulator** — Runs original and optimized code side by side and renders the exact seconds saved and grams of CO₂ reduced
- **GitHub Repository Scanner** — Paste any public repository URL and audit the entire codebase for energy impact
- **Two-Layer Refactoring** — Deterministic rule-based fixes followed by Google Gemini AI for advanced optimization
- **Global Leaderboard** — Competitive sustainability rankings across all platform users
- **PDF Report Export** — One-click export of scores, charts, and AI suggestions into a shareable professional document

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUT                           │
│              Python Code  ──or──  GitHub URL                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  SANDBOXED EXECUTION                        │
│                                                             │
│   sandbox.py  →  spawns isolated child process              │
│   energy_runner.py  →  hooks into measurement tools         │
│                                                             │
│   ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │ CodeCarbon  │  │ tracemalloc  │  │     psutil      │  │
│   │  CO₂ Track  │  │Memory Peaks  │  │  CPU Utilization│  │
│   └─────────────┘  └──────────────┘  └─────────────────┘  │
│                         │                                   │
│              JSON payload → stdout → sandbox.py             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   STATIC ANALYSIS                           │
│                                                             │
│   klean_analysis.py  →  reads code without executing        │
│                                                             │
│   ┌──────────────┐  ┌──────────┐  ┌────────────────────┐  │
│   │  Python AST  │  │  Radon   │  │      Pylint        │  │
│   │ O(n²) loops  │  │Complexity│  │  Code Quality      │  │
│   │ code smells  │  │ Scoring  │  │  Analysis          │  │
│   └──────────────┘  └──────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GREEN SCORE                              │
│                                                             │
│   GreenScore = 100 − (w₁·Emission + w₂·Complexity +        │
│                        w₃·CodeSmell)                        │
│                                                             │
│   Every component transparent · Every weight explainable   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   REFACTORING ENGINE                        │
│                                                             │
│   Layer 1: refactor_engine.py                               │
│   → Deterministic rule-based transformations                │
│   → Safe, guaranteed improvements                           │
│                                                             │
│   Layer 2: gemini_analyzer.py                               │
│   → Google Gemini AI advanced optimization                  │
│   → Human-readable explanation of every change              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SIMULATOR  ·  LEADERBOARD  ·  PDF              │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.9+ | Core platform |
| Frontend | Streamlit | Dashboard and UI |
| AI Optimization | Google Gemini API | Advanced code refactoring |
| Carbon Tracking | CodeCarbon | CO₂ emission measurement |
| Resource Monitoring | psutil, tracemalloc | CPU and memory profiling |
| Code Analysis | Python AST, Radon, Pylint | Structural code inspection |
| ML Foundation | CodeBERT | Inefficiency pattern recognition |
| Visualization | Plotly, Pandas | Charts and data handling |
| Containerization | Docker, Docker Compose | Deployment and portability |

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Google Gemini API key — [Get one here](https://aistudio.google.com/app/apikey)

### Option 1 — Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ecocode-ai.git
cd ecocode-ai

# Configure environment
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# Build and run
docker-compose up --build
```

Open `http://localhost:8501` in your browser.

### Option 2 — Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ecocode-ai.git
cd ecocode-ai

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# Run the application
streamlit run app.py
```

---

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Additional settings are available in `config.yaml`.

---

## Project Structure

```
ecocode-ai/
│
├── app.py                    # Main Streamlit dashboard entry point
├── dashboard.py              # Alternative dashboard layout
│
├── sandbox.py                # Sandboxed execution manager
├── energy_runner.py          # Carbon and resource measurement worker
│
├── klean_analysis.py         # Static analysis engine (AST + Radon + Pylint)
├── refactor_engine.py        # Rule-based code refactoring
├── gemini_analyzer.py        # Google Gemini AI integration
│
├── repo_analyzer.py          # GitHub repository scanner
├── klean_leaderboard.py      # Global leaderboard system
├── pdf_generator.py          # PDF report generator
├── klean_pdf_report.py       # PDF report helper
│
├── trainer.py                # CodeBERT model training
├── local_train.py            # Local training script
├── benchmark_a.py            # Performance benchmarking
├── analyze_emissions.py      # Emissions data processing
├── CUDA_opt.py               # GPU/CUDA optimization (experimental)
├── parallel_optimization.py  # Multi-threading optimization (experimental)
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container configuration
├── docker-compose.yml        # Multi-container orchestration
├── config.yaml               # Application configuration
├── config_parser.py          # Configuration parser
├── logging_config.py         # Logging setup
└── .env                      # Environment variables (not committed)
```

---

## The Green Score

The Green Score is a single number out of 100 that reflects the overall sustainability of a piece of code. It is calculated from three normalized penalty signals:

```
GreenScore = 100 − (w₁ · EmissionPenalty + w₂ · ComplexityPenalty + w₃ · SmellPenalty)
```

**EmissionPenalty** — Derived from real CO₂ measured during sandboxed execution via CodeCarbon

**ComplexityPenalty** — Derived from cyclomatic complexity calculated by Radon. High complexity indicates code paths that waste computation

**SmellPenalty** — Derived from AST-detected anti-patterns including nested loops, unnecessary recursion, blocking calls inside loops, and missing type annotations

Every component is transparent and explainable. Developers always understand exactly why their score is what it is.

---

## Engineering Challenges

**Sandboxing untrusted code at scale**
Running arbitrary user code safely required building a two-layer isolation system. `sandbox.py` spawns a child process with a hard timeout. `energy_runner.py` writes measurement results to stdout as its final action, ensuring data is never lost when the timeout fires mid-execution.

**Carbon measurement at millisecond timescales**
CodeCarbon is designed for long model training runs, not short scripts. At small timescales, emission readings approach zero regardless of actual code quality. The solution was to combine runtime emissions with static analysis penalties, keeping the Green Score meaningful even when runtime measurements alone cannot distinguish between good and bad code.

**Trustworthy AI refactoring**
Generating refactored code with Gemini AI is straightforward. Ensuring developers trust and understand those changes is not. The platform always shows the refactored version alongside the original, never replacing it silently. Every change Gemini makes is accompanied by a plain-language explanation.

**Depth without complexity**
EcoCode AI touches sandboxing, AST parsing, carbon tracking, machine learning, and AI integration simultaneously. Keeping the dashboard comprehensible in under thirty seconds — while the engineering underneath is genuinely complex — required multiple UI iterations and significant scope discipline.

---

## Results

Across all test cases evaluated during development:

- Average CO₂ reduction of **75%** between original and optimized code
- Average runtime improvement of **4x** after optimization
- Green Score improvements of **30–60 points** on code with common inefficiency patterns

---

## Roadmap

- [ ] Multi-language support — JavaScript, Java, C++
- [ ] ML-trained Green Score weights replacing heuristic values
- [ ] CI/CD pipeline integration for automatic carbon audits on pull requests
- [ ] Team and organization dashboards for collective carbon tracking
- [ ] IDE extension for real-time Green Score feedback inside the editor
- [ ] Browser extension for lightweight code auditing without leaving the browser

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

```bash
# Fork the repository
# Create your feature branch
git checkout -b feature/your-feature-name

# Commit your changes
git commit -m "Add your feature"

# Push to the branch
git push origin feature/your-feature-name

# Open a pull request
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [CodeCarbon](https://codecarbon.io) — Carbon tracking infrastructure
- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI-powered code optimization
- [Streamlit](https://streamlit.io) — Dashboard framework
- [Radon](https://radon.readthedocs.io) — Cyclomatic complexity analysis
- [Pylint](https://pylint.org) — Code quality analysis

---

<div align="center">

**EcoCode AI** — Built for developers who believe green code and good code are the same thing.

</div>
