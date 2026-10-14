# 04. Database Schema & Entity Design (PostgreSQL)

To build a production waiting-time prediction and queue orchestration application, the database schema must serve two distinct functions:
1. **Real-Time Operational Queue Management:** Sub-10 millisecond ticket creation, counter calling, customer routing, and state transitions.
2. **Analytical ML Feature Extraction & Auditing:** Logging continuous system snapshots (waiting counts, active servers, arrival rates), caching rolling delay metrics (LES, AST), and maintaining an immutable prediction audit log.

---

## 1. Five Core Entity Groups

```
+-------------------------------------------------------------------------------------------------+
|                                    1. STRUCTURAL / CONFIGURATION                                |
|  [Branch] <---1:N---> [Department/Hall] <---1:N---> [Counter] <---M:N---> [Service]            |
|                                                         ^                     ^                 |
+---------------------------------------------------------|---------------------|-----------------+
                                                          |                     |
+---------------------------------------------------------|---------------------|-----------------+
|                                    2. TRANSACTIONAL / JOURNEY                 |                 |
|  [Customer] <---1:N---> [Ticket / Queue_Visit] <---1:N---> [Service_Transaction]               |
|                                  |                                                              |
+----------------------------------|--------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------------------------------+
|                              3. AUDIT & MODEL REGISTRY                                          |
|  [Ticket] <---1:N---> [Prediction_Log] <---N:1---> [Model_Registry]                             |
+-------------------------------------------------------------------------------------------------+
                                   ^
                                   | Features read from
+----------------------------------|--------------------------------------------------------------+
|                              4. TIME-SERIES & FEATURE CACHE                                     |
|  [Queue_Status_Snapshot] (Minute/hourly system states)                                          |
|  [Rolling_Service_Metrics] (Cached LES, 7-day rolling AST)                                      |
|  [Exogenous_Context] (Holidays, academic deadlines, weather)                                   |
+-------------------------------------------------------------------------------------------------+
```

---

## 2. Entity Dictionary & Attributes

### Group 1: Structural & Configuration Entities
- **`branches`**: Physical facilities (e.g., Main Administrative Building, South Campus Center).
- **`departments`**: Functional halls (e.g., Accounts Section, Registrar, Admissions).
- **`services`**: Specific transaction categories offered (e.g., Tuition Fee, Fine Clearance, Exam Admit Card).
- **`counters`**: Physical teller windows/desks, tracking operational state (`open`, `serving`, `paused`, `offline`).
- **`counter_service_mappings`**: Many-to-many junction enabling multi-skilled counters to handle multiple service types.
- **`staff_users`**: Tellers and administrators assigned to counters.

### Group 2: Transactional & Customer Journey Entities
- **`customers`**: Visitor profile (Student ID, name, contact info, category).
- **`tickets`**: Represents the physical/virtual token withdrawn at the kiosk. Stores initial queue position, priority level, channel, and arrival epoch $t_A$.
- **`service_transactions`**: Supports multi-stage visits (e.g., Stage 1: Document Check $\rightarrow$ Stage 2: Cashier). Stores timestamps $t_A, t_S, t_D$, status (`waiting`, `in_service`, `completed`, `balked`, `reneged`), and calculated ground-truth durations:
  - $W_q = t_S - t_A$ (`waited_time_seconds`)
  - $S = t_D - t_S$ (`service_duration_seconds`)

### Group 3: Time-Series Queue Status Snapshot Entities
- **`queue_status_snapshots`**: Minute-level or hourly system status snapshots. Stores instantaneous queue depth, active server counts, incoming arrival rates ($\lambda$), and completion rates ($\mu$).
- **`exogenous_contexts`**: Date-keyed records of public holidays, academic calendar milestones (e.g., "Tuition Fee Deadline"), and weather conditions.

### Group 4: Rolling Metrics & Delay-History Cache
- **`rolling_service_metrics`**: Pre-aggregated features updated by background workers so inference requests avoid expensive table scans:
  - `last_similar_waited_time`: Wait time of the Last-to-Enter-Service (LES) customer.
  - `ast_estimated_time_seconds`: 7-day Average Service Time (AST) formula benchmark.
  - Rolling 1h/4h average and standard deviation of waiting times.

### Group 5: Prediction Audit & Model Registry Entities
- **`model_registry`**: Catalog of trained model artifacts (e.g., `RandomForestRegressor_v2.1`, `XGBoost_v1.0`), their hyperparameter configurations, and validation benchmarks (MAE, RMSE, $R^2$).
- **`prediction_logs`**: Immutable log of every prediction made at ticket withdrawal: predicted wait time, baseline AST estimate, actual realized wait time, and calculated prediction error.

---

## 3. Production PostgreSQL 15+ DDL Schema

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. STRUCTURAL / CONFIGURATION ENTITIES
-- ============================================================================

CREATE TABLE branches (
    branch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    location VARCHAR(255),
    operating_hours JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE departments (
    department_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id UUID NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    floor_number INT DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE services (
    service_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    service_code VARCHAR(20) UNIQUE NOT NULL,
    base_priority INT NOT NULL DEFAULT 1, -- 1=Normal, 2=Senior, 3=Emergency
    avg_service_time_seconds NUMERIC(8, 2) NOT NULL DEFAULT 180.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE counters (
    counter_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    counter_number VARCHAR(20) NOT NULL,
    current_status VARCHAR(20) NOT NULL DEFAULT 'offline' 
        CHECK (current_status IN ('open', 'serving', 'paused', 'offline')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE counter_service_mappings (
    counter_id UUID NOT NULL REFERENCES counters(counter_id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(service_id) ON DELETE CASCADE,
    PRIMARY KEY (counter_id, service_id)
);

-- ============================================================================
-- 2. TRANSACTIONAL & CUSTOMER JOURNEY ENTITIES
-- ============================================================================

CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    phone_number VARCHAR(30),
    customer_type VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tickets (
    ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE SET NULL,
    ticket_number VARCHAR(30) NOT NULL,
    priority_level INT NOT NULL DEFAULT 1,
    channel VARCHAR(30) NOT NULL DEFAULT 'kiosk' CHECK (channel IN ('kiosk', 'mobile_app', 'web_portal', 'manual')),
    people_in_front_at_arrival INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE service_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(service_id),
    counter_id UUID REFERENCES counters(counter_id),
    stage_sequence_order INT NOT NULL DEFAULT 1,
    transaction_status VARCHAR(20) NOT NULL DEFAULT 'waiting'
        CHECK (transaction_status IN ('waiting', 'in_service', 'completed', 'balked', 'reneged')),
    waiting_start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    serving_start_time TIMESTAMPTZ,
    serving_end_time TIMESTAMPTZ,
    waited_time_seconds NUMERIC(10, 2),
    service_duration_seconds NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. TIME-SERIES & FEATURE CACHE ENTITIES
-- ============================================================================

CREATE TABLE queue_status_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    department_id UUID NOT NULL REFERENCES departments(department_id),
    service_id UUID NOT NULL REFERENCES services(service_id),
    hour_of_day INT NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    customers_waiting_count INT NOT NULL DEFAULT 0,
    active_servers_count INT NOT NULL DEFAULT 0,
    arrival_rate_per_min NUMERIC(6, 3) NOT NULL DEFAULT 0.0,
    service_rate_per_min NUMERIC(6, 3) NOT NULL DEFAULT 0.0
);

CREATE TABLE rolling_service_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID NOT NULL REFERENCES services(service_id) ON DELETE CASCADE,
    priority_level INT NOT NULL DEFAULT 1,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    avg_wait_prev_day_seconds NUMERIC(10, 2),
    avg_wait_curr_day_seconds NUMERIC(10, 2),
    std_wait_curr_day_seconds NUMERIC(10, 2),
    last_similar_waited_time_seconds NUMERIC(10, 2), -- LES
    ast_estimated_time_seconds NUMERIC(10, 2),       -- AST formula benchmark
    UNIQUE (service_id, priority_level)
);

CREATE TABLE exogenous_contexts (
    calendar_date DATE PRIMARY KEY,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    special_event_flag VARCHAR(100), -- e.g. 'Tuition Fee Deadline'
    weather_condition VARCHAR(50) DEFAULT 'clear',
    temperature_celsius NUMERIC(4, 1)
);

-- ============================================================================
-- 4. PREDICTION AUDIT & MODEL REGISTRY
-- ============================================================================

CREATE TABLE model_registry (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    algorithm_name VARCHAR(100) NOT NULL, -- e.g. 'RandomForestRegressor'
    model_version VARCHAR(50) NOT NULL,
    artifact_path VARCHAR(255) NOT NULL,
    hyperparameters JSONB,
    eval_mae NUMERIC(8, 2),
    eval_rmse NUMERIC(8, 2),
    eval_r2 NUMERIC(5, 4),
    is_active_production BOOLEAN NOT NULL DEFAULT FALSE,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE prediction_logs (
    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    model_id UUID REFERENCES model_registry(model_id),
    prediction_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    predicted_wait_time_seconds NUMERIC(10, 2) NOT NULL,
    baseline_ast_prediction_seconds NUMERIC(10, 2),
    actual_wait_time_seconds NUMERIC(10, 2),
    prediction_error_seconds NUMERIC(10, 2),
    engine_used VARCHAR(50) NOT NULL DEFAULT 'scikit_learn_rf'
);

-- ============================================================================
-- 5. PERFORMANCE INDEXES (FOR SUB-10MS QUERY LATENCY)
-- ============================================================================

-- Fast active queue lookup for teller screens
CREATE INDEX idx_transactions_active_queue 
    ON service_transactions(service_id, transaction_status) 
    WHERE transaction_status = 'waiting';

-- Rapid timestamp filtering for rolling feature aggregations
CREATE INDEX idx_transactions_waiting_start 
    ON service_transactions(waiting_start_time DESC);

CREATE INDEX idx_tickets_created_at 
    ON tickets(created_at DESC);

-- Snapshot time-series query index
CREATE INDEX idx_snapshots_service_time 
    ON queue_status_snapshots(service_id, snapshot_timestamp DESC);

-- Prediction audit index
CREATE INDEX idx_prediction_logs_ticket 
    ON prediction_logs(ticket_id);
```
