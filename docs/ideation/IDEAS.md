# Improvement Ideas: Adaptive Calmar Shield v2

**Session:** d4a6e807 · **Date:** 2026-06-10
**Goal:** 39 raw ideas → 10 survivors after cross-referencing vs 8 competitor forks
**Scoring:** Composite = 0.50×CalmarImpact + 0.25×Novelty + 0.15×Feasibility + 0.10×Robustness

---

## Tier 1: Highest Confidence (Composite ≥ 3.75)

### 1. Panic State Gate — SPY 126d return < -10% AND 20d RVOL > 1.5 → 60% min cash
**Score: 4.4 · Novelty: None do this**

Catches prolonged bear regimes with two uncorrelated triggers (trend duration + vol expansion). Forces 60% cash, protecting capital during the worst drawdown periods. Unlike our current DD governor which reacts to portfolio damage *after* it happens, this detects the macro conditions that cause damage *before* the full drawdown materializes. Almost impossible to overfit — the dual condition requires both a sustained downtrend AND elevated fear.

### 2. Permanent TLT Tail Hedge — 8-12% TLT always held, never traded out
**Score: 3.9 · Novelty: None do this**

Reinsurance analogy: pay a small premium (TLT's mild drag in rallies) to cap crash losses. TLT rallies during flight-to-safety, offsetting equity losses. Having it always-on removes timing risk entirely (no "should I enter the hedge now?" decisions). Unlike our current regime-dependent defensive book, this ensures the hedge is in place before any crash starts.

### 3. Regime-Conditional Universe — Different ticker sets per vol regime
**Score: 3.75 · Novelty: None do this**

Three universes: low vol (<14% QQQ) → high-beta names + 2x ETFs; mid vol → core equities; high vol (>25%) → defensives + cash. Removes drawdown-prone names *at source* rather than reacting after damage. The two-universe approach is unique — competitors run the same universe through all states.

---

## Tier 2: Strong Confidence (Composite ≥ 3.55)

### 4. VIX Spike Circuit Breaker — VIX > 28 → cut gross exposure to ≤ 0.5×
**Score: 3.65 · Novelty: Only Zaid mentions VIX**

Flips the TLT tail hedge logic: instead of hedging, just reduce size. VIX > 28 is a well-known "this is not normal" threshold. Cuts gross exposure by half, eliminating the need to pick hedges. Complements the panic state gate with a different trigger (implied vol vs. trailing vol + return).

### 5. Correlation Sector Cap — any sector cluster max 25% of portfolio
**Score: 3.6 · Novelty: Only Dalal does correlation work**

Prevents hidden concentration in correlated names (e.g., SMH + NVDA + AVGO = 60% semis). If semis correct -20% with 60% allocation, that's -12% portfolio drawdown. With 25% cap, it's -5%. Maps tickers to sectors via hardcoded dict, sums exposure per cluster at rebalance, scales down proportionally.

### 6. Position-Level Vol Targeting — each name sized to equal vol contribution
**Score: 3.6 · Novelty: None do this (all use portfolio-level only)**

Instead of inverse-vol weighting (which mixes position-level and portfolio-level vol), each position is independently sized to a fixed vol contribution (e.g., 3% annualized vol per position). High-vol names auto-shrink; low-vol names grow. Naturally diversifies risk contribution. No covariance math needed.

### 7. Invert Regime Asymmetry — 1 tick to enter FULL_RISK, 2 ticks to leave
**Score: 3.55 · Novelty: Everyone uses slow-in/fast-out**

Current "2 ticks in, 1 out" is defensive-first. Flipping to "1 in, 2 out" makes the agent quicker to capture V-bounces (less time in TLT during recovery) while being more skeptical of false exits. Better for 60-day Calmar where recovery days are precious.

### 8. Consecutive-Win Risk Reduction — -15% after 5 green days, -25% after 8
**Score: 3.55 · Novelty: None do this**

Behavioral edge: reduces risk exactly when overconfidence grows. Winning streaks in trend-following are followed by sharp reversions. This mechanically trims into strength, locking in gains. The missed upside from trimming is smaller than the drawdown avoided. Counter-cyclical by design.

### 9. Hard Drawdown Cap at 8% — force 25/75 equity/defensive immediately
**Score: 3.55 · Novelty: None have ratchet mechanism**

Last-resort insurance. In a 60-day window, -8% DD already means the competition is likely lost — this prevents catastrophic further damage. Ratchet mechanism: once triggered, stay defensive until recovering to +2%, then re-enter gradually. Creates a hard floor on the Calmar denominator.

---

## Tier 3: Worth Considering (Composite ≥ 3.4)

### 10. QQQ 1d/3d Sudden-Drop Brake — -3%/-5% thresholds, 3-bar lockout
**Score: 3.4 · Novelty: Only San245o/balaji have fast crash detection**

Captures tech-specific flash crashes before SPY circuit breaker triggers. QQQ dropped -5% on Aug 5, 2024 — SPY same day but lagged. Two timeframes (1d and 3d) cover both sudden crashes and multi-day bleeds. Unlocks only after QQQ recovers 50% of the drop.

---

## Killed Ideas Summary

| Reason | Count | Examples |
|--------|-------|---------|
| Calmar impact ≤ 2 | 12 | Config registry, event-driven rebalance, SHY cash replacement |
| Composite < 3.0 | 3 | Per-position ATR stop, mean reversion, remove SPY |
| Outperformed by survivor | 14 | Cash-only defense (TLT hedge better), tighten DD governor (hard cap better), QLD/SSO overlay (VIX breaker better) |
