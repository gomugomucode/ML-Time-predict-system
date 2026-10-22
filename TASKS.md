# Project Task Tracker: ML Queue Waiting-Time Prediction System

This document tracks all actionable engineering tasks across the 8 phases of the project. Tasks are prioritized by urgency (`P0`: Critical blocker, `P1`: Core feature, `P2`: Enhancement) and marked with execution status (`[ ]` Pending, `[/]` In Progress, `[x]` Completed).

---

## 🚀 Immediate Next Steps (Sprint 1 Focus)

1. [ ] **Task 2.1:** Build a Python data inspection and cleaning script for `data/verified_queue_waiting_time_dataset.csv`.
2. [ ] **Task 3.1:** Extract arrival-time features (`queue_length`, `hour_of_day`, `day_of_week`, cyclical encodings) and compute $W_q$.
3. [ ] **Task 4.1:** Compute baseline evaluation metrics (Historical Mean, LES, AST formula, QL estimator) to establish the minimum performance floor.

---

## Phase 1: Problem Formulation, Target Definition & Operational SLAs

- [x] **Task 1.1 [P0]:** Define primary prediction target variable ($W_q = t_S - t_A$) in minutes and seconds. *(Completed in research)*
- [x] **Task 1.2 [P0]:** Establish inference latency Service Level Agreement ($\le 10$ ms per prediction). *(Completed in research)*
- [x] **Task 1.3 [P1]:** Formalize accuracy criteria: ML model MAE must outperform baseline AST formula by $\ge 15\%$. *(Completed in research)*
- [x] **Task 1.4 [P1]:** Synthesize Little's Law ($L = \lambda W$) and $M/M/1$ vs. $M/M/c$ queueing theory benchmarks into documentation. *(Completed in research)*

---

## Phase 2: Data Acquisition, Hygiene & Exploration

- [ ] **Task 2.1 [P0]:** Develop Python script (`src/data/inspect_data.py` or Jupyter notebook) to inspect `data/verified_queue_waiting_time_dataset.csv`.
  - Check missing values, nulls, and duplicate timestamps.
  - Verify timestamp data types and date ranges (October 5 – 22, 2026).
- [ ] **Task 2.2 [P0]:** Validate data consistency between recorded `wait_time` and computed difference $(t_S - t_A)$.
- [ ] **Task 2.3 [P1]:** Inspect secondary datasets (`data/queue_data.csv`, `data/wait_times.csv`) for potential multi-counter or cross-validation use.
- [ ] **Task 2.4 [P1]:** Apply anomaly filtering:
  - Drop invalid records where $t_S < t_A$ (negative wait times).
  - Apply Interquartile Range (IQR) filter to identify extreme outliers caused by system pauses or unrecorded lunch breaks.
- [ ] **Task 2.5 [P2]:** Generate exploratory data analysis (EDA) plots:
  - Histogram & KDE of waiting times (checking right-skewness).
  - Queue length vs. Waiting time scatter plot.
  - Hourly arrival density plot ($\lambda(t)$ across 9:00 AM – 5:00 PM).

---

## Phase 3: Feature Engineering & Preprocessing Pipeline

- [ ] **Task 3.1 [P0]:** Implement strict prediction-time feature extraction pipeline (strictly using data available at $t_A$):
  - `queue_length`: Headcount waiting ahead at arrival.
  - `hour_of_day`: Integer $9 \dots 17$.
  - `day_of_week`: Integer $0 \dots 6$.
  - `is_weekend`: Binary indicator.
  - `sin_hour`, `cos_hour`: Cyclical trigonometric transformations.
- [ ] **Task 3.2 [P0]:** Engineer delay-history (DH) metrics:
  - `last_to_enter_service_wait` (LES): The realized wait time of the most recent customer called to a counter prior to $t_A$.
  - `rolling_service_time_avg`: Rolling average service time over recent completions.
- [ ] **Task 3.3 [P1]:** Target transformation:
  - Apply natural log transformation $y = \ln(W_q + 1)$ to normalize right-skewed wait times.
  - Implement inverse transform $\exp(\widehat{y}) - 1$ for model evaluation and API response.
- [ ] **Task 3.4 [P0]:** Implement chronological train-test split:
  - Train set: First 80% of records chronologically (~9,600 rows).
  - Test set: Remaining 20% of records chronologically (~2,400 rows).
  - *No random shuffling to prevent temporal data leakage.*

---

## Phase 4: Baseline Benchmarking & Heuristic Development

- [ ] **Task 4.1 [P0]:** Implement non-ML baseline predictors on the test split:
  - **Naïve Historical Mean:** $\widehat{W} = \text{mean}(W_{q, \text{train}})$.
  - **Last-To-Enter-Service (LES):** $\widehat{W} = W_{q, \text{latest}}$.
  - **Average Service Time (AST) Formula:** $\widehat{W}_{\text{AST}} = \frac{L_q \times \overline{S}}{c}$.
  - **Queue-Length (QL) Estimator:** $\widehat{W}_{\text{QL}} = \frac{L_q + 1}{c \cdot \mu}$.
- [ ] **Task 4.2 [P0]:** Evaluate baseline performance metrics:
  - Mean Absolute Error (MAE) in minutes.
  - Root Mean Squared Error (RMSE) in minutes.
  - Mean Absolute Percentage Error (MAPE).
- [ ] **Task 4.3 [P1]:** Package the AST / QL formula as an independent fallback function to be embedded in the backend.

---

## Phase 5: Machine Learning Model Development & Validation

- [ ] **Task 5.1 [P0]:** Build an integrated Scikit-Learn `Pipeline` combining:
  - `ColumnTransformer` (scaling numerical features, one-hot/ordinal encoding categoricals).
  - Estimator: `RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)`.
- [ ] **Task 5.2 [P0]:** Train and compare candidate models:
  - `LinearRegression` / `Ridge` (linear baseline).
  - `RandomForestRegressor`.
  - `HistGradientBoostingRegressor` / `XGBoost`.
- [ ] **Task 5.3 [P0]:** Evaluate models on test set and benchmark against Phase 4 baselines:
  - Verify MAE improvement over AST baseline $\ge 15\%$.
- [ ] **Task 5.4 [P1]:** Hyperparameter tuning:
  - Optimize `n_estimators`, `max_depth`, `min_samples_split` using `TimeSeriesSplit` cross-validation.
- [ ] **Task 5.5 [P1]:** Interpretability analysis:
  - Compute SHAP values or feature importances to verify domain sanity (`queue_length` should dominate).
- [ ] **Task 5.6 [P0]:** Serialize the winning pipeline:
  - Export using `joblib.dump(pipeline, "artifacts/wait_time_model.joblib")`.
  - Verify standalone inference latency using Python `time.perf_counter()` ($\le 10$ ms target).

---

## Phase 6: Database Architecture & PostgreSQL Setup

- [ ] **Task 6.1 [P0]:** Initialize PostgreSQL 15+ database instance and configure connection credentials.
- [ ] **Task 6.2 [P0]:** Implement Django ORM models matching the research schema:
  - `Branch`, `Department`, `Service`, `Counter`, `StaffUser`.
  - `Ticket` (token number, arrival time, queue length ahead, priority).
  - `ServiceTransaction` (`waiting_start_time`, `serving_start_time`, `serving_end_time`, `status`).
  - `QueueStatusSnapshot` (minute/hourly snapshots of waiting count, active counters).
  - `RollingServiceMetrics` (cached LES and rolling AST).
  - `PredictionLog` (ticket reference, predicted wait, baseline wait, actual realized wait, error).
  - `ModelRegistry` (model metadata, version, MAE, active flag).
- [ ] **Task 6.3 [P1]:** Create specialized database indexes:
  - Composite partial index: `(service_id, transaction_status)` WHERE `transaction_status = 'waiting'`.
  - B-tree indexes on `waiting_start_time` and `created_at`.
- [ ] **Task 6.4 [P1]:** Seed initial facility data (e.g., College Account Section, 3 service counters: Tuition Fees, Clearance, General Inquiries).

---

## Phase 7: Backend Serving, API Orchestration & Dual-Engine Fallback

- [ ] **Task 7.1 [P0]:** Initialize Django REST Framework project structure:
  - Set up `queue_backend` Django project and `api` application.
  - Configure CORS, REST Framework settings, and JWT authentication.
- [ ] **Task 7.2 [P0]:** Implement in-memory ML model singleton service (`ml_service.py`):
  - Preload `.joblib` model at server startup inside `AppConfig.ready()`.
  - Wrap inference in thread-safe prediction method.
- [ ] **Task 7.3 [P0]:** Implement Dual-Engine Fallback mechanism:
  - Primary path: Execute in-memory ML pipeline (System A).
  - Fallback path: If ML encounters error/missing values, immediately execute AST formula (System B).
- [ ] **Task 7.4 [P0]:** Develop REST API endpoints:
  - `POST /api/tickets/`: Issue ticket, compute instantaneous features, predict wait time, log prediction, return token + EWT.
  - `PATCH /api/tickets/{id}/status/`: Update ticket state (`in_service`, `completed`, `reneged`) and log actual wait time.
  - `GET /api/counters/{id}/queue/`: Return active waiting line for teller counter.
  - `GET /api/analytics/dashboard/`: Return queue metrics ($L_q, W_q, \lambda, \mu, \rho$) and prediction accuracy audit.
- [ ] **Task 7.5 [P1]:** Configure Django Channels (ASGI) and Redis channel layer for real-time WebSocket events (`queue:updated`, `ticket:called`).

---

## Phase 8: Frontend Delivery, Real-Time Transport & MLOps

- [ ] **Task 8.1 [P0]:** Scaffold React.js application using Vite (`queue-frontend`).
- [ ] **Task 8.2 [P0]:** Build **Student / Public Kiosk View**:
  - Service selection form (Tuition, Exam Fee, Clearance).
  - "Draw Ticket" action generating digital token and QR code.
  - Estimated Waiting Time (EWT) display and current serving ticket indicator.
- [ ] **Task 8.3 [P0]:** Build **Teller Counter Interface**:
  - Active counter status toggle (Open, Paused, Closed).
  - "Call Next Ticket" button with audible ping / visual alert.
  - "Start Transaction" and "Complete Transaction" controls.
  - Real-time queue count display for assigned service.
- [ ] **Task 8.4 [P1]:** Build **Waiting Hall Display Screen**:
  - Fullscreen display showing currently called tokens per counter window.
  - Live estimated wait times for incoming arrivals.
- [ ] **Task 8.5 [P1]:** Build **Admin Operations & Accuracy Dashboard**:
  - Real-time performance meters: Queue length ($L_q$), Server utilization ($\rho$), Arrival rate ($\lambda$).
  - Prediction accuracy monitoring: Scatter plot of Predicted vs. Realized wait times and live MAE gauge.
- [ ] **Task 8.6 [P1]:** Connect WebSocket client to Django Channels to trigger instant UI re-renders upon state changes.
- [ ] **Task 8.7 [P2]:** Set up Celery background tasks:
  - Periodic queue snapshot aggregation (every 5 minutes).
  - Nightly model accuracy reporting and drift alerting.

---

## Tracking Legend
- `[ ]` Open / Backlog
- `[/]` In Progress
- `[x]` Completed
- `P0` High Priority / Blocker
- `P1` Medium Priority / Core
- `P2` Low Priority / Polish
