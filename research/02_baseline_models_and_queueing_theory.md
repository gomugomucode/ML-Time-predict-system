# 02. Baseline Models & Queueing Theory Benchmarks

Before training complex machine learning models (such as Random Forest, XGBoost, or Deep Neural Networks), operational literature and queueing theory mandate establishing **non-ML baseline models**. These models serve as the benchmark: if an ML model cannot significantly outperform these baselines in Mean Absolute Error (MAE) or Root Mean Squared Error (RMSE), its operational overhead is unjustified.

---

## 1. Why Baseline Models Matter

1. **Zero-Training Simplicity:** Naïve, Delay-History, and analytical formulas require no GPU resources, training pipelines, or hyperparameter optimization.
2. **Performance Floor:** They define the minimum acceptable accuracy.
3. **Fail-Safe Mechanism:** Analytical formulas (e.g., AST or Queue-Length estimators) act as instantaneous fallback engines if the primary ML model encounters unexpected or out-of-distribution inputs.

---

## 2. Naïve & Empirical Rolling-Average Baselines

### A. Historical Mean Predictor
Predicts the static historical average waiting time:

$$\widehat{W}_{\text{Mean}} = \frac{1}{N} \sum_{i=1}^{N} W_{q, i}$$

Often segmented by time bucket (e.g., historical mean for Mondays between 10:00 AM – 11:00 AM).

### B. Empirical Rolling $p$-Hour Average
Predicts wait time by computing the moving average of customers served over the preceding $p$ hours (e.g., the standard 4-hour empirical rolling average used in emergency departments):

$$\widehat{W}_{\text{Roll-p}}(t) = \frac{1}{|K_p(t)|} \sum_{j \in K_p(t)} W_{q, j}$$

Where $K_p(t)$ is the set of customers who completed waiting within the window $[t - p, t]$.

### C. Naïve Latest Known
Assumes the arriving customer will experience the exact waiting time of the most recently completed customer whose wait time has fully resolved. Reveals whether an ML model is truly capturing queue dynamics or merely lagging behind a delayed signal.

---

## 3. Delay-History (DH) Predictors

Delay-history predictors estimate delays using only recently realized durations, eliminating the need to estimate arrival rates ($\lambda$) or service rates ($\mu$).

### A. Last-To-Enter-Service (LES)
Predicts delay using the actual waiting duration experienced by the last customer of the same class who entered service:

$$\widehat{W}_{\text{LES}}(t) = W_{q, \text{latest called to counter}}$$

*Advantages:* Extremely simple, robust to unobserved server slowdowns.  
*Disadvantages:* Lags behind sudden demand spikes or queue surges.

### B. Head-of-Line (HOL)
Uses the elapsed waiting time already spent by the customer currently at the very front of the line:

$$\widehat{W}_{\text{HOL}}(t) = t - t_{A, \text{customer at front}}$$

*Advantages:* Direct real-time signal of the current backlog.

### C. Average LES (Avg-LES & AvgC-LES)
Computes the mean wait across the last $N$ customers called to service ($N \in [5, 15]$), or conditions the average on recent customers who encountered an identical queue length upon arrival.

### D. Proportional Queue LES (P-LES) & Extrapolated LES (E-LES)
Adjusts the LES observation proportionally by the ratio of current queue length to the queue length seen by the LES customer:

$$\widehat{W}_{\text{P-LES}}(t) = \widehat{W}_{\text{LES}}(t) \cdot \frac{Q(t) + 1}{Q(t_{\text{LES}}) + 1}$$

---

## 4. Analytical Queueing Theory (QT) Predictors

### A. Standard Queue-Length (QL) Estimator
For a system with $Q(t) = n$ customers waiting, $s(t)$ active servers, and mean service rate $\mu$ (where mean service time $m = 1/\mu$):

$$\widehat{W}_{\text{QL}} = \frac{Q(t) + 1}{s(t) \cdot \mu} = \frac{n + 1}{s \cdot \mu}$$

In an idealized $GI/M/s$ queue without abandonments, $\widehat{W}_{\text{QL}}$ represents the exact conditional expectation of wait time given the current queue depth.

### B. Classical $M/M/1$ Queueing Model
Assumptions:
- Poisson arrival process with rate $\lambda$ (exponential inter-arrival times)
- Exponential service times with rate $\mu$
- Single server ($c = 1$), infinite queue capacity, First-Come First-Served (FCFS) discipline

**Key Mathematical Formulations:**
1. **Traffic Intensity (Server Utilization):**
   $$\rho = \frac{\lambda}{\mu} \quad (\text{Stability condition: } \rho < 1)$$
2. **State Probability ($n$ customers in system):**
   $$P_n = (1 - \rho)\rho^n$$
   $$P_0 = 1 - \rho \quad (\text{Probability of server being idle})$$
3. **Average Number of Customers in System ($L$):**
   $$L = \frac{\rho}{1 - \rho} = \frac{\lambda}{\mu - \lambda}$$
4. **Average Number of Customers Waiting in Queue ($L_q$):**
   $$L_q = \frac{\rho^2}{1 - \rho} = \frac{\lambda^2}{\mu(\mu - \lambda)}$$
5. **Average Total Time in System ($W_s$ or $W$):**
   $$W_s = \frac{1}{\mu - \lambda} = \frac{L}{\lambda}$$
6. **Average Waiting Time in Queue ($W_q$):**
   $$W_q = \frac{\lambda}{\mu(\mu - \lambda)} = \frac{\rho}{\mu(1 - \rho)} = \frac{L_q}{\lambda}$$
7. **Conservation Laws (Little's Law):**
   $$L = \lambda W_s \quad \text{and} \quad L_q = \lambda W_q$$
   $$W_s = W_q + \frac{1}{\mu}$$

### C. Classical $M/M/c$ Multi-Server Model
For systems with $c$ identical parallel servers:

1. **Traffic Intensity:**
   $$\rho = \frac{\lambda}{c \mu} \quad (\rho < 1)$$
2. **Idle Probability ($P_0$):**
   $$P_0 = \left[ \sum_{n=0}^{c-1} \frac{(\lambda / \mu)^n}{n!} + \frac{(\lambda / \mu)^c}{c! (1 - \rho)} \right]^{-1}$$
3. **Erlang's C Formula (Probability an arrival must wait):**
   $$C(c, \lambda/\mu) = \frac{\frac{(\lambda / \mu)^c}{c!(1 - \rho)}}{\sum_{k=0}^{c-1}\frac{(\lambda / \mu)^k}{k!} + \frac{(\lambda / \mu)^c}{c!(1 - \rho)}}$$
4. **Expected Queue Length ($L_q$):**
   $$L_q = C(c, \lambda/\mu) \cdot \frac{\rho}{1 - \rho}$$
5. **Expected Waiting Time in Queue ($W_q$):**
   $$W_q = \frac{L_q}{\lambda} = \frac{C(c, \lambda/\mu)}{c\mu - \lambda}$$

---

## 5. Average Service Time (AST) Method

Used extensively in commercial queue management systems (e.g., banking kiosks):
1. Compute the rolling historical average service duration for each service category $m$:
   $$\overline{S}_m = \frac{1}{|D_m|} \sum_{i \in D_m} S_i$$
2. For an arrival facing $K$ individuals ahead in line:
   $$\widehat{W}_{\text{AST}} = \sum_{k=1}^{K} \overline{S}_{\text{type}(k)}$$
If multi-server routing applies, distribute across $c$ servers:
$$\widehat{W}_{\text{AST-Multi}} = \frac{1}{c} \sum_{k=1}^{K} \overline{S}_{\text{type}(k)}$$

---

## 6. Classical Statistical & Linear Baselines

- **Ordinary Least Squares (OLS) / Ridge Regression:**
  $$W_q = \beta_0 + \beta_1 L_q + \beta_2 c_{\text{active}} + \beta_3 \text{Hour} + \epsilon$$
- **Q-Lasso:** Regularized linear regression incorporating the fluid queueing ratio $\frac{\text{Workload}}{\text{Capacity}}$ as a physical covariate.
- **$k$-Nearest Neighbors ($k$-NN):** Averages realized delays of the $k$ historically most similar queue states (matching queue length, hour, and day).
- **ARIMA / Seasonal ARIMA:** Benchmarking periodic aggregate arrival counts and system-level waiting patterns.
- **Discrete Event Simulation (DES):** Using Python libraries like `Ciw` or `SimPy` to simulate stochastic arrivals and server processing under specific priority and routing rules.

---

## 7. Comparative Baseline Summary

| Baseline Model | Input Requirements | Complexity | Advantages | Disadvantages |
|---|---|---|---|---|
| **Historical Mean** | Historical $W_q$ | Minimal | Zero real-time data needed | High error during rush hours |
| **Rolling 4-Hour** | Recent $W_q$ log | Low | Adapts to daily trend | Lags behind rapid shifts |
| **LES** | Last served $W_q$ | Minimal | Real-time ground truth | No queue-depth awareness |
| **AST Formula** | Queue ahead + Category | Low | Transparent, industry standard | Ignores server breaks/reneging |
| **QL Estimator** | Queue depth $n$, servers $s$, $\mu$ | Low | Grounded in queueing theory | Assumes exponential service |
| **$M/M/c$ Queue** | $\lambda, \mu, c$ | Medium | Mathematical equilibrium | Fails under transient bursts |
| **Linear / Lasso** | Snapshot tabular vector | Low-Medium | Fast, interpretable | Misses non-linear bottlenecks |
