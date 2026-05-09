# Decision Intelligence Experimentation Platform

A production-style A/B testing system that goes from raw event data to a
statistically grounded SHIP / DO NOT SHIP / INCONCLUSIVE decision — with
segment-level breakdowns that explain *where* the experiment worked and
where it did not.

---

## Live Demo
**[→ Open Experiment Decision Simulator](https://experiment-decision-simulator.streamlit.app/)**

No setup needed. Simulate an A/B test and turn the result into a rollout decision.

---

## The Problem

Most A/B testing implementations answer one question: is this result
statistically significant?

That is the wrong stopping point.

A p-value of 0.012 on an 8.3% lift sounds clean. But if that lift is
entirely driven by iOS users in the US, and Android users in India are
seeing negative impact, shipping to everyone is the wrong call. The
aggregate number hides the decision that actually matters: *who* do you
ship to, and *when*?

This project builds the layer between statistical output and product
decision — the part most dashboards skip.

---

## System Overview

```
Raw Event Simulation → PostgreSQL → dbt Models → Metrics Layer
→ Statistical Engine → Segment Analysis → Decision Dashboard
```

**50,000 simulated users** assigned to control and treatment groups,
generating **280K+ events** and **3.8K+ orders** across platforms and
regions.

---

## What It Does

### 1. Data Pipeline

- Simulates realistic user behavior — experiment assignment, event
  activity, purchase decisions
- Loads raw events into PostgreSQL for transformation
- Handles control vs. treatment group separation at the ingestion layer

### 2. dbt Analytics Layer

Staging, intermediate, and mart models built to analytics engineering
standards:

- `int_experiment_base` — experiment-level dataset joining users,
  assignments, and events
- Metrics tables: conversion rate, average order value, segment-level
  breakdowns by platform and country

### 3. Statistical Engine

- Z-test for conversion rate comparison between groups
- Calculates lift, p-value, and confidence interval
- Outputs a deterministic decision: **SHIP / DO NOT SHIP / INCONCLUSIVE**
- No manual interpretation — the decision logic is coded, not eyeballed

### 4. Segment Analysis

The part that changes the rollout recommendation:

- Breaks results by platform (iOS, Android) and country (US, India, etc.)
- Identifies where the experiment succeeds and where it fails
- Generates plain-English insight: which segment drives the lift, which
  segment should be excluded from the initial rollout

### 5. Decision Dashboard

Built with Streamlit. Shows experiment metrics, statistical results,
the final decision, and the segment breakdown — in one place, for a
non-technical audience.

---

## Example Output

```
Control CR   : 8.4%
Treatment CR : 9.1%
Lift         : +8.3%
P-value      : 0.012

Decision     : SHIP

Segment insight:
  Strongest lift — iOS users, US (+14.2%)
  Negative impact — Android users, India (-3.1%)
  Recommendation: segment rollout, not full release
```

The aggregate says SHIP. The segment analysis says *who to ship to first*.
That is the decision the dashboard is actually built to support.

---

## Case Study

We simulated a product feature A/B test on 50,000 users.

| Metric | Control | Treatment |
|---|---|---|
| Conversion Rate | 8.4% | 9.1% |
| Lift | — | +8.3% |
| P-value | — | 0.012 |
| Decision | — | SHIP |

**Segment breakdown:**
- iOS / US: strongest positive lift — ship here first
- Android / India: negative impact — investigate before including in rollout

The flat "SHIP" decision misses the second row. This platform surfaces both.

---

## Tech Stack

Python · PostgreSQL · dbt · SQL · Streamlit · Pandas · NumPy · SciPy

---

## Project Structure

```
decision-intelligence-experimentation-platform/
├── data/                 Raw simulation scripts
├── models/               dbt staging, intermediate, mart models
├── src/                  Statistical engine and decision logic
├── dashboard/            Streamlit app
├── outputs/              Example decision reports
└── README.md
```

---

## Connection to My AI Data Governance Platform

Experiments are only trustworthy if the underlying data is trustworthy.
This platform produces the statistical outputs. My
[AI Data Governance Platform](https://github.com/SomeshZanwar/ai-data-governance-platform)
handles the layer underneath — validating that the event data feeding
this system is fresh, reconciled, and free of quality failures before
results are interpreted.

---

## Future Improvements

- CUPED / variance reduction for faster significance detection
- Sample size and power analysis (MDE calculator)
- Experiment registry — track running experiments, prevent overlap
- Real-time streaming pipeline
- Automated alerts when experiments breach guardrail metrics
