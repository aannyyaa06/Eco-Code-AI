<div align="center">

# EcoCode AI

**Understand code efficiency. Explore ways to make it greener.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/AI-Google_Gemini-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

[Open the live app](https://ecocode-ai.onrender.com) · [Deployment guide](DEPLOYMENT.md)

</div>

EcoCode AI is a Streamlit web application for exploring Python code performance and sustainability. Paste a snippet to inspect its structure, run it for resource measurements, try automatic or Gemini-generated optimizations, and compare versions. You can also scan a public GitHub repository for basic structural signals.

## What the app does

The dashboard has seven tabs:

| Tab | What you can do |
| --- | --- |
| **Workspace** | Paste Python code, see a syntax check, run static and measured analysis, or apply safe rule-based refactoring. |
| **Gemini AI** | Ask Google Gemini for a sustainability-oriented code review or an optimized code suggestion. |
| **Simulator** | Run a snippet, apply the rule-based optimizer, then compare the original and transformed snippets' runtime, memory, and estimated CO₂. |
| **Metrics** | View the Green Score, runtime/resource measurements from the last analysis, and download a PDF summary. |
| **Learn** | Read short guidance on algorithmic efficiency, memory, dependencies, and carbon-aware practices. |
| **Leaderboard** | Submit a display name and score to a simple leaderboard. |
| **Repo** | Scan a public GitHub URL or a directory available to the running app. |

### Typical workflow

1. Open the [live app](https://ecocode-ai.onrender.com) or run it locally.
2. In **Workspace**, paste a short Python snippet and click **Analyze (measured + static)**.
3. Review the score and metrics in **Metrics**, and read the suggestions.
4. Try **Refactor (safe transforms)** or ask the **Gemini AI** tab for another suggestion.
5. Use **Simulator** to compare the original snippet with the rule-based transformed version.
6. Optionally export a PDF or scan a public repository in **Repo**.

## How analysis works

### Workspace analysis

The app first runs submitted Python through `sandbox.py` and `energy_runner.py` in a child process, with a timeout. The worker attempts to collect:

- **Elapsed runtime** using Python's performance timer.
- **Python allocation peak** using `tracemalloc`.
- **Process memory and CPU** using `psutil`.
- **Estimated CO₂ emissions** using CodeCarbon.

Static analysis parses the code with Python's AST and looks for metrics and patterns such as functions, classes, loops, branch count, loop nesting, long lines, bare `except`, `sleep()` in loops, type annotations, docstrings, and a specific naive recursive Fibonacci pattern. Radon is used for average cyclomatic complexity when available. The project also provides code-quality and optimization suggestions.

### Green Score

The Green Score is a project-specific heuristic from 0 to 100. It is **not** a standardized certification or a direct measurement of carbon emissions. The current implementation in `ecocode_ai_analysis.py`:

1. Starts from 38 points.
2. Adds up to 22 points for docstring coverage and 14 for typed function parameters.
3. Subtracts penalties for long lines, the detected naive Fibonacci pattern, bare exception handlers, `sleep()` inside loops, and high Radon complexity.
4. When a measured run succeeds, may add points based on the worker's CPU-efficiency heuristic and a short-duration bonus.
5. Clamps the result to the range 0–100.

The score should be read as a code-analysis indicator, not a promise that a particular change will reduce real-world emissions by the same percentage.

### Refactoring and Gemini

- **Rule-based refactoring** uses deterministic transformations and templates from `ecocode_ai_analysis.py` and `refactor_engine.py`. The Simulator uses this optimizer to produce its “after” version.
- **Gemini AI** sends the pasted code to Google's `gemini-2.5-flash` model for a review or optimization suggestion. AI-generated output is a suggestion: inspect and test it before using it.
- Gemini features require a `GEMINI_API_KEY`. The other app features do not require it.

### Simulator

The Simulator runs the original snippet and the rule-based optimized snippet separately, then displays their measured runtime, memory, and CodeCarbon output. These are individual short runs, not a controlled benchmark: machine load, warm-up, and very short runtimes can affect results. CodeCarbon may report zero or too little CO₂ to distinguish snippets. Treat the comparison as indicative, especially for tiny examples.

### Repository scanner

The Repo tab clones a public GitHub repository or scans a local directory visible to the server. The current scanner:

- Walks at most 400 files and excludes common generated/dependency folders such as `.git`, virtual environments, `node_modules`, and build/test caches.
- Counts Python files and total scanned file size.
- Lists files over 350 KB and Python files over 80 KB.
- Hashes normalized sliding five-line windows in Python files and reports matching windows as possible duplication.
- Reports the largest line count found in a requirements-style file (`requirements.txt`, `pyproject.toml`, or `Pipfile`).
- Displays an **estimated unused-dependency count** derived only from that line count.
- Produces a **heuristic potential-savings percentage** from fixed weights for file size, repeated windows, large Python files, and dependency-file length.

This scanner does **not** execute every file, determine whether dependencies are actually unused, or measure repository energy or carbon. Duplicate windows can overlap or be ordinary repeated boilerplate. Its savings percentage is a triage heuristic, not a measured forecast. Review the listed evidence yourself before changing a repository.

### PDF and leaderboard

The PDF report summarizes the current Green Score, the latest measured runtime, memory, CPU, CO₂ value, and suggestions. The leaderboard stores a small JSON list on the app filesystem; it has no accounts or database, so entries may not persist across redeploys or instance changes.

## Important security and measurement limitations

> **Do not treat the code runner as a security sandbox.**

The app starts submitted code in a child process, checks for a few suspicious source patterns, and applies a timeout. This is not strong isolation: it is not a substitute for a restricted container, OS-level sandbox, or separate execution service. Do not use the public deployment to run code from untrusted people or sensitive code unless a stronger isolation boundary has been added.

Resource and carbon readings depend on the host, workload, installed tools, and run duration. Short runs can be dominated by measurement overhead or produce zero readings. Static signals and the Green Score are heuristics; they do not prove environmental impact or code correctness.

The app does not provide user accounts or private workspaces. Do not paste secrets, credentials, or proprietary code into the hosted app. Code sent to Gemini is processed by Google's API under the applicable Google service terms.

## Run locally

### Requirements

- Python 3.9 or newer
- Git, if you want to scan GitHub repositories
- A Gemini API key only if you want to use Gemini features

### Windows PowerShell

```powershell
git clone https://github.com/aannyyaa06/Eco-Code-AI.git
Set-Location Eco-Code-AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root for Gemini features:

```env
GEMINI_API_KEY=your_new_key_here
```

Then start the dashboard:

```powershell
python -m streamlit run app.py
```

Open `http://localhost:8501`.

### macOS or Linux

```bash
git clone https://github.com/aannyyaa06/Eco-Code-AI.git
cd Eco-Code-AI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Optionally create `.env` with `GEMINI_API_KEY=your_new_key_here`, then run:

```bash
python -m streamlit run app.py
```

Never commit `.env` or publish an API key. If a key is exposed, revoke it and replace it.

## Deploy on Render

The live service is [ecocode-ai.onrender.com](https://ecocode-ai.onrender.com). This repository includes a Render Blueprint (`render.yaml`) and a Dockerfile configured to listen on Render's assigned port.

To create or update a Render deployment:

1. Push the repository to GitHub.
2. In Render, open **Blueprints** and choose **New Blueprint Instance**.
3. Select `aannyyaa06/Eco-Code-AI`, branch `main`, and Blueprint path `render.yaml`.
4. Set `GEMINI_API_KEY` to a valid, private API key in Render's environment settings. Rotate any key that has been exposed.
5. Deploy the Blueprint and open the service URL Render provides.

See [DEPLOYMENT.md](DEPLOYMENT.md) for more details. The app is a persistent Streamlit server; Vercel is not the host for this Streamlit deployment.

## Project structure

| File or folder | Purpose |
| --- | --- |
| `app.py` | Streamlit page, tabs, interaction flow, and presentation of analysis results. |
| `sandbox.py` | Starts the measurement worker, applies timeout handling, and parses its output. |
| `energy_runner.py` | Executes a snippet and gathers runtime/resource/CodeCarbon data. |
| `ecocode_ai_analysis.py` | AST-based code statistics, complexity hooks, Green Score, and rule-based analysis. |
| `refactor_engine.py` | Complexity helpers, suggestions, and rule-based optimized-code generation. |
| `gemini_analyzer.py` | Gemini API key loading and code review/optimization prompts. |
| `ecocode_ai_repo_scan.py` | Heuristic repository file and repeated-window scan. |
| `repo_analyzer.py` | Adapts scanner output for the Streamlit UI. |
| `pdf_generator.py` | Creates downloadable PDF reports. |
| `ecocode_ai_leaderboard.py` | JSON-file leaderboard operations. |
| `input/`, `output/` | Example challenge inputs and optimized examples. |
| `images/` | App screenshots and other project images. |
| `tests/` | Core module tests. |
| `render.yaml`, `Dockerfile` | Render Blueprint and container configuration. |

## Run tests

Install the dependencies, then run:

```bash
python -m unittest discover -s tests -v
```

## Technology

- Python and Streamlit
- Google Gemini API (`google-generativeai`)
- CodeCarbon, `psutil`, and `tracemalloc`
- Python AST, Radon, and Pylint
- Plotly and Pandas
- Docker and Render

## Contributing

Contributions are welcome. Open an issue to discuss a significant change, then submit a pull request with a clear description and tests where appropriate.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
