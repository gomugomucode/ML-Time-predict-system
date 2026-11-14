# Project Task Tracker: ML Queue Waiting-Time Prediction System

This document tracks all actionable engineering tasks across the 8 phases of the project. Tasks are prioritized by urgency (`P0`: Critical blocker, `P1`: Core feature, `P2`: Enhancement) and marked with execution status (`[ ]` Pending, `[/]` In Progress, `[x]` Completed).

---

## 🚀 Immediate Next Steps (Sprint 1 & 2 Focus)

1. [x] **Task 2.1:** Build a Python data inspection and cleaning script for `data/verified_queue_waiting_time_dataset.csv`. *(Completed in `main.py`)*
2. [x] **Task 2.3:** Inspect secondary datasets (`data/queue_data.csv`, `data/wait_times.csv`) and combine into unified pipeline. *(Completed in `main.py`)*
3. [x] **Task 3.1:** Extract arrival-time features (`queue_length`, `hour_of_day`, `day_of_week`, `is_weekend`) and define $X, y$. *(Completed in `main.py`)*
4. [x] **Task 4.1:** Compute baseline evaluation metrics (Historical Mean baseline: 59.09 min MAE). *(Completed in `main.py`)*
5. [x] **Task 5.2:** Train prototype `RandomForestRegressor` (Achieved 9.68 min MAE, 83.62% improvement over baseline). *(Completed in `main.py`)*
6. [x] **Task 5.6:** Serialize trained model to `wait_time_rf_model.joblib`. *(Completed in `main.py`)*
7. [x] **Task 4.3:** Package Average Service Time (AST) formula fallback engine for the backend. *(Completed in `api/ml_service.py`)*
8. [x] **Task 7.1:** Initialize Django REST Framework backend project (`queue_backend`) with DRF and CORS. *(Completed)*
9. [x] **Task 7.2:** Implement thread-safe in-memory ML model singleton service (`WaitTimePredictor` with `threading.RLock`). *(Completed in `api/ml_service.py`)*
10. [x] **Task 7.3:** Implement Dual-Engine Fallback mechanism with low-latency REST endpoints (`GET/POST /api/predict/`, `GET /`). *(Completed in `api/views.py`)*
11. [x] **Task 6.2:** Implement core Django ORM database models (`Service`, `Counter`, `Ticket`, `PredictionLog`) in `queue_backend/api/models.py`. *(Completed & Migrated)*
12. [x] **Task 7.4:** Develop ticket issuance and status transition REST endpoints (`POST /api/tickets/issue/`, `POST /api/counters/<counter_id>/call-next/`). *(Completed & Verified)*
13. [ ] **Task 8.1:** Scaffold React.js frontend interface using Vite (`queue-frontend`).
14. [ ] **Task 8.2:** Build Student / Kiosk self-service check-in view with digital token generation.

---

## Phase 1: Problem Formulation, Target Definition & Operational SLAs

- [x] **Task 1.1 [P0]:** Define primary prediction target variable ($W_q = t_S - t_A$) in minutes and seconds. *(Completed in research)*
- [x] **Task 1.2 [P0]:** Establish inference latency Service Level Agreement ($\le 10$ ms per prediction). *(Completed in research)*
- [x] **Task 1.3 [P1]:** Formalize accuracy criteria: ML model MAE must outperform baseline AST formula by $\ge 15\%$. *(Completed in research)*
- [x] **Task 1.4 [P1]:** Synthesize Little's Law ($L = \lambda W$) and $M/M/1$ vs. $M/M/c$ queueing theory benchmarks into documentation. *(Completed in research)*

---

## Phase 2: Data Acquisition, Hygiene & Exploration

- [x] **Task 2.1 [P0]:** Develop Python script (`main.py`) to inspect and harmonize queue datasets. *(Completed in `main.py`)*
  - Check missing values, nulls, and duplicate timestamps.
  - Verify timestamp data types and date ranges across all datasets.
- [ ] **Task 2.2 [P0]:** Validate data consistency between recorded `wait_time` and computed difference $(t_S - t_A)$.
- [x] **Task 2.3 [P1]:** Inspect and standardize secondary datasets (`data/queue_data.csv`, `data/wait_times.csv`) for potential multi-counter or cross-validation use. *(Completed in `main.py`)*
- [ ] **Task 2.4 [P1]:** Apply anomaly filtering:
  - Drop invalid records where $t_S < t_A$ (negative wait times).
  - Apply Interquartile Range (IQR) filter to identify extreme outliers caused by system pauses or unrecorded lunch breaks.
- [ ] **Task 2.5 [P2]:** Generate exploratory data analysis (EDA) plots:
  - Histogram & KDE of waiting times (checking right-skewness).
  - Queue length vs. Waiting time scatter plot.
  - Hourly arrival density plot ($\lambda(t)$ across 9:00 AM – 5:00 PM).

---

## Phase 3: Feature Engineering & Preprocessing Pipeline

- [x] **Task 3.1 [P0]:** Implement strict prediction-time feature extraction pipeline (strictly using data available at $t_A$): *(Completed in `main.py`)*
  - `queue_length`: Headcount waiting ahead at arrival (with 0-fill imputation for missing values).
  - `hour_of_day`: Integer $0 \dots 23$ extracted from `arrival_time`.
  - `day_of_week`: Integer $0 \dots 6$ extracted from `arrival_time`.
  - `is_weekend`: Binary indicator ($1$ for Saturday/Sunday, $0$ otherwise).
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

- [x] **Task 4.1 [P0]:** Implement non-ML baseline predictors on the test split: *(Completed in `main.py`)*
  - **Naïve Historical Mean:** $\widehat{W} = \text{mean}(W_{q, \text{train}})$ (Baseline MAE: 59.09 min).
  - **Last-To-Enter-Service (LES):** $\widehat{W} = W_{q, \text{latest}}$.
  - **Average Service Time (AST) Formula:** $\widehat{W}_{\text{AST}} = \frac{L_q \times \overline{S}}{c}$.
  - **Queue-Length (QL) Estimator:** $\widehat{W}_{\text{QL}} = \frac{L_q + 1}{c \cdot \mu}$.
- [x] **Task 4.2 [P0]:** Evaluate baseline performance metrics: *(Completed in `main.py`)*
  - Mean Absolute Error (MAE) in minutes.
  - Root Mean Squared Error (RMSE) in minutes.
  - Mean Absolute Percentage Error (MAPE).
- [x] **Task 4.3 [P1]:** Package the AST / QL formula as an independent fallback function to be embedded in the backend. *(Completed in `queue_backend/api/ml_service.py` with $\overline{S} = 2.38\text{ min}$)*

---

## Phase 5: Machine Learning Model Development & Validation

- [ ] **Task 5.1 [P0]:** Build an integrated Scikit-Learn `Pipeline` combining:
  - `ColumnTransformer` (scaling numerical features, one-hot/ordinal encoding categoricals).
  - Estimator: `RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)`.
- [x] **Task 5.2 [P0]:** Train and compare candidate models: *(Completed in `main.py`)*
  - `RandomForestRegressor(n_estimators=100, random_state=42)` trained on 80/20 split.
- [x] **Task 5.3 [P0]:** Evaluate models on test set and benchmark against Phase 4 baselines: *(Completed in `main.py`)*
  - MAE: 9.68 min, RMSE: 21.07 min, $R^2$: 0.9083.
  - Verified MAE improvement over baseline: 83.62% ($\ge 15\%$ requirement satisfied).
- [ ] **Task 5.4 [P1]:** Hyperparameter tuning:
  - Optimize `n_estimators`, `max_depth`, `min_samples_split` using `TimeSeriesSplit` cross-validation.
- [ ] **Task 5.5 [P1]:** Interpretability analysis:
  - Compute SHAP values or feature importances to verify domain sanity (`queue_length` should dominate).
- [x] **Task 5.6 [P0]:** Serialize the winning model/pipeline: *(Completed in `main.py`)*
  - Export using `joblib.dump(model, "wait_time_rf_model.joblib")`.
  - Standalone model file verified on disk (~33 MB).

---

## Phase 6: Database Architecture & PostgreSQL Setup

- [ ] **Task 6.1 [P0]:** Initialize PostgreSQL 15+ database instance and configure connection credentials.
- [x] **Task 6.2 [P0]:** Implement Django ORM models matching the research schema: *(Completed in `api/models.py` & migrated)*
  - `Service` (code, name, is_active).
  - `Counter` (counter_number, is_open, current_staff_name).
  - `Ticket` (ticket_number, queue_length_at_arrival, predicted_wait_minutes, actual_wait_minutes, status, timestamps).
  - `PredictionLog` (ticket reference, predicted wait, baseline wait, actual realized wait, prediction error, engine used, features snapshot).
  - Configured specialized database indexes on `(status, created_at)`, `(service, status)`, and `(engine_used)`.
  - Registered models in Django Admin (`api/admin.py`) with search, filter, and tabular inlines.
- [ ] **Task 6.3 [P1]:** Create specialized database indexes:
  - Composite partial index: `(service_id, transaction_status)` WHERE `transaction_status = 'waiting'`.
  - B-tree indexes on `waiting_start_time` and `created_at`.
- [ ] **Task 6.4 [P1]:** Seed initial facility data (e.g., College Account Section, 3 service counters: Tuition Fees, Clearance, General Inquiries).

---

## Phase 7: Backend Serving, API Orchestration & Dual-Engine Fallback

- [x] **Task 7.1 [P0]:** Initialize Django REST Framework project structure: *(Completed)*
  - Set up `queue_backend` Django project and `api` application.
  - Installed and verified `django`, `djangorestframework`, and `django-cors-headers`.
  - Configured `rest_framework`, `corsheaders`, and `api` in `INSTALLED_APPS` with CORS middleware.
- [x] **Task 7.2 [P0]:** Implement in-memory ML model singleton service (`api/ml_service.py`): *(Completed)*
  - Preload `.joblib` model at server startup inside `AppConfig.ready()`.
  - Wrap inference in thread-safe prediction method (`WaitTimePredictor` with `threading.RLock`).
- [x] **Task 7.3 [P0]:** Implement Dual-Engine Fallback mechanism: *(Completed)*
  - Primary path: Execute in-memory ML pipeline (System A).
  - Fallback path: If ML encounters error/missing values, immediately execute AST formula (System B: $\overline{S} = 2.38\text{ min}$).
- [x] **Task 7.4 [P0]:** Develop REST API endpoints: *(Completed in `api/views.py` & verified)*
  - `POST /api/tickets/issue/`: Issues ticket token, counts current queue length, predicts wait time via in-memory ML model, creates `PredictionLog`, and returns token + EWT.
  - `POST /api/counters/<counter_id>/call-next/`: Calls oldest waiting ticket in FIFO order, updates ticket state to `in_service`, records `called_at`, computes realized wait time ($W_q = t_S - t_A$), and synchronizes prediction error.
  - `POST /api/predict/`: Direct standalone prediction endpoint with parameter validation and automatic temporal inference.
  - `GET /` & `GET /api/`: Interactive API catalog and health check.
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
