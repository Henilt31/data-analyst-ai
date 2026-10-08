# DataMind

### Autonomous, self-correcting, RAG-augmented exploratory data analysis.

> Upload a dataset in CSV, JSON, Excel, or Parquet format. DataMind deterministically profiles it, formulates testable research hypotheses, writes and executes Python analysis code in an isolated sandbox, automatically heals execution tracebacks, extracts strictly grounded findings, renders visualizations, and compiles a comprehensive analytical report.

---

<p align="center">
  <img src="docs/assets/datamind-hero.svg" alt="DataMind Autonomous EDA Platform" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/Henilt31/data-analyst-ai/actions"><img src="https://img.shields.io/badge/backend%20tests-64%2F64%20passed-34d399?style=flat-square&logo=pytest&logoColor=white" alt="Pytest Tests" /></a>
  <a href="https://github.com/Henilt31/data-analyst-ai"><img src="https://img.shields.io/badge/frontend%20build-clean%20(Next.js%2016)-38bdf8?style=flat-square&logo=next.js&logoColor=white" alt="Next.js Build" /></a>
  <a href="https://github.com/Henilt31/data-analyst-ai"><img src="https://img.shields.io/badge/python-3.12%20%7C%203.14-blue?style=flat-square&logo=python&logoColor=white" alt="Python Versions" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://langchain-ai.github.io/langgraph/"><img src="https://img.shields.io/badge/LangGraph-0.2%2B-818cf8?style=flat-square" alt="LangGraph" /></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-Asyncpg-4169e1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" /></a>
  <a href="https://www.trychroma.com/"><img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-ff69b4?style=flat-square" alt="ChromaDB" /></a>
  <a href="https://docker.com"><img src="https://img.shields.io/badge/Sandbox-Docker%20%2F%20Subprocess-2496ed?style=flat-square&logo=docker&logoColor=white" alt="Docker Sandbox" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT" /></a>
</p>

---

## Table of Contents

- [What is DataMind?](#what-is-datamind)
- [Why This Exists](#why-this-exists)
- [Architecture at a Glance](#architecture-at-a-glance)
- [End-to-End Workflow](#end-to-end-workflow)
- [Analysis Pipeline (LangGraph)](#analysis-pipeline-langgraph)
- [Privacy-Preserving Structural RAG](#privacy-preserving-structural-rag)
- [Sandboxed Code Execution](#sandboxed-code-execution)
- [Grounded Insights & Zero Hallucinations](#grounded-insights--zero-hallucinations)
- [Visualizations & Report Synthesis](#visualizations--report-synthesis)
- [Persistence Architecture](#persistence-architecture)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Evaluation & Test Suite](#evaluation--test-suite)
- [Research & Telemetry Instrumentation](#research--telemetry-instrumentation)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Research Context & Lineage](#research-context--lineage)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is DataMind?

**DataMind** is a local-first, autonomous exploratory data analysis (EDA) platform engineered to transform raw datasets into complete, publication-ready analytical reports without manual script authoring or human-in-the-loop debugging.

Standard AI data assistants operate as shallow chatbots: users prompt an LLM, copy-paste code snippets into Jupyter notebooks, debug runtime exceptions manually, and hope the LLM has not hallucinated statistical values. DataMind re-engineers this workflow into an **autonomous agentic closed loop**:

1. **Ingest & Profile Deterministically:** Raw files are parsed locally with pandas and numpy into rigorous statistical profiles (schema, distributions, correlations, missingness, and data-quality signals).
2. **Formulate Hypotheses:** LLMs receive structured profile facts to generate testable, dataset-grounded research questions restricted to existing variables.
3. **Synthesize & Execute Python:** LangGraph compiles analysis scripts, validating AST syntax before launching them into an isolated, network-blocked execution sandbox.
4. **Self-Correct Runtime Tracebacks:** When code raises exceptions (`KeyError`, `TypeError`, `ValueError`, `ZeroDivisionError`), the execution traceback is fed back into a specialized repair agent to heal the script within bounded retry thresholds.
5. **Verify & Bind Evidence:** Numerical findings are parsed deterministically via standard `RESULT_JSON` tokens. The insight agent is constrained to synthesize observations strictly referencing executed results.
6. **Compile Visual Reports:** All verified findings, distribution plots, and executive takeaways are compiled into an analytical Markdown report.

---

## Why This Exists

Manual exploratory data analysis is cognitively demanding, highly repetitive, and fraught with common analytical traps:

- **Surface-Level Summarization:** Analysts often check `.describe()` or `.head()` and overlook subtle skewness, multimodal distributions, or collinear features.
- **The LLM Hallucination Trap:** Generative models queried directly on tabular questions frequently fabricate summary statistics, p-values, or correlation coefficients.
- **Brittle Iteration Cycles:** Writing custom matplotlib scripts, formatting timestamps, resolving dtype mismatches, and handling divide-by-zero errors consumes the majority of analysis time.

DataMind is built around **four non-negotiable engineering principles**:

### 1. Absolute Grounding
The LLM is **never allowed to calculate or invent numbers**. All calculations are performed deterministically in Python. Every narrative claim in the final report is linked to machine-verified execution evidence.

### 2. Autonomous Recovery
Code execution failure is treated as an expected, routine event. Instead of terminating the pipeline or burdening the user with tracebacks, errors trigger an automated reflection and correction cycle bounded by finite retry limits.

### 3. Hardened Local Isolation
Generated code is untrusted code. Analysis scripts execute in an isolated sandbox with **network sockets disabled**, **host environment secrets scrubbed**, memory quotas enforced, and hard execution timeouts applied.

### 4. Measurability & Telemetry
Every analysis trial logs structured metadata (`execution_time`, `retry_attempts`, `failure_type`, `token_usage`, `model_name`) to append-only JSONL files, enabling empirical evaluation of agent repair performance over time.

---

## Architecture at a Glance

DataMind follows a modular, decoupled architecture where the user interface, API gateway, execution sandbox, and orchestration graph remain strictly separated:

<p align="center">
  <img src="docs/assets/architecture.svg" alt="DataMind System Architecture" width="100%" />
</p>

- **Client Tier:** Next.js 16 App Router application providing dataset workspaces, interactive profile tables, real-time WebSocket progress bars, and rich report rendering.
- **Transport Tier:** FastAPI async REST gateway paired with an asynchronous WebSocket `JobBus` for live multi-subscriber state streaming.
- **Agent Orchestrator:** Stateful LangGraph execution graph managing transitions between code generation, sandbox execution, error triage, and insight synthesis.
- **Sandbox Boundary:** Dual-mode execution engine supporting Docker container isolation or a hardened local subprocess sandbox with OS-level restrictions.
- **Memory & Storage:** Relational persistence via PostgreSQL (with zero-config SQLite fallback), Chroma vector store for past dataset patterns, and structured filesystem outputs.

---

## End-to-End Workflow

Every analysis run traverses a 10-stage sequential pipeline from ingestion to synthesized report:

<p align="center">
  <img src="docs/assets/end-to-end-flow.svg" alt="End-to-End Data Flow" width="100%" />
</p>

*Caption: From dataset upload to grounded analytical report — the complete autonomous workflow.*

| Stage | Name | Description | Output Artifact |
| :---: | :--- | :--- | :--- |
| **01** | **Upload** | Validates file format (CSV, JSON, Excel, Parquet), verifies size bounds (&le;100MB), and writes to local storage. | Sanitized raw dataset file |
| **02** | **Profile** | Calculates deterministic summary statistics, histograms, null ratios, cardinality, and quality signals. | `DatasetProfile` JSON record |
| **03** | **Questions** | LLM evaluates the profile to generate 3–5 specific hypotheses with explicit rationale and required columns. | `ResearchQuestion` records |
| **04** | **RAG Recall** | Embeds structural schema representation to retrieve past analysis patterns from similar datasets. | Augmented question prompt context |
| **05** | **Code Gen** | Generates standalone Python script with AST syntax pre-check and required `RESULT_JSON` printing. | `code.py` executable script |
| **06** | **Sandbox** | Executes script inside network-isolated sandbox with memory limits and a 30-second hard cutoff. | Captured stdout, stderr, exit code |
| **07** | **Result Parser** | Deterministically parses `RESULT_JSON` from stdout and validates numeric data structures. | Machine-verified finding dictionary |
| **08** | **Insights** | Grounded LLM agent synthesizes takeaway, narrative context, and analytical caveats based on findings. | `Insight` schema with evidence lock |
| **09** | **Viz Builder** | Inspects output directory for generated chart artifacts (PNG), detects chart type, and maps filesystem paths. | `Visualization` database record |
| **10** | **Report** | Aggregates executive summary, data quality findings, and question answers into a Markdown report. | Comprehensive analytical report |

---

## Analysis Pipeline (LangGraph)

The core autonomous engine is implemented as a stateful, compiled **LangGraph** workflow. The graph coordinates code synthesis, isolated execution, conditional failure routing, iterative repair, and result publishing:

<p align="center">
  <img src="docs/assets/langgraph-pipeline.svg" alt="LangGraph Self-Correcting Execution Pipeline" width="100%" />
</p>

*Caption: Self-correction is bounded by the configured retry budget (default: 3 attempts).*

### Node Responsibilities & LLM Involvements

| Node Name | Handler Function | Responsibility | Uses LLM? |
| :--- | :--- | :--- | :---: |
| `code_generator` | `generate_code_node` | Synthesizes initial Python script using schema, profile stats, and hypothesis requirements. Runs AST syntax pre-check. | **Yes** |
| `sandbox_execute` | `sandbox_execute_node` | Executes script in Docker or isolated subprocess. Captures stdout/stderr, measures duration, logs trial telemetry. | **No** |
| `code_corrector` | `correct_code_node` | Reads runtime traceback, previous code, and schema; generates an updated script correcting the specific failure. | **Yes** |
| `result_analyzer` | `result_analyzer_node` | Parses stdout for `RESULT_JSON` token; validates data structure; extracts numerical metrics into state. | **No** |
| `insight_writer` | `insight_writer_node` | Translates verified numbers into a grounded analytical takeaway with explicit evidence and stated caveats. | **Yes** |
| `visualization_builder`| `visualization_builder_node` | Scans output directory for PNG charts, identifies plot type heuristic, attaches file path to run state. | **No** |
| `failed_end` | `failed_end_node` | Terminal node reached when retries are exhausted. Marks run as failed and preserves audit history. | **No** |

---

## Privacy-Preserving Structural RAG

DataMind includes a retrieval-augmented generation (RAG) system to recall successful analytical question patterns from previously explored datasets. 

<p align="center">
  <img src="docs/assets/rag-flow.svg" alt="Privacy-Preserving Structural RAG" width="100%" />
</p>

### Strict Data Privacy Distinctions

To ensure sensitive records are never leaked into vector databases:

1. **Raw Dataset Rows are NEVER Embedded:** The RAG index does not receive, process, or store raw dataset records.
2. **Synthetic Structural Representations Only:** DataMind transforms profiles into abstract structural signatures containing solely column names, inferred semantic types, missingness ratios, and general analytical domains (e.g., `features: [age, income], domain: financial, target: churn`).
3. **Local Deterministic Embeddings:** Uses local 384-dimensional sentence embeddings (`all-MiniLM-L6-v2` with deterministic local vector fallback), guaranteeing 100% offline functionality without external API calls.
4. **Local Chroma Storage:** Indexed vectors reside strictly on the local filesystem (`data/rag`).
5. **Strict Baseline Toggle:** RAG retrieval can be completely bypassed by setting `?rag_enabled=false` on question generation requests, establishing a clean baseline for evaluation.

---

## Sandboxed Code Execution

Executing arbitrary LLM-generated Python code introduces security and stability challenges. DataMind implements multi-layered isolation controls:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Untrusted LLM-Generated Python Code                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                       AST Pre-Execution Validation
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Hardened Sandbox Boundary                       │
│                                                                        │
│   [Network Blocked]      socket.socket.connect -> PermissionError     │
│   [Secrets Scrubbed]     Stripped of API keys, DB urls, tokens         │
│   [Execution Timeout]    Subprocess SIGKILL after 30 seconds           │
│   [Filesystem Quota]     Max 20 files, 50MB per file                   │
│   [Isolation Mode]       Docker Container OR Isolated Subprocess       │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │   Isolated Runtime: Python 3.12+ • Pandas • NumPy • Seaborn    │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │
                                     ▼
                     Captured stdout / RESULT_JSON / stderr
```

### Verified Sandbox Security Controls
- **Socket Network Blocking:** The execution preamble overrides `socket.socket.connect` to immediately raise `PermissionError`. Network calls (e.g., `requests`, `urllib`, raw sockets) are blocked.
- **Environment Variable Scrubbing:** The execution environment is scrubbed of all host secrets. Variables such as `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, database credentials, and user tokens are completely removed. Only `PATH`, `SYSTEMROOT`, and output directories are accessible.
- **Execution Timeouts:** Long-running operations or infinite loops are terminated after 30 seconds (`exit_code = 124`).
- **Filesystem Quotas:** Output directories are restricted to a maximum of 20 generated files and 50MB per file to prevent disk exhaustion.
- **Dual Sandbox Support:** Supports Docker container isolation with automatic, transparent fallback to the hardened local subprocess runner if Docker is not running.

---

## Grounded Insights & Zero Hallucinations

To guarantee that narrative findings reflect actual statistical reality, DataMind uses a strict **`RESULT_JSON` contract**:

```python
# The generated Python script executes deterministic calculations
import pandas as pd, json

df = pd.read_csv("data/input.csv")
tenure_low = df[df["tenure"] < 6]["churn"].mean()
tenure_high = df[df["tenure"] >= 6]["churn"].mean()
odds_ratio = round(tenure_low / (tenure_high + 1e-9), 2)

# Results are output via explicit RESULT_JSON token
results = {
    "tenure_low_churn_rate": round(tenure_low, 3),
    "tenure_high_churn_rate": round(tenure_high, 3),
    "odds_ratio": odds_ratio
}
print(f"RESULT_JSON: {json.dumps(results)}")
```

The `result_analyzer` node extracts the JSON payload from stdout. The `insight_writer` node then synthesizes the explanation, constrained by a Pydantic schema:

```json
{
  "text": "Customers with less than 6 months tenure exhibit a churn rate of 42.1%, compared to 12.4% for longer-tenured customers, representing an odds ratio of 3.4.",
  "evidence": {
    "tenure_low_churn_rate": 0.421,
    "tenure_high_churn_rate": 0.124,
    "odds_ratio": 3.4
  },
  "important_numbers": { "odds_ratio": 3.4 },
  "takeaway": "Early customer onboarding requires targeted retention interventions during the first 6 months.",
  "caveats": "Analysis is observational and does not establish causal attribution."
}
```

If code execution fails or stdout does not contain verified results, the system **never guesses** numbers. It either repairs the script or marks the finding as unverified.

---

## Visualizations & Report Synthesis

<p align="center">
  <img src="docs/assets/report-flow.svg" alt="Synthesis & Grounded Analytical Reporting" width="100%" />
</p>

### Supported Chart Typologies
DataMind scripts generate standard visualization artifacts via `matplotlib` and `seaborn`:
- **Histograms & KDE:** Feature distributions, skewness checks, and density profiles.
- **Scatter Plots:** Bivariate relationships, regression trends, and cluster visual inspections.
- **Bar Charts & Count Plots:** Categorical breakdowns and frequency distributions.
- **Box & Violin Plots:** Outlier detection and quartile comparisons across segments.
- **Correlation Heatmaps:** Feature covariance matrices.

### Analytical Report Assembly
When analysis runs complete, `POST /datasets/{id}/report` aggregates all artifacts into a standardized Markdown document:
1. **Executive Summary:** Dataset dimensions, format, and overarching analysis objectives.
2. **Dataset Overview & Data Quality:** Row/column counts, missingness rates, constant column detections, and suspected target variables.
3. **Research Questions:** Formulated hypotheses with analytical categories and business rationales.
4. **Detailed Findings per Question:** Grounded answer narrative, machine evidence numbers, stated caveats, and embedded visualization links.
5. **Key Takeaways:** Synthesized actionable business bullets.
6. **Analytical Limitations:** Explicit boundaries regarding sample size and external validity.

---

## Persistence Architecture

DataMind maintains a clean separation between relational state, filesystem artifacts, vector indices, and append-only telemetry:

```text
C:\Users\HP\data-analyst-ai\
├── data/
│   ├── datasets/         # Local uploaded raw data files (CSV, Parquet, JSON, Excel)
│   ├── outputs/          # Execution workspace artifacts (code.py, stdout.log, charts.png)
│   ├── rag/              # ChromaDB vector index files (384-d structural embeddings)
│   └── logs/
│       └── trials.jsonl  # Append-only execution trial telemetry records
```

### Relational Database Schema (SQLAlchemy + Asyncpg)

```text
users ─────────── (Authentication foundation)
  │
datasets ──────── 1:1 ── dataset_profiles (Schema, stats, nulls, quality)
  │      ──────── 1:1 ── reports (Compiled analytical markdown)
  │
  └────────────── 1:N ── research_questions
                            │
                            └──── 1:N ── analysis_runs
                                            │
                                            ├──── 1:N ── analysis_attempts (Code, exit_code, stderr)
                                            ├──── 1:1 ── insights (Grounded text, evidence, caveats)
                                            └──── 1:1 ── visualizations (Chart type, path, data)
```

*(Zero-Config Fallback: Automatically falls back to an asynchronous SQLite database `sqlite+aiosqlite:///:memory:` or local file when PostgreSQL is not configured).*

---

## Backend Architecture

The backend is built with **FastAPI**, **SQLAlchemy 2.0 (async)**, and **LangGraph**:

| Module Path | Primary Responsibility |
| :--- | :--- |
| `backend/app/main.py` | FastAPI application initialization, CORS configuration, router mounting, lifespan DB auto-init. |
| `backend/app/config.py` | Pydantic BaseSettings for environment variables, model choices, quotas, and file paths. |
| `backend/app/api/datasets.py` | Ingestion endpoint (`POST /datasets`), listing, dataset details, and on-demand profiling. |
| `backend/app/api/questions.py` | Hypothesis formulation endpoint with toggleable RAG context injection (`?rag_enabled`). |
| `backend/app/api/runs.py` | Analysis run trigger endpoint (`POST /runs`), attempt inspections, and WebSocket streaming. |
| `backend/app/api/reports.py` | Full analytical report compilation endpoint (`POST /datasets/{id}/report`) and viewer. |
| `backend/app/api/auth.py` | User registration and token authentication foundation (`POST /auth/register`, `/login`). |
| `backend/app/agents/graph.py` | LangGraph compiled state machine, conditional branching logic, and node wiring. |
| `backend/app/agents/code_generator.py` | Agent node generating Python analysis code with AST syntax validation. |
| `backend/app/agents/code_corrector.py` | Agent node repairing broken Python code using traceback diagnostics. |
| `backend/app/agents/result_analyzer.py` | Deterministic node extracting and validating `RESULT_JSON` execution metrics. |
| `backend/app/agents/insight_writer.py` | Agent node producing grounded qualitative takeaways from verified evidence. |
| `backend/app/agents/visualization_builder.py` | Node discovering generated PNG charts and cataloging visualization metadata. |
| `backend/app/services/sandbox.py` | Sandbox execution service (Docker & Subprocess) with network isolation and timeouts. |
| `backend/app/services/profiling.py` | Deterministic pandas/numpy profiler (schema, statistics, missingness, quality). |
| `backend/app/services/job_bus.py` | Multi-client WebSocket event bus with fine-grained pipeline state broadcasting. |
| `backend/app/services/telemetry.py` | Error taxonomy classification engine and JSONL trial logger (`trials.jsonl`). |
| `backend/app/services/llm.py` | Provider abstraction supporting OpenRouter, Google Gemini, and deterministic offline fallback. |
| `backend/app/rag/retriever.py` | Chroma similarity search engine matching dataset structural profiles. |
| `backend/app/rag/embeddings.py` | 384-dimensional sentence embedding service with offline fallback. |

---

## Frontend Architecture

The frontend is an interactive single-page application built on **Next.js 16 (App Router)**, **React 19**, and **Tailwind CSS**:

```text
frontend/src/
├── app/
│   ├── layout.tsx                # Root layout with dark technical theme
│   ├── page.tsx                  # Landing view and dataset upload entry point
│   ├── datasets/page.tsx         # Dataset listing and historical exploration dashboard
│   └── datasets/[id]/page.tsx    # Primary EDA Workspace (Profile, Questions, Runs, Report)
├── components/
│   ├── DatasetUpload.tsx         # Drag-and-drop file uploader with size/type validation
│   ├── DatasetProfileView.tsx    # Interactive schema tables, null distributions, quality flags
│   ├── QuestionsList.tsx         # Research hypothesis cards with RAG toggle controls
│   ├── RunProgress.tsx           # Real-time WebSocket execution monitor with step badges
│   ├── InsightCard.tsx           # Grounded finding viewer with verified numbers and charts
│   └── ReportViewer.tsx          # Rendered Markdown analytical report dashboard
└── lib/
    └── api.ts                    # Typed API client for FastAPI backend endpoints
```

---

## Evaluation & Test Suite

The codebase has undergone a full engineering audit and includes **64 granular, independent automated tests**:

```text
Backend Test Suite Results:
============================== 64 passed in 33.37s ==============================

Frontend Verification:
✓ Next.js 16 Optimized Production Build: Successful
✓ ESLint Verification: 0 errors, 0 warnings
```

### Verified Test Categories

| Test Module | Coverage Scope | Status |
| :--- | :--- | :---: |
| `tests/test_file_validation.py` | CSV, JSON, Excel, Parquet validation; executable rejection; file size limits. | **Passed** |
| `tests/test_profiling_schema.py` | Data type inference, semantic type classification, unicode character handling. | **Passed** |
| `tests/test_profiling_statistics.py` | Means, medians, IQR, standard deviations, distributions, datetime ranges. | **Passed** |
| `tests/test_profiling_quality.py` | Duplicate rows, constant columns, null flags, correlation matrices. | **Passed** |
| `tests/test_question_validation.py` | Pydantic schema validation, column-lock enforcement, batch schemas. | **Passed** |
| `tests/test_llm_service.py` | OpenRouter/Gemini abstractions, JSON repair, deterministic offline fallback. | **Passed** |
| `tests/test_rag_embeddings.py` | 384-dimensional vector output, mathematical determinism, offline capability. | **Passed** |
| `tests/test_rag_retrieval.py` | Synthetic structural representation (zero raw data leak), Chroma indexing, RAG toggle. | **Passed** |
| `tests/test_code_generation.py` | Python code generation structure, markdown fence stripping, AST validation. | **Passed** |
| `tests/test_sandbox_security.py` | Socket network blocking, host secret environment variable scrubbing. | **Passed** |
| `tests/test_sandbox_timeout.py` | Infinite loop termination via 30s hard timeout cutoff. | **Passed** |
| `tests/test_code_correction.py` | Traceback diagnostic parsing and self-correction repair node. | **Passed** |
| `tests/test_retry_logic.py` | Conditional routing decisions, finite retry bounds, terminal failure handling. | **Passed** |
| `tests/test_result_parser.py` | Deterministic `RESULT_JSON` extraction, malformed output resilience. | **Passed** |
| `tests/test_grounded_insights.py` | Quantitative evidence binding, caveat attachment, takeaway synthesis. | **Passed** |
| `tests/test_visualization.py` | Plot artifact detection, chart type heuristics, missing visual handling. | **Passed** |
| `tests/test_reports.py` | Markdown report compilation, section formatting, and structure verification. | **Passed** |
| `tests/test_database.py` | SQLAlchemy async models, cascading relationships, SQLite in-memory isolation. | **Passed** |
| `tests/test_api_datasets.py` | Dataset upload, listing, retrieval, and profile REST endpoints. | **Passed** |
| `tests/test_api_questions.py` | Question formulation and retrieval REST endpoints. | **Passed** |
| `tests/test_api_runs.py` | Run execution trigger, attempt inspection, and insight REST endpoints. | **Passed** |
| `tests/test_api_reports.py` | Report generation and retrieval REST endpoints. | **Passed** |
| `tests/test_websocket.py` | WebSocket subscription, multi-client broadcasting, and disconnection handling. | **Passed** |
| `tests/test_telemetry.py` | Failure taxonomy classification and JSONL trial logging persistence. | **Passed** |
| `tests/test_end_to_end.py` | Full autonomous EDA pipeline lifecycle from raw upload to compiled report. | **Passed** |

---

## Research & Telemetry Instrumentation

DataMind is instrumented to support empirical research into autonomous agent reliability and self-repair performance.

Every execution attempt appends a JSON record to `data/logs/trials.jsonl`:

```json
{
  "timestamp": 1775638210.45,
  "dataset_id": "8b52f9e4-c5a3-41bb-b567-c20e2ef5b47a",
  "question_id": "a98816c5-8422-4821-b1e7-d2e5b41cfbe2",
  "run_id": "02d44933-722a-4318-ae8b-592d3f9226cb",
  "attempt": 2,
  "status": "success",
  "failure_type": "none",
  "duration_ms": 420,
  "llm_model": "google/gemini-2.5-flash",
  "rag_enabled": false,
  "token_usage": { "prompt_tokens": 840, "completion_tokens": 195 }
}
```

### Failure Taxonomy Classification
The telemetry engine automatically classifies execution failures into structured categories:
- `timeout`: Subprocess exceeded time limit (exit code 124).
- `out-of-memory`: Process killed due to memory exhaustion (exit code 137).
- `KeyError`: Attempted access to non-existent dataset column.
- `TypeError`: Invalid type operation (e.g., adding string to float).
- `ValueError`: Mathematical or conversion failure.
- `malformed JSON`: Missing or unparseable `RESULT_JSON` token in stdout.
- `dtype mismatch`: Incompatible pandas series operations.
- `sandbox failure`: Container initialization or OS process error.
- `none`: Clean execution with exit code 0.

This instrumentation allows researchers to measure **First-Attempt Pass Rate (FAPR)** versus **Repaired Pass Rate (RPR)** across different foundation models.

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Health check endpoint | `200 OK` |
| `POST` | `/auth/register` | Register new user account | `201 Created` |
| `POST` | `/auth/login` | Authenticate user and receive token | `200 OK` |
| `POST` | `/datasets` | Upload and deterministically profile a dataset | `201 Created` |
| `GET` | `/datasets` | List all uploaded datasets | `200 OK` |
| `GET` | `/datasets/{id}` | Retrieve dataset metadata and status | `200 OK` |
| `GET` | `/datasets/{id}/profile` | Retrieve detailed statistical profile | `200 OK` |
| `POST` | `/datasets/{id}/questions` | Formulate research hypotheses (`?rag_enabled=false`) | `201 Created` |
| `GET` | `/datasets/{id}/questions` | List research questions for dataset | `200 OK` |
| `POST` | `/runs` | Trigger autonomous analysis run for a question | `202 Accepted` |
| `GET` | `/runs/{run_id}` | Inspect analysis run, attempts, insights, and charts | `200 OK` |
| `GET` | `/insights/{id}` | Retrieve individual grounded insight record | `200 OK` |
| `POST` | `/datasets/{id}/report` | Compile and synthesize analytical Markdown report | `201 Created` |
| `GET` | `/datasets/{id}/report` | Fetch compiled analytical report | `200 OK` |

### WebSocket Streaming

| Protocol | Endpoint | Description |
| :--- | :--- | :--- |
| `WS` | `/ws/datasets/{id}/status` | Real-time event stream broadcasting pipeline transitions (`code_generating`, `sandbox_executing`, `correction_started`, `analysis_success`, `failed`). |

---

## Configuration

All configuration is managed via environment variables (loaded through `backend/app/config.py`):

```bash
# Database Configuration (PostgreSQL with automatic SQLite in-memory/file fallback)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/datamind

# LLM Provider ("openrouter", "gemini", or offline fallback)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=
GOOGLE_API_KEY=

# Model Configuration
QUESTION_GENERATOR_MODEL=google/gemini-2.5-flash
CODE_GENERATOR_MODEL=google/gemini-2.5-flash
CODE_CORRECTOR_MODEL=google/gemini-2.5-flash
INSIGHT_WRITER_MODEL=google/gemini-2.5-flash

# Sandbox & Execution Bounds
USE_DOCKER_SANDBOX=false
SANDBOX_TIMEOUT_SECONDS=30
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0
MAX_ATTEMPTS=3

# Filesystem Storage Paths
DATASET_DIR=../data/datasets
OUTPUT_DIR=../data/outputs
RAG_PERSIST_DIR=../data/rag
LOGS_DIR=../data/logs
```

---

## Project Structure

```text
data-analyst-ai/
├── DATAMIND_AUDIT.md             # Complete engineering audit & verification report
├── README.md                     # Technical documentation & project guide
├── docker-compose.yml            # Container infrastructure for PostgreSQL & backend
│
├── backend/
│   ├── alembic.ini               # Database migration configuration
│   ├── pytest.ini                # Pytest configuration & asyncio options
│   ├── requirements.txt          # Python dependencies
│   ├── sandbox/
│   │   ├── Dockerfile            # Container sandbox specification
│   │   └── run_analysis.sh       # Script runner
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── config.py             # Settings & environment variables
│   │   ├── api/                  # REST & WebSocket routers
│   │   ├── agents/               # LangGraph nodes & compiled graph
│   │   ├── services/             # Sandbox, Profiler, Telemetry, Storage, JobBus
│   │   ├── rag/                  # Chroma store, local embeddings, retriever
│   │   ├── db/                   # SQLAlchemy models, sessions, repositories
│   │   └── schemas/              # Pydantic request/response schemas
│   └── tests/                    # 64 modular unit, integration, and E2E tests
│
├── frontend/
│   ├── package.json              # Next.js 16 dependencies
│   ├── tsconfig.json             # TypeScript configuration
│   ├── next.config.ts            # Next.js compiler settings
│   └── src/
│       ├── app/                  # App Router pages (Upload, Workspace, Listing)
│       ├── components/           # UI components (Profile, Questions, Runs, Reports)
│       ├── lib/                  # API client & WebSocket utilities
│       └── types/                # TypeScript interface definitions
│
├── data/                         # Local storage (Git-ignored)
│   ├── datasets/                 # Uploaded dataset files
│   ├── outputs/                  # Analysis execution artifacts
│   ├── rag/                      # ChromaDB vector persistent directory
│   └── logs/                     # Append-only trial telemetry (trials.jsonl)
│
└── docs/
    └── assets/                   # Architecture, workflow, and pipeline SVG diagrams
```

---

## Getting Started

### Prerequisites
- **Python:** 3.12 or newer (tested on Python 3.12 and 3.14)
- **Node.js:** 18 or newer (Node 20+ recommended)
- **Git:** Installed and configured
- **Docker:** *(Optional)* Required only if `USE_DOCKER_SANDBOX=true`

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Henilt31/data-analyst-ai.git
cd data-analyst-ai
```

---

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# (Optional: Add OPENROUTER_API_KEY or GOOGLE_API_KEY to .env)

# Run test suite to verify installation
pytest -v
```

All 64 tests should pass cleanly.

---

### Step 3: Start the Backend Server

```bash
# From the backend directory with virtual environment activated:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The FastAPI backend will start at `http://localhost:8000`.  
Interactive Swagger docs: `http://localhost:8000/docs`.

---

### Step 4: Frontend Setup

Open a second terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Verify lint and build
npm run lint
npm run build

# Start development server
npm run dev
```

The Next.js frontend will launch at `http://localhost:3000`.

---

## Research Context & Lineage

DataMind is inspired by research in **autonomous code-generation agents**, **self-correcting program synthesis**, and **grounded exploratory data analysis**:

- **Reflexion & Self-Correction:** Incorporating runtime tracebacks directly into iterative LLM prompts significantly improves completion rates over one-shot generation (*Shinn et al.*).
- **Grounded Quantitative Synthesis:** Decoupling numerical computation (delegated to deterministic interpreters) from semantic reasoning prevents hallucinated metrics (*Toolformer, Schick et al.*).
- **Architectural Lineage:** This platform reproduces and hardens the architecture pioneered by the open-source **DataMind** project, adding strict network sandbox isolation, secret scrubbing, and localized offline RAG.

---

## Roadmap

- [x] Multi-format ingestion (CSV, JSON, Excel, Parquet)
- [x] Deterministic statistical profiling and anomaly heuristics
- [x] LangGraph self-correcting execution state machine
- [x] Isolated execution sandbox (Docker & Subprocess) with network blocking
- [x] Standardized `RESULT_JSON` deterministic grounding protocol
- [x] Privacy-preserving structural RAG with local 384-d embeddings
- [x] Automated Markdown analytical report synthesis
- [x] WebSocket live execution progress streaming
- [x] JSONL execution telemetry and error taxonomy classification
- [ ] Exportable executive PDF and slide decks
- [ ] Multi-dataset comparative cross-analysis
- [ ] User authentication and multi-tenant workspace isolation

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
