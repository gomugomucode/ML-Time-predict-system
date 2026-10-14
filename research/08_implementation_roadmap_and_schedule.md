# 08. Implementation Roadmap & 12-Week Project Schedule

This document outlines the end-to-end engineering roadmap for transitioning from raw transactional queue logs (or observational field studies) to a deployed, real-time waiting-time prediction platform. The workflow is structured around the **CRISP-DM (Cross-Industry Standard Process for Data Mining)** lifecycle, mapped to an Agile 12-week delivery schedule.

---

## 1. Phase Dependency Matrix

```
[Phase 1: Problem Framing & Target Definition]
       │
       ▼
[Phase 2: Data Acquisition & Ingestion Protocol]
       │
       ▼
[Phase 3: Data Cleaning, Preprocessing & Feature Engineering]
       │
       ├──────────────────────────────────────────────┐
       ▼                                              ▼
[Phase 4: Baseline Benchmarking & Heuristics]   [Phase 6: Storage & Database Setup]
       │                                              │
       ▼                                              │
[Phase 5: ML Model Training & Optimization]          │
       │                                              │
       ├──────────────────────────────────────────────┘
       ▼
[Phase 7: Backend Serving & API Orchestration]
       │
       ▼
[Phase 8: Frontend Transport, Real-Time Delivery & MLOps]
```

---

## 2. Eight Chronological Implementation Phases

### Phase 1: Problem Formulation, Target Definition & Operational SLAs
- **Core Objectives:**
  - Formalize prediction targets: continuous waiting time ($W_q$) vs. total journey duration ($W_s$).
  - Establish strict operational Service Level Agreements (SLAs): **$\le 10$ ms inference latency** to support physical ticket printing.
  - Define success criteria: candidate ML model must achieve lower MAE and RMSE than formula-based AST and empirical LES benchmarks.
- **Upstream Prerequisites:** Facility workflow documentation and operational stakeholder sign-off.
- **Downstream Deliverables:** Project charter, Target Variable Specification Document, and Benchmark SLA Criteria.

---

### Phase 2: Data Acquisition & Ingestion Protocol
- **Core Objectives:**
  - Ingest 1–2 years of historical transactional logs from existing queue systems (if available).
  - If arrival times are missing, execute the **observational field study protocol** (logging $t_A, t_S, t_D$ across peak and off-peak days).
  - Ingest external contextual feeds: academic calendars, deadlines, and weather records.
- **Upstream Prerequisites:** Phase 1 (Target definitions and measurement unit standards).
- **Downstream Deliverables:** Staged raw transaction data lake, observational log files, and ingestion pipelines.

---

### Phase 3: Data Hygiene, Preprocessing & Feature Engineering Pipeline
- **Core Objectives:**
  - Clean data: drop negative wait durations and remove extreme anomalies using the Interquartile Range (IQR) rule.
  - Reconstruct minute-by-minute system state snapshots (`queue_status_snapshots`) capturing queue depth, active counters, arrival rates ($\lambda$), and service rates ($\mu$).
  - Compute rolling delay-history metrics (LES, rolling 7-day AST).
  - Apply log transformations ($y = \ln(W_q + 1)$) to normalize skewed waiting distributions.
- **Upstream Prerequisites:** Phase 2 (Raw event logs and timestamped records).
- **Downstream Deliverables:** Partitioned, leakage-free feature matrices (train, validation, test).

---

### Phase 4: Baseline Benchmarking & Heuristic Development
- **Core Objectives:**
  - Implement non-ML statistical baselines: Naïve Historical Mean, 4-Hour Rolling Average, Last-to-Enter-Service (LES).
  - Implement formula-based baselines: Average Service Time (AST) and analytical queue-length formulas ($\widehat{W}_{\text{QL}} = \frac{n+1}{c\mu}$).
  - Evaluate baseline MAE and RMSE to establish the performance floor.
- **Upstream Prerequisites:** Phase 3 (Feature-engineered datasets and target labels).
- **Downstream Deliverables:** Baseline Benchmark Evaluation Suite and deterministic fallback engine logic.

---

### Phase 5: Machine Learning Model Development & Validation
- **Core Objectives:**
  - Train and evaluate multiple model families: Random Forest Regressor, Gradient Boosted Trees (XGBoost / LightGBM), and Neural Networks (MLP).
  - Implement strict **temporal / rolling-window cross-validation** to prevent chronological data leakage.
  - Hyperparameter optimization via grid and randomized search.
  - Compute SHAP (Shapley Additive Explanations) values to verify feature importances and domain sanity.
  - Gate check: Candidate model must beat baseline AST MAE by $\ge 15\%$.
- **Upstream Prerequisites:** Phase 3 (Clean feature matrices) and Phase 4 (Baseline target benchmarks).
- **Downstream Deliverables:** Serialized, production-ready `.joblib` model pipeline artifact.

---

### Phase 6: Database Architecture & Data Tier Implementation
- **Core Objectives:**
  - Deploy PostgreSQL 15+ database instance.
  - Execute DDL schemas: `branches`, `departments`, `services`, `counters`, `tickets`, `service_transactions`, `queue_status_snapshots`, `rolling_service_metrics`, `model_registry`, and `prediction_logs`.
  - Create specialized partial indexes for active queues (`WHERE transaction_status = 'waiting'`).
- **Upstream Prerequisites:** Phase 1 (Entities) and Phase 3 (Feature schema specifications).
- **Downstream Deliverables:** Production relational database instance configured, seeded, and indexed.

---

### Phase 7: Backend Serving, API Orchestration & Dual-Engine Fallback
- **Core Objectives:**
  - Build RESTful endpoints in Django REST Framework: `/api/tickets/`, `/api/counters/`, `/api/predict/`, `/api/analytics/`.
  - Implement in-memory singleton model loader in `AppConfig.ready()`.
  - Wire dual-engine fallback: route to System A (ML), with automatic fallback to System B (AST formula) on error.
  - Enforce sub-10ms response time validation under load.
- **Upstream Prerequisites:** Phase 4 (Fallback logic), Phase 5 (Serialized ML artifact), Phase 6 (Database).
- **Downstream Deliverables:** High-throughput prediction and ticket orchestration API.

---

### Phase 8: Frontend Delivery, Real-Time Transport & MLOps Lifecycle
- **Core Objectives:**
  - Develop React.js interfaces: Student/Kiosk Check-In, Teller Counter Screen, Admin Dashboard.
  - Connect Django Channels WebSockets for instant state broadcasts (`ticket:created`, `ticket:called`).
  - Deploy Celery workers with Redis for minute-by-minute snapshot aggregation and delay cache updates.
  - Implement continuous model auditing: track real-time MAE/RMSE and configure nightly retraining tasks.
- **Upstream Prerequisites:** Phase 6 (Audit tables), Phase 7 (Serving APIs and WebSocket events).
- **Downstream Deliverables:** Fully operational, end-to-end system deployed with real-time sync and automated MLOps.

---

## 3. 12-Week Gantt Schedule

| Week | Project Phase | Primary Engineering Deliverables | Phase Milestone |
|---|---|---|---|
| **W1–W2** | **Phase 1: Problem Formulation** | Formalize targets ($W_q$), define latency SLA ($\le 10$ ms), domain workflows | **M1: Project Charter & SLA Spec** |
| **W1–W2** | **Phase 2: Data Acquisition** | Ingest historical transaction logs or execute 2-week observational field study | **M2: Raw Event Data Lake Ingested** |
| **W3–W4** | **Phase 3: Data Hygiene & Features** | Clean outliers, construct minute snapshots, compute rolling AST/LES features | **M3: Validated ML Feature Matrix** |
| **W5–W6** | **Phase 4: Baseline Benchmarking** | Implement AST formulas, LES, and analytical queue-length models | **M4: Baseline Suite & Fallback Logic** |
| **W5–W6** | **Phase 6: Database Deployment** | Deploy PostgreSQL 15+, create tables, partial indexes, and cache structures | **M5: Production Database Deployed** |
| **W7–W8** | **Phase 5: ML Model Training** | Train Random Forest & XGBoost, temporal cross-validation, SHAP analysis | **M6: Serialized ML Pipeline Artifact** |
| **W9–W10** | **Phase 7: Backend API & Serving** | DRF REST APIs, in-memory singleton loader, dual-engine fallback, latency tests | **M7: Low-Latency API Validated ($\le 10$ ms)** |
| **W11–W12**| **Phase 8: Frontend & Real-Time MLOps**| React UI (Kiosk, Teller, Admin), WebSockets, Celery workers, nightly retraining | **M8: Production Launch & Live Audit** |

---

## 4. Engineering Effort Allocation

```
+-------------------------------------------------------------+
| Data Engineering & Pipelines (Phases 2 & 3)           | 25% |
+-------------------------------------------------------------+
| Machine Learning & Benchmarking (Phases 1, 4 & 5)       | 25% |
+-------------------------------------------------------------+
| Backend Architecture & Database (Phases 6 & 7)        | 25% |
+-------------------------------------------------------------+
| Frontend, WebSockets & MLOps (Phase 8)                | 25% |
+-------------------------------------------------------------+
```

---

## 5. Critical Path & Risk Management

1. **The Data Hygiene Bottleneck (Weeks 3–4):**
   - *Risk:* Incomplete queue logs, missing service start times, or unrecorded server downtime.
   - *Mitigation:* Baseline formula development (Phase 4) and PostgreSQL database setup (Phase 6) execute in parallel during Weeks 5–6, ensuring backend engineering is never blocked by ML modeling.
2. **The ML Performance Gate (Week 8):**
   - *Risk:* Complex ensemble or neural network fails to beat simple delay-history (LES) or rolling AST benchmarks.
   - *Mitigation:* Candidate models must pass a strict gate: $\ge 15\%$ reduction in MAE compared to the AST baseline. If the hurdle is not met, the production deployment defaults to System B (AST formula) while feature engineering is iterated.
3. **Inference Latency SLA Violation (Week 10):**
   - *Risk:* Multi-table relational joins during ticket issuance breach the $\le 10$ ms ticket printing SLA.
   - *Mitigation:* Strict architecture separation: live inference queries read exclusively from pre-aggregated `rolling_service_metrics` cache tables updated asynchronously by Celery workers, keeping read paths $O(1)$.
