# 01. Feature Engineering & Target Variable Definition

This document outlines the core feature taxonomy, prediction-time data availability constraints, target variable formulations, and mathematical calculation methods for queue waiting-time prediction models.

---

## 1. Feature Taxonomy for Waiting-Time Prediction

In machine-learning queue prediction systems, input features are classified into five primary operational categories:

### A. System State & Queue Dynamics (Queue-Length Predictors)
These capture the instantaneous state of the queue at the moment of prediction:
- **Queue Length / Waiting Count ($L_q$):** Total number of customers, patients, or jobs currently waiting in line ahead of or at arrival. *Consistently proven across empirical literature to be the single most critical predictor.*
- **Service & Arrival Rates ($\lambda, \mu$):** Real-time empirical arrival rates (arrivals/minute or hour) and instantaneous service completion rates.
- **Active Server Capacity ($c$ or $s$):** Number of operational teller counters, active clinicians, or active computing nodes.
- **Queue Workload / Congestion Metrics:** Aggregate requested runtime, pending processing requirements, or bed census counts in healthcare.

### B. Delay-History (DH) & Rolling Performance Metrics
These reflect recent realized latency without requiring rigid distribution assumptions:
- **Last-To-Enter-Service (LES):** The actual waiting time experienced by the most recent customer of the same service category/priority class who began service.
- **Historical Rolling Averages:** Moving-window average waiting times and service durations calculated over the last 1 hour, 4 hours, current day, or previous day.
- **Lagged Queue Variables:** Historical wait times and queue counts at specific lag intervals (e.g., $t-12\text{h}$, $t-24\text{h}$, $t-48\text{h}$) to capture autoregressive periodicity.

### C. Temporal & Calendar Features
Features capturing cyclical human behavior and organizational operations:
- **Time & Date Attributes:** Hour of day (0–23), day of week (Monday–Sunday), day of month, and month/season.
- **Operational Shifts:** Categorical indicators for morning, afternoon, or evening shifts, and teller handover windows.
- **Holidays & Event Flags:** Binary indicators for public holidays, semester payment deadlines, campus events, or local peak incidents.

### D. Entity & Request Attributes (Static Arrival Properties)
Attributes specific to the arriving entity:
- **Priority / Triage Class:** VIP, emergency, appointment, standard walk-in, or Emergency Severity Index (ESI) level.
- **Service / Transaction Type:** Specific service requested (e.g., tuition fee, scholarship disbursement, general inquiry, cash deposit).
- **Resource Demands / Demographics:** Age group, customer type, or requested walltime limits for computing tasks.

### E. Exogenous & Environmental Factors
- **Weather Conditions:** Rain, snow, ambient temperature, and weather severity index (influencing physical transit and arrival surges).

---

## 2. Feature Availability at Prediction Time (Data Leakage Prevention)

A critical requirement in queue modeling is preventing **data leakage** by strictly separating what is known at prediction time from what only becomes known downstream.

```
Arrival / Ticket Issuance Epoch (t_A)
│
├── [AVAILABLE FEATURES] ──────────────────────────────────────────┐
│   ✔ Instantaneous Queue Length (headcount ahead in line)         │
│   ✔ Number of Active / Open Counters                             │
│   ✔ Real-time Arrival Rate (recent 15/30 min window)             │
│   ✔ Last-to-Enter-Service (LES) realized wait time               │
│   ✔ Rolling Average Service Time (AST)                           │
│   ✔ Calendar Attributes (Hour, Day of Week, Holiday Flag)        │
│   ✔ Customer / Transaction Category & Priority Class             │
│   ✔ Environmental / Weather Conditions                           │
└───┬──────────────────────────────────────────────────────────────┘
    │
    ▼ [WAITING PERIOD - W_q]
    │
Service Start Epoch (t_S)
│
├── [STRICTLY FORBIDDEN AT t_A] ───────────────────────────────────┐
│   ✖ Actual Service Duration of this customer (S)                 │
│   ✖ Exact Service Times of customers ahead in line               │
│   ✖ Future arrivals or emergency walk-ins that arrive after t_A  │
│   ✖ Downstream clinical / diagnostic results                     │
│   ✖ Mid-queue server downtime / unplanned staff breaks           │
└───┬──────────────────────────────────────────────────────────────┘
    │
    ▼ [SERVICE PERIOD - S]
    │
Service Completion Epoch (t_D)
```

### Feature Availability Matrix

| Feature | Available at $t_A$? | Source | Processing Method |
|---|---|---|---|
| `queue_length_ahead` | **Yes** | Instantaneous snapshot | Direct integer count |
| `active_servers` | **Yes** | Counter status table | Active server count |
| `service_category` | **Yes** | Kiosk / Ticket selection | One-hot / Target encoding |
| `priority_level` | **Yes** | Customer / Ticket profile | Ordinal / Categorical |
| `hour_of_day` | **Yes** | Timestamp $t_A$ | Cyclic sine/cosine encoding |
| `day_of_week` | **Yes** | Timestamp $t_A$ | Cyclic sine/cosine encoding |
| `last_to_enter_service_wait` | **Yes** | Delay-history cache | Log-transformed continuous |
| `rolling_ast_7d` | **Yes** | Rolling metrics cache | Continuous (seconds) |
| `actual_service_duration` | **NO** | Available only at $t_D$ | Must **never** be an input feature |
| `future_queue_arrivals` | **NO** | Unborn future events | Stochastic; captured via rolling rate |

---

## 3. Target Variable Formulations

Depending on the operational goal, the target variable $y$ can be modeled in several ways:

### 1. Pure Queue Waiting Time ($W_q$) — Primary Regression Target
- **Definition:** The continuous time elapsed between entering the queue (ticket withdrawal timestamp) and the initiation of service at a counter.
- **Unit:** Seconds or decimal minutes.
- **Characteristics:** Highly positive, often right-skewed; typically modeled with log-transformed targets: $y = \ln(W_q + 1)$.

### 2. Total System / Sojourn Time ($W_s$)
- **Definition:** Total time spent in the system from arrival to departure.
- $$W_s = W_q + S$$
- **Use Case:** End-to-end customer satisfaction analysis where overall visit time is the primary KPI.

### 3. Start-of-Treatment Time
- **Definition:** Used in healthcare/ER settings: time from registration/triage to the first medical intervention. Strongly correlated with clinical outcomes and patient retention.

### 4. Categorical Waiting Time Buckets (Classification Target)
- Discretized ordinal bands (e.g., `< 5 min`, `5–15 min`, `15–30 min`, `> 30 min`).
- Useful for simplified public-facing mobile displays (e.g., Green / Yellow / Red congestion badges).

### 5. Multi-Step Future Queue Length ($L_{q, t+h}$)
- Predicting aggregate waiting line depth $h$ hours into the future for capacity planning and shift scheduling.

---

## 4. Mathematical Ground-Truth & Heuristic Calculations

### A. Transactional Log Calculation (Ground Truth)
From raw timestamped event logs:

$$\text{Queue Waiting Time: } W_q = t_S - t_A$$

$$\text{Service Duration: } S = t_D - t_S$$

$$\text{Total System Time: } W_s = t_D - t_A = W_q + S$$

Where:
- $t_A$ = Arrival / Ticket generation epoch
- $t_S$ = Serving start epoch (teller calls ticket)
- $t_D$ = Service completion / departure epoch

### B. Multi-Stage Journey Aggregation
When a customer must complete a sequence of $n$ distinct service stages (e.g., Account Inquiry $\rightarrow$ Fee Payment $\rightarrow$ Clearance Verification):

$$T[\text{visit}] = \sum_{x=1}^{n} WS(x, \text{hall}, \text{counter}) + \sum_{x=1}^{n-1} SS(x, \text{hall}, \text{counter})$$

Where $WS(x)$ is the waiting time experienced at stage $x$, and $SS(x)$ is the active service duration at stage $x$.

### C. Heuristic & Formula-Based Benchmarks (Non-ML)
These provide the non-ML baseline targets:

#### 1. Average Service Time (AST) Formula
For a new arrival facing $K$ customers ahead in queue:

$$\widehat{W}_{\text{AST}} = \sum_{k=1}^{K} \overline{S}_{k}$$

Where $\overline{S}_{k}$ is the historical average service duration for the transaction type requested by customer $k$.

#### 2. Last-To-Enter-Service (LES) Baseline
$$\widehat{W}_{\text{LES}}(t) = W_{q, \text{most recent served of same class}}$$
An empirical delay-history metric that adapts quickly to sudden line stoppages without requiring queue counts.
