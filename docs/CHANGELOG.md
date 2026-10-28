# Project Changelog & Revision History

All notable changes, refactors, architectural decisions, and documentation additions to the **ML-Driven Queue Waiting-Time Prediction and Management System** (`ML-Time-predict-system`) are documented in this file.

---

## 📅 Chronological Version History

```
dd3dae3 (2026-10-28) - feat: standardize columns, parse timestamps, and combine loaded CSV datasets
b9fce5a (2026-10-25) - docs: add project task execution matrix and phase-by-phase tracker
0fdf1c1 (2026-10-22) - docs: add docs directory with comprehensive audit, changelog, tasks, and plan
34d7210 (2026-10-22) - fix: resolve Mermaid diagram syntax errors across README, PLAN, and research docs
e59966b (2026-10-22) - docs: update README with comprehensive overview, architecture, and codebase links
94e7749 (2026-10-22) - feat: add project planning, task tracking, and queueing theory research documentation
a5ff7ff (2026-10-22) - feat: add print statements to inspect columns of the first three loaded dataframes
f12b122 (2026-10-16) - refactor: comment out dataframe column printing loop in main.py
1d9248f (2026-10-16) - refactor: disable Excel file loading and update column iteration for all dataframes
4202247 (2026-10-16) - feat: add script to load and parse CSV and Excel datasets from data directory
73e3c4e (2026-10-16) - feat: add wait times dataset and related queue data files
37245c8 (2026-10-14) - docs: add comprehensive research documents and Django ML integration guide
32cb338 (2026-10-14) - initial: repository initialization
```

---

## 🔍 Detailed Change Log by Release / Commit

### [Commit dd3dae3] — 2026-10-28: CSV Column Standardization, Full Timestamp Parsing & Unified Dataset Loading
- **Type:** Feature / Data Engineering & Hygiene
- **Author:** gomugomucode
- **Problem Statement:** 
  1. Datasets in `data/` used divergent schema names (`arrival` vs `arrival_time`, `start` vs `start_time`, `end` vs `finish_time`, `wait_min` vs `wait_time`).
  2. Timestamps were stored as raw unparsed strings across mixed formats (`%d-%m-%Y %H.%M` in `queue_data.csv`, ISO strings with microseconds in `wait_times.csv`).
  3. Concatenation logic in `main.py` was mistakenly placed inside the per-file loop, causing incomplete merging and missing datasets.
- **Modifications:**
  - `main.py`:
    - Standardized column mapping across `queue_data.csv`, `verified_queue_waiting_time_dataset.csv`, and `wait_times.csv`.
    - Added comprehensive datetime parsing across `arrival_time`, `start_time`, and `finish_time`.
    - Added dataset provenance column (`source_file`) and uniform `date` derivation (`arrival_time.dt.date`).
    - Moved `pd.concat(dfs_list, ignore_index=True)` after the loading loop to unify all 14,545 records.
    - Added structured diagnostics: total dataset shape, data types, missing value audit, and sample preview.

---

### [Commit b9fce5a] — 2026-10-25: Task Execution Matrix & Phase-by-Phase Tracker
- **Type:** Documentation Enhancement
- **Author:** gomugomucode
- **Modifications:**
  - `TASKS.md`: Added project execution tracker detailing priorities (`P0`, `P1`, `P2`), Sprint 1 immediate focus, and delivery checkboxes across all 8 phases.

---

### [Commit 0fdf1c1] — 2026-10-22: Docs Portal, Codebase Audit & Master Plan
- **Type:** Documentation Architecture
- **Author:** gomugomucode
- **Modifications:**
  - `docs/AUDIT.md`: Created comprehensive technical audit of datasets, theoretical queue compliance, and SLAs.
  - `docs/CHANGELOG.md`: Established chronological commit history and detailed release log.
  - `docs/PLAN.md`: Strategic implementation architecture and SLA definitions.
  - `docs/README.md`: Navigation index for central documentation repository.

---

### [Commit 34d7210] — 2026-10-22: Mermaid Diagram Syntax & Parser Fix
- **Type:** Bug Fix / Documentation Quality
- **Author:** gomugomucode
- **Problem Statement:** GitHub's rich markdown display failed with `Parse error on line 27: ... end Client Tier <-->|REST API| Expecting SEMI, NEWLINE, got NODE_STRING`.
- **Root Cause:**
  1. Subgraph identifiers contained spaces (`subgraph Client Tier [Presentation Tier - React.js]`).
  2. Attempting to connect a subgraph directly to a node (`Client Tier <-->|REST API| API`) is unsupported by standard Mermaid lexers.
- **Modifications:**
  - `README.md`: Updated subgraph identifier to `ClientTier["Presentation Tier (React.js)"]` and replaced subgraph-level links with clean node-to-node connections (`Kiosk`, `Teller`, `Admin` $\leftrightarrow$ `API` / `WS`).
  - `PLAN.md`: Synchronized architecture diagram with valid node IDs.
  - `research/07_component_specifications.md`: Updated `subgraph FrontendSubsystems["Frontend Subsystems"]`.
  - `WORK_BREAKDOWN_SCHEDULE.md`: Cleaned up markdown table spacing and block borders.

---

### [Commit e59966b] — 2026-10-22: Comprehensive README Master Overhaul
- **Type:** Documentation Enhancement
- **Author:** gomugomucode
- **Problem Statement:** The repository root `README.md` previously contained only a 54-byte raw title string encoded in UTF-16LE without architecture diagrams, quick links, or directory mapping.
- **Modifications:**
  - Rewrote `README.md` as clean UTF-8 markdown.
  - Added project overview, dual-engine prediction concept (System A ML + System B Fallback).
  - Added interactive Mermaid system topology diagram.
  - Added comprehensive repository file tree.
  - Added categorized **Quick Links & Documentation** section linking:
    - Planning & Management: `PLAN.md`, `TASKS.md`, `WORK_BREAKDOWN_SCHEDULE.md`
    - Research Specifications: Documents `00` through `09` in `research/`
    - Data Assets: Primary verified dataset (12,017 records), sample records, data dictionary
    - Scripts: `main.py`
  - Added **Where to Start** immediate actionable bash snippet.

---

### [Commit 94e7749] — 2026-10-22: Project Planning, Task Tracking & Queueing Research
- **Type:** Feature / Architectural Documentation
- **Author:** gomugomucode
- **Modifications:**
  - **`PLAN.md`:** Created master implementation plan outlining vision, SLAs ($\le 10$ ms latency, $\ge 15\%$ MAE improvement over AST), dataset profiling, 8-phase execution methodology, dual-engine fallback, and risk mitigations.
  - **`TASKS.md`:** Created actionable task checklist across Phases 1–8 with checkboxes (`[ ]` / `[x]`), priorities (`P0`, `P1`, `P2`), and sprint focus.
  - **`WORK_BREAKDOWN_SCHEDULE.md`:** Created formal hierarchical Work Breakdown Structure (WBS 1.0 to 8.0), work package dictionary with estimated hours, 12-week Gantt schedule, and balanced discipline allocation (25% Data, 25% ML, 25% Backend, 25% Frontend).
  - **`research/00_queuing_theory_fundamentals_and_numerical_walkthrough.md`:** Added mathematical foundations of Little's Law ($L = \lambda W$), step-by-step numerical walkthrough of $M/M/1$ queue ($\lambda = 8, \mu = 10, \rho = 0.8, W = 30\text{ min}$), $M/M/1$ vs. $M/M/c$ pooling analysis, Erlang C delay formulas, and total operational cost optimization ($\text{Cost} = C_s \cdot c + C_w \cdot L_q$).
  - **`research/09_project_kickoff_and_technology_selection.md`:** Added strategic guidance resolving where to start (Data/ML first, backend second, frontend last), evaluating Python Django vs. Node.js (in-memory $\le 10$ ms latency), and the immediate 4-step action plan.
  - **`research/README.md`:** Updated index to reference new research documents.

---

### [Commit a5ff7ff] — 2026-10-22: Dataframe Column Inspection Statements
- **Type:** Feature / Scratch Script Enhancement
- **Author:** gomugomucode
- **Modifications:**
  - Added explicit `print(dfs_list[0].columns)`, `print(dfs_list[1].columns)`, and `print(dfs_list[2].columns)` in `main.py` to directly output column headers for loaded CSV files upon script execution.

---

### [Commit f12b122] — 2026-10-16: Column Printing Loop Commented
- **Type:** Refactor
- **Author:** gomugomucode
- **Modifications:**
  - Commented out the terminal loop in `main.py` that printed columns across all dataframes to reduce console verbosity.

---

### [Commit 1d9248f] — 2026-10-16: Excel Loading Disabled
- **Type:** Refactor / Dependency Mitigation
- **Author:** gomugomucode
- **Modifications:**
  - Commented out `.xlsx` loading via `pd.read_excel()` in `main.py` to avoid triggering missing optional dependency errors (`openpyxl`) when running in lightweight virtual environments.

---

### [Commit 4202247] — 2026-10-16: Dataset Ingestion Script Creation
- **Type:** Feature
- **Author:** gomugomucode
- **Modifications:**
  - Created `main.py` to iterate through the `data/` directory and populate `dfs` (dictionary by filename) and `dfs_list` (list by index).

---

### [Commit 73e3c4e] — 2026-10-16: Core Data Assets Added
- **Type:** Feature / Data Asset Ingestion
- **Author:** gomugomucode
- **Modifications:**
  - Added `data/verified_queue_waiting_time_dataset.csv` (12,017 records, date range Oct 5 to Oct 22, 2026).
  - Added `data/queue_data.csv` (560 rows).
  - Added `data/wait_times.csv` (multi-day microsecond resolution logs).
  - Added `data/DataDictionary.xlsx` (field metadata).

---

### [Commit 37245c8] — 2026-10-14: Research Documentation Suite
- **Type:** Documentation / Research Architecture
- **Author:** gomugomucode
- **Modifications:**
  - Added original research documents in `research/`:
    - `01_features_and_target_variables.md`
    - `02_baseline_models_and_queueing_theory.md`
    - `03_data_collection_protocol_college_queue.md`
    - `04_database_design_and_entities.md`
    - `05_system_architecture_react_django_postgres.md`
    - `06_django_ml_integration_guide.md`
    - `07_component_specifications.md`
    - `08_implementation_roadmap_and_schedule.md`
    - `README.md`

---

### [Commit 32cb338] — 2026-10-14: Initial Repository Commit
- **Type:** Initialization
- **Author:** gomugomucode
- **Modifications:** Initial project repository setup with `README.md`.
