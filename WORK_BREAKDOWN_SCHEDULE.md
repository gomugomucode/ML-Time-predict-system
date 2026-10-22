# Work Breakdown Structure (WBS) & Schedule

This document defines the formal **Work Breakdown Structure (WBS)**, resource effort allocation, 12-week Gantt delivery schedule, and critical path risk analysis for the **ML-Driven Queue Waiting-Time Prediction and Management System**.

---

## 1. Overall Engineering Effort Allocation

To ensure a balanced, reliable system that avoids disproportionate investment in isolated layers, engineering capacity is divided equally across the four core disciplines:

```
┌────────────────────────────────────────────────────────┐
│  DATA ENGINEERING & PREPROCESSING (Phases 2 & 3)   │ 25% │
├────────────────────────────────────────────────────────┼─────┤
│  MACHINE LEARNING & BENCHMARKING (Phases 1, 4 & 5) │ 25% │
├────────────────────────────────────────────────────────┼─────┤
│  BACKEND & DATABASE INFRASTRUCTURE (Phases 6 & 7)  │ 25% │
├────────────────────────────────────────────────────────┼─────┤
│  FRONTEND, WEBSOCKETS & MLOPS (Phase 8)            │ 25% │
└────────────────────────────────────────────────────────┴─────┘
```

---

## 2. Hierarchical Work Breakdown Structure (WBS)

```
1.0 PROBLEM DEFINITION & QUEUEING THEORY SPECIFICATIONS
    1.1 Target Formulation & Mathematical Metrics
    1.2 Operational Service Level Agreements (SLAs)
    1.3 Queueing Theory Modeling (Little's Law, M/M/1 vs M/M/c)

2.0 DATA INGESTION, AUDIT & STAGING
    2.1 Raw Dataset Loading & Schema Verification
    2.2 Timestamp Consistency & Duration Calculations
    2.3 Anomaly Filtering & Quality Assurance

3.0 DATA PREPROCESSING & FEATURE ENGINEERING
    3.1 Arrival-Time Feature Extraction (Strict No-Leakage Policy)
    3.2 Delay-History (LES) & Rolling Metrics Computation
    3.3 Target Scaling & Transformations
    3.4 Chronological Train-Test Partitioning

4.0 BASELINE BENCHMARKING & HEURISTIC ENGINES
    4.1 Non-ML Statistical Baselines (Historical Mean, LES)
    4.2 Analytical Queueing Baselines (Average Service Time AST, QL)
    4.3 Baseline Error Benchmarking Suite (MAE, RMSE, MAPE)
    4.4 Deterministic Fallback Engine Packaging

5.0 MACHINE LEARNING MODEL DEVELOPMENT & SERIALIZATION
    5.1 Scikit-Learn Pipeline Construction
    5.2 Model Exploration (Linear, Random Forest, Gradient Boosting)
    5.3 Hyperparameter Tuning & Time-Series Cross-Validation
    5.4 Model Interpretability (SHAP Values & Feature Importance)
    5.5 Model Packaging (.joblib) & Latency Verification (<= 10 ms)

6.0 DATABASE ARCHITECTURE & PERSISTENCE LAYER
    6.1 PostgreSQL Instance Setup & Configuration
    6.2 Relational Entity Schema Definition (Django ORM)
    6.3 Database Indexing & Performance Optimization
    6.4 Initial Facility Seeding (Counters, Services, Users)

7.0 BACKEND SERVING, DRF APIS & DUAL-ENGINE FALLBACK
    7.1 Django REST Framework Application Setup
    7.2 In-Memory ML Singleton Service (Startup Preloading)
    7.3 Dual-Engine Fallback Routing Orchestration
    7.4 REST Endpoints Development (/tickets/, /counters/, /analytics/)
    7.5 Django Channels (ASGI) & WebSockets Configuration

8.0 FRONTEND INTERFACES, REAL-TIME TRANSPORT & MLOPS
    8.1 React.js (Vite) Presentation Tier Setup
    8.2 Student / Public Kiosk View & Digital QR Token
    8.3 Teller Counter Operations Interface
    8.4 Waiting Hall Display Screen
    8.5 Operations Dashboard & Accuracy Monitoring
    8.6 WebSocket Live Synchronization
    8.7 Celery Background Workers & Retraining Infrastructure
```

---

## 3. Work Package Dictionary & Task Details

| WBS Code | Work Package / Task | Description | Estimated Effort | Deliverable | Pre-requisites |
|---|---|---|---|---|---|
| **1.1** | Target Formulation | Formalize $W_q = t_S - t_A$ in minutes; specify precision and range. | 4 hrs | Spec Doc | None |
| **1.2** | SLA Definition | Define $\le 10$ ms latency limit and $\ge 15\%$ MAE improvement hurdle over AST. | 4 hrs | SLA Document | 1.1 |
| **1.3** | Queueing Theory Math | Mathematical modeling of $M/M/1$ and $M/M/c$ pooling advantages; Little's Law. | 8 hrs | Research Doc 00 | None |
| **2.1** | Raw Data Loading | Inspect `verified_queue_waiting_time_dataset.csv`, schema, and datatypes. | 6 hrs | EDA Notebook | None |
| **2.2** | Duration Audit | Verify `wait_time` column against $(t_S - t_A)$; compute service duration $(t_D - t_S)$. | 6 hrs | Validation Report | 2.1 |
| **2.3** | Anomaly Filtering | Drop negative wait times; apply IQR to isolate unrecorded server breaks. | 8 hrs | Cleaned Dataset | 2.2 |
| **3.1** | Arrival-Time Features | Extract `queue_length`, `hour_of_day`, `day_of_week`, cyclical trigonometric sine/cosine. | 10 hrs | Feature Matrix | 2.3 |
| **3.2** | Delay-History Features | Compute Last-To-Enter-Service (LES) and rolling 7-day Average Service Time (AST). | 12 hrs | Feature Matrix v2 | 3.1 |
| **3.3** | Target Transformation | Apply log transformation $y = \ln(W_q + 1)$ and build inverse transformer. | 4 hrs | Transformed Target | 3.2 |
| **3.4** | Chronological Split | Partition data into first 80% train and last 20% test chronologically. | 4 hrs | Train/Test Sets | 3.3 |
| **4.1** | Statistical Baselines | Code Historical Mean and Last-to-Enter-Service (LES) prediction logic. | 8 hrs | Baseline Script | 3.4 |
| **4.2** | Analytical Baselines | Code Average Service Time (AST) formula and Queue-Length ($\widehat{W}_{\text{QL}}$) formulas. | 8 hrs | Baseline Script | 4.1 |
| **4.3** | Benchmark Evaluation | Compute MAE, RMSE, MAPE on test split across all baselines; set performance floor. | 6 hrs | Benchmark Report | 4.2 |
| **4.4** | Fallback Packaging | Encapsulate AST formula into a standalone deterministic Python function. | 4 hrs | Fallback Module | 4.3 |
| **5.1** | Pipeline Construction | Build Scikit-Learn `Pipeline` with `ColumnTransformer` preprocessing. | 8 hrs | Pipeline Code | 3.4, 4.3 |
| **5.2** | Model Exploration | Train Linear Regression, Random Forest Regressor, and Gradient Boosting. | 14 hrs | Candidate Models | 5.1 |
| **5.3** | Tuning & Cross-Val | Tune hyperparameters (`max_depth`, `n_estimators`) via `TimeSeriesSplit`. | 12 hrs | Tuned Models | 5.2 |
| **5.4** | Interpretability | Calculate SHAP values and feature importances (validate queue length dominance). | 6 hrs | SHAP Analysis | 5.3 |
| **5.5** | Serialization & Latency | Export to `wait_time_model.joblib`; verify single-item inference latency is $\le 10$ ms. | 6 hrs | Model Artifact | 5.3 |
| **6.1** | Database Setup | Deploy PostgreSQL 15+ container/service and verify connectivity. | 6 hrs | Active DB Instance | None |
| **6.2** | Schema Implementation | Write Django ORM models for Tickets, Counters, Services, Snapshots, and Logs. | 14 hrs | Django Models | 6.1, 1.1 |
| **6.3** | Index Optimization | Create partial B-tree index on active waiting tickets (`status = 'waiting'`). | 6 hrs | Migration Scripts | 6.2 |
| **6.4** | Facility Seeding | Populate baseline branch, services (Tuition, Clearance), and counters. | 4 hrs | Seed Script | 6.2 |
| **7.1** | Django DRF Setup | Configure Django project, CORS headers, and REST Framework serializers. | 8 hrs | Base API Repo | 6.2 |
| **7.2** | In-Memory Singleton | Implement `WaitTimePredictor` singleton; preload model in `AppConfig.ready()`. | 10 hrs | `ml_service.py` | 5.5, 7.1 |
| **7.3** | Dual-Engine Routing | Wire prediction routing: try System A (ML) $\to$ except System B (AST baseline). | 8 hrs | Serving Logic | 7.2, 4.4 |
| **7.4** | API Endpoints | Build `/api/tickets/` (creation + prediction) and `/api/counters/` endpoints. | 14 hrs | REST Endpoints | 7.3 |
| **7.5** | WebSockets (Channels) | Set up Django Channels ASGI + Redis layer for `queue:updated` broadcasts. | 12 hrs | ASGI Consumer | 7.4 |
| **8.1** | React Setup | Initialize React + Vite project with Tailwind/Vanilla CSS tokens. | 6 hrs | Frontend Repo | None |
| **8.2** | Student Kiosk View | Build ticket issue screen, service selector, and digital token/QR view. | 14 hrs | Kiosk Page | 7.4, 8.1 |
| **8.3** | Teller Counter View | Build staff call interface ("Call Next", "Serve", "Complete", queue count). | 14 hrs | Teller Dashboard | 7.4, 8.1 |
| **8.4** | Hall Display Screen | Build full-screen public display showing currently called tokens and wait times. | 8 hrs | Display Screen | 7.5, 8.1 |
| **8.5** | Admin Dashboard | Build operational graphs ($L_q, \rho, \lambda$) and live prediction accuracy audit. | 14 hrs | Admin Dashboard | 7.4, 8.1 |
| **8.6** | WebSocket UI Sync | Connect React WebSocket hook to re-render queue states on live events. | 10 hrs | Live UI Sync | 7.5, 8.2-8.5 |
| **8.7** | Celery & Retraining | Configure Celery worker for scheduled snapshot rollups and nightly accuracy audit. | 12 hrs | Async Worker | 7.4 |

---

## 4. 12-Week Gantt Schedule & Milestone Progression

```
WEEK:  1   2   3   4   5   6   7   8   9   10  11  12
───────────────────────────────────────────────────────
Ph 1: [████]                                          (Milestone 1: Project Charter & SLAs)
Ph 2: [████████]                                      (Milestone 2: Raw Staged Dataset)
Ph 3:         [████████]                              (Milestone 3: Validated Feature Matrix)
Ph 4:                 [████████]                      (Milestone 4: Baseline Benchmark Suite)
Ph 6:                 [████████]                      (Milestone 5: PostgreSQL Deployed & Seeded)
Ph 5:                         [████████]              (Milestone 6: Serialized ML Pipeline)
Ph 7:                                 [████████]      (Milestone 7: Prediction API Serving <= 10ms)
Ph 8:                                         [████████] (Milestone 8: Live Real-Time System)
```

### Review Checkpoints & Quality Gates
- **Gate 1 (End of Week 2):** Raw dataset cleaned and validated; zero negative wait times.
- **Gate 2 (End of Week 4):** Leakage-free feature matrix generated with chronological train/test partitioning.
- **Gate 3 (End of Week 6):** Baseline benchmarks calculated (MAE/RMSE for Mean, LES, AST); PostgreSQL schema deployed and indexed.
- **Gate 4 (End of Week 8):** ML model trained; candidate model must demonstrate $\ge 15\%$ lower MAE than baseline AST and latency $\le 10$ ms.
- **Gate 5 (End of Week 10):** Dual-engine API operational in Django; model preloaded in process memory; fallback tested.
- **Gate 6 (End of Week 12):** React interfaces connected via WebSockets; full ticket lifecycle verified end-to-end.

---

## 5. Critical Path & Risk Analysis

The critical path of the project runs through:
$$\text{Phase 1} \longrightarrow \text{Phase 2} \longrightarrow \text{Phase 3} \longrightarrow \text{Phase 5} \longrightarrow \text{Phase 7} \longrightarrow \text{Phase 8}$$

### Key Bottlenecks and Buffer Strategies
1. **The Feature Engineering Bottleneck (Weeks 3–4):**  
   *Risk:* Complex delay-history aggregations slowing down progress.  
   *Mitigation:* Baseline model creation (Phase 4) and PostgreSQL database setup (Phase 6) run concurrently in Weeks 5–6 so that ML tuning and backend modeling can begin immediately.
2. **The ML Performance Gate (Week 8):**  
   *Risk:* ML model fails to beat simple AST formula.  
   *Mitigation:* The dual-engine architecture ensures the system is functional regardless: if ML models do not meet the 15% improvement threshold, the system immediately uses the verified AST formula as its active engine while refining features.
3. **Inference Latency Spike (Week 10):**  
   *Risk:* Live queries during ticket issuance exceeding 10 ms SLA.  
   *Mitigation:* Preload model at application boot (`AppConfig.ready()`) and query pre-aggregated rolling metrics rather than performing expensive `COUNT(*)` or `AVG()` table scans during client requests.
