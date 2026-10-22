# 09. Project Kickoff, Technology Selection & Execution Strategy

This document addresses key strategic questions when starting a machine-learning queue prediction system from scratch with sample datasets: **Where to start (Data vs. Backend vs. Frontend)**, **Technology Selection (Python Django vs. Node.js)**, and the **Immediate 4-Step Action Plan**.

---

## 1. Where to Start: Data/ML First, Backend Second, Frontend Last

When initiating an ML-driven queue management system, developers often wonder whether to start with the frontend UI, the backend API, or the machine learning pipeline.

```
┌────────────────────────────────────────────────────────┐
│ STEP 1: DATA EXPLORATION & ML PROTOTYPING (Notebook/Py)│
│ - Inspect data schema, column types, and distributions │
│ - Calculate target variable (wait_time = start - arriv)│
│ - Engineer prediction-time features (no leakage!)      │
│ - Fit non-ML baselines and prototype ML model          │
│ - Export trained pipeline to .joblib artifact          │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ STEP 2: BACKEND & DATABASE (Django REST + PostgreSQL)  │
│ - Define models (Branch, Counter, Ticket, Snapshot)    │
│ - Load .joblib artifact as in-memory singleton         │
│ - Create /api/tickets/ and /api/predict/ endpoints     │
│ - Build deterministic fallback (AST / QL formula)      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ STEP 3: FRONTEND INTERFACE (React.js + WebSockets)     │
│ - Kiosk / Mobile Check-in (Ticket generation + EWT)    │
│ - Teller Station UI (Call ticket, start, complete)     │
│ - Public Waiting Hall Display (Live queue & status)    │
│ - Admin Operations & Model Accuracy Dashboard          │
└────────────────────────────────────────────────────────┘
```

### Why You Must Start with Data & ML Prototyping

1. **Avoid Wasteful Architectural Rework:**  
   If you design database tables, backend serializers, or frontend forms before exploring your data, you will inevitably guess the input features incorrectly. When you later train your ML model and realize certain features are unavailable at ticket arrival (data leakage) or require different formats, you will have to rewrite your frontend forms, backend APIs, and database migrations.

2. **Understand Feature Constraints at Prediction Time:**  
   At the moment a ticket is issued ($t_A$), you only have access to arrival timestamp, current queue length ahead, and active counter status. Service duration and departure time are strictly future events. Inspecting the raw data ensures you build features that reflect this real-world reality.

3. **Establish Model Feasibility & Performance Floor:**  
   Before building microservices and web sockets, verify that an ML model (e.g., Random Forest or Gradient Boosting) actually outperforms simple baselines (like Average Service Time or Last-To-Enter-Service).

---

## 2. Backend Technology Selection: Python Django vs. Node.js

| Evaluation Criteria                | Python Django (DRF)                                                                                                                                                                    | Node.js (Express / NestJS)                                                                                                                                                                                                   | Winning Recommendation                                        |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **ML Model Serving & Latency**     | **Native In-Memory Loading:** Scikit-learn/XGBoost models load directly into Python process memory via `joblib`. Predictions execute in $< 10$ ms without inter-process communication. | **External Process Required:** Node cannot natively execute scikit-learn models. Requires spawning Python child processes or making HTTP calls to a secondary microservice, adding serialization latency and failure points. | **Python Django**                                             |
| **Architectural Simplicity**       | **Single Backend Service:** One Python virtual environment manages database models, business logic, REST APIs, and ML inference.                                                       | **Dual-Service Architecture:** Must maintain two separate codebases (Node.js web server + Python FastAPI ML service) with independent containerization and CI/CD pipelines.                                                  | **Python Django**                                             |
| **Database ORM & Migrations**      | **Django ORM:** Mature, automated migrations, built-in connection pooling, and rich querying for PostgreSQL.                                                                           | Prisma or TypeORM: Modern, but requires extra configuration for complex time-series queries.                                                                                                                                 | **Python Django**                                             |
| **Admin & Operational Backoffice** | **Django Admin (Built-in):** Instant UI out-of-the-box to manage service counters, view ticket logs, inspect status snapshots, and audit predictions without writing frontend code.    | Must build custom admin screens or integrate third-party CMS tools.                                                                                                                                                          | **Python Django**                                             |
| **Real-Time WebSockets**           | Handled natively using **Django Channels (ASGI) + Redis** for asynchronous event broadcasting (`queue:updated`, `ticket:called`).                                                      | Excellent native asynchronous event loop (Socket.io).                                                                                                                                                                        | Node.js (slight edge), but Django Channels is fully adequate. |

### Conclusion: **Use Python Django & Django REST Framework (DRF)**

Python Django is the undisputed best choice because keeping ML inference inside the same process guarantees sub-10 ms latency, eliminates multi-service deployment headaches, and provides an immediate admin backoffice to inspect queue states.

---

## 3. Immediate 4-Step Action Plan for This Project

Given the sample datasets available in `data/` (`verified_queue_waiting_time_dataset.csv`, `queue_data.csv`, `wait_times.csv`), here is your direct, step-by-step roadmap:

### Step 1: Inspect & Preprocess the Dataset (Current Phase)

1. Load `data/verified_queue_waiting_time_dataset.csv` in Python.
2. Verify timestamp fields (`arrival_time`, `start_time`, `finish_time`).
3. Compute the ground truth target:
   $$\text{wait\_time\_minutes} = \frac{\text{start\_time} - \text{arrival\_time}}{60\text{ seconds}}$$
   $$\text{service\_time\_minutes} = \frac{\text{finish\_time} - \text{start\_time}}{60\text{ seconds}}$$
4. Engineer prediction-time features:
   - `queue_length`: Headcount waiting ahead at arrival.
   - `hour_of_day`: $0 \dots 23$.
   - `day_of_week`: $0 \dots 6$.
   - `is_weekend`: Binary flag.
   - Rolling Average Service Time (AST) from recent completions.

### Step 2: Fit Baseline Benchmarks & Prototype ML Pipeline

1. Compute baseline errors (MAE, RMSE) using:
   - Historical Mean waiting time.
   - Last-To-Enter-Service (LES).
   - Analytical Queue-Length estimator: $\widehat{W}_{\text{QL}} = \frac{\text{queue\_length} + 1}{c \cdot \mu}$.
2. Train prototype models using scikit-learn:
   - `LinearRegression` / `Ridge`
   - `RandomForestRegressor`
   - `HistGradientBoostingRegressor` / `XGBoost`
3. Validate using chronological train-test split (e.g., first 80% chronologically for training, last 20% for testing).
4. Save the fitted model pipeline:
   ```python
   import joblib
   joblib.dump(pipeline, "artifacts/wait_time_model.joblib")
   ```

### Step 3: Scaffold the Django REST API Backend

1. Initialize Django project and application:
   ```bash
   django-admin startproject queue_backend
   python manage.py startapp api
   ```
2. Configure PostgreSQL database connection in `settings.py`.
3. Create models: `Service`, `Counter`, `Ticket`, `QueueSnapshot`, `PredictionLog`.
4. Implement the in-memory singleton predictor (`ml_service.py`) and preload the model in `AppConfig.ready()`.
5. Expose REST endpoints:
   - `POST /api/tickets/`: Issues a new ticket, queries queue depth, executes ML inference, logs prediction, and returns Estimated Waiting Time (EWT).
   - `PATCH /api/tickets/{id}/status/`: Updates ticket lifecycle (`waiting` $\to$ `in_service` $\to$ `completed`).
   - `GET /api/counters/{id}/queue/`: Returns the active waiting line for counter staff.

### Step 4: Build the React.js Frontend

1. Initialize React frontend using Vite:
   ```bash
   npm create vite@latest queue-frontend -- --template react
   ```
2. Build 3 core interfaces:
   - **Student / Visitor Kiosk:** Enter details, draw ticket, view real-time countdown and queue position.
   - **Teller Counter Screen:** "Call Next", "Start Service", "Complete", "Mark Absent".
   - **Waiting Hall Display / Admin Dashboard:** Current token being served, queue depth, average wait, and model accuracy metrics.
3. Connect Django Channels WebSockets for instant state updates without manual page refreshes.
