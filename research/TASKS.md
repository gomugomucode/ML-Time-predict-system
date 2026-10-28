# Project Task Execution Matrix

> **Current Sprint:** Sprint 1 — Data Cleaning, Baseline Benchmarks & Model Prototyping  
> **Status Legend:** `[x]` Completed | `[/]` In Progress | `[ ]` Backlog / Pending  
> **Priority Legend:** `P0` Critical Blocker | `P1` Core Deliverable | `P2` Polish & Enhancement

---

## 🎯 Sprint 1 Focus: Data, Baselines & Prototype ML (Current Phase)

| Task ID | Task Description | Priority | Status | Owner | Output / Deliverable |
|---|---|---|---|---|---|
| **T-1.1** | Load and inspect `verified_queue_waiting_time_dataset.csv` | `P0` | `[x]` | Data Eng | `main.py` verified; columns inspected. |
| **T-1.2** | Parse `arrival_time`, `start_time`, `finish_time` as ISO datetimes | `P0` | `[x]` | Data Eng | Timestamp conversion across all datasets in `main.py`. |
| **T-1.3** | Verify wait time consistency: $(t_S - t_A)$ vs. recorded `wait_time` | `P0` | `[x]` | Data Eng | Max difference $\le 0.02$ min verified in audit. |
| **T-1.4** | Extract arrival-time features (`queue_length`, `hour`, `dayofweek`, `is_weekend`) | `P0` | `[x]` | ML Eng | Feature matrix X and target y extracted in `main.py`. |
| **T-1.5** | Compute Non-ML Baselines (Historical Mean MAE & AST formula MAE) | `P0` | `[x]` | ML Eng | Historical Mean baseline MAE computed (59.09 min) in `main.py`. |
| **T-1.6** | Partition data chronologically (80% train / 20% test, no shuffling) | `P0` | `[x]` | ML Eng | 80/20 train/test partition executed in `main.py`. |
| **T-1.7** | Train prototype `RandomForestRegressor` and evaluate MAE vs. baseline | `P0` | `[x]` | ML Eng | RF MAE 9.68 min, 83.62% improvement over baseline verified. |
| **T-1.8** | Export trained pipeline to `artifacts/wait_time_model.joblib` | `P0` | `[ ]` | ML Eng | Model artifact ($\le 10$ ms latency). |

---

## 📋 Comprehensive Phase-by-Phase Task Tracker

### Phase 1: Problem Formulation, Target Definition & SLAs
- [x] **Task 1.1 [P0]:** Define target variable $W_q = t_S - t_A$ in decimal minutes. *(Completed in research)*
- [x] **Task 1.2 [P0]:** Establish latency SLA: $\le 10$ ms inference per ticket request. *(Completed in research)*
- [x] **Task 1.3 [P1]:** Define accuracy gate: ML model must outperform baseline AST MAE by $\ge 15\%$. *(Completed in research)*
- [x] **Task 1.4 [P1]:** Synthesize Little's Law ($L = \lambda W$) and $M/M/1$ vs $M/M/c$ pooling models. *(Completed in research)*

### Phase 2: Data Acquisition, Hygiene & Exploration
- [x] **Task 2.1 [P0]:** Acquire and stage queue dataset in `data/` directory. *(Completed: 12,017 records)*
- [x] **Task 2.2 [P0]:** Script initial dataset loading in `main.py`. *(Completed)*
- [x] **Task 2.3 [P0]:** Implement datetime parsing and standardization in `main.py`. *(Completed across all 3 CSVs)*
- [ ] **Task 2.4 [P1]:** Filter extreme anomalies using Interquartile Range (IQR) on service durations.
- [ ] **Task 2.5 [P2]:** Generate exploratory data analysis (EDA) plots (histograms, scatter, arrival rate).

### Phase 3: Feature Engineering & Preprocessing Pipeline
- [x] **Task 3.1 [P0]:** Extract arrival features available at $t_A$ (`queue_length`, `hour`, `dayofweek`, `is_weekend`) in `main.py`.
- [ ] **Task 3.2 [P1]:** Compute Delay-History (DH) metrics (Last-To-Enter-Service wait time).
- [ ] **Task 3.3 [P1]:** Apply target log-transformation $y = \ln(W_q + 1)$ for skewed wait times.
- [ ] **Task 3.4 [P0]:** Enforce chronological train-test split (80% train / 20% test).

### Phase 4: Baseline Benchmarking & Heuristic Engines
- [ ] **Task 4.1 [P0]:** Compute Naïve Historical Mean predictor on test split.
- [ ] **Task 4.2 [P0]:** Implement Last-to-Enter-Service (LES) and Average Service Time (AST) formulas.
- [ ] **Task 4.3 [P0]:** Calculate MAE, RMSE, MAPE to establish minimum performance floor.
- [ ] **Task 4.4 [P1]:** Package AST formula as standalone Python fallback function.

### Phase 5: Machine Learning Model Development & Optimization
- [ ] **Task 5.1 [P0]:** Construct Scikit-Learn `Pipeline` with preprocessing transformers.
- [ ] **Task 5.2 [P0]:** Train Linear Regression, Random Forest, and HistGradientBoosting / LightGBM.
- [ ] **Task 5.3 [P0]:** Verify candidate model beats baseline AST MAE by $\ge 15\%$.
- [ ] **Task 5.4 [P1]:** Perform hyperparameter tuning via `TimeSeriesSplit`.
- [ ] **Task 5.5 [P1]:** Calculate SHAP feature importance values to verify queue depth dominance.
- [ ] **Task 5.6 [P0]:** Serialize model to `wait_time_model.joblib` and benchmark single-prediction latency ($\le 10$ ms).

### Phase 6: Database Architecture & PostgreSQL Setup
- [ ] **Task 6.1 [P0]:** Deploy PostgreSQL 15+ database instance.
- [ ] **Task 6.2 [P0]:** Implement Django ORM models matching the research schema (`Ticket`, `Counter`, `Service`, `Snapshot`, `PredictionLog`).
- [ ] **Task 6.3 [P1]:** Create partial B-tree index on active waiting tickets (`status = 'waiting'`).
- [ ] **Task 6.4 [P1]:** Seed initial facility layout (Branches, Counters, Services, Staff accounts).

### Phase 7: Backend Serving, Django REST API & Dual-Engine Fallback
- [ ] **Task 7.1 [P0]:** Initialize Django REST Framework project (`queue_backend`).
- [ ] **Task 7.2 [P0]:** Implement in-memory singleton predictor (`ml_service.py`) preloaded at boot (`AppConfig.ready()`).
- [ ] **Task 7.3 [P0]:** Implement dual-engine routing: primary ML with automatic AST baseline fallback.
- [ ] **Task 7.4 [P0]:** Develop REST endpoints: `POST /api/tickets/`, `PATCH /api/tickets/{id}/status/`, `GET /api/counters/{id}/queue/`.
- [ ] **Task 7.5 [P1]:** Configure Django Channels ASGI + Redis for live `queue:updated` WebSocket broadcasts.

### Phase 8: Frontend Interfaces, Real-Time Delivery & MLOps
- [ ] **Task 8.1 [P0]:** Scaffold React.js application using Vite (`queue-frontend`).
- [ ] **Task 8.2 [P0]:** Build Student / Kiosk self-service check-in view with digital QR token.
- [ ] **Task 8.3 [P0]:** Build Teller Counter screen ("Call Next", "Serve", "Complete").
- [ ] **Task 8.4 [P1]:** Build Public Waiting Hall TV display showing current serving tokens.
- [ ] **Task 8.5 [P1]:** Build Operations & Model Accuracy dashboard (live MAE, server utilization).
- [ ] **Task 8.6 [P1]:** Connect WebSocket client to update UI in real-time on queue events.
- [ ] **Task 8.7 [P2]:** Set up Celery background workers for periodic snapshot rollups and nightly accuracy audit.
