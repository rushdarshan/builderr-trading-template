# Risk Stack v4 — Rev 3 (gross scaling + asymmetric confirmation)

**Date:** 2026-06-12 · **Revision:** 3 of 4 spent (Round 1)
**Status:** Ready for submit@builderr.ai · all admission gates PASS
**SHA:** (current working tree, not yet pushed)

## Changes from rev 2

### 1. Gross scaling by DD tiers (replaces regime-switch + dynamic split)

**Before:** Regime switched between HALF_RISK (50/50 momentum/defensive) and DEFENSIVE at 2%/4% DD thresholds. Dynamic split glided momentum budget from 50%→0% within HALF_RISK.

**After:** Portfolio composition is always the same (50/50 momentum/defensive when regime is HALF_RISK). Total gross is scaled proportionally by DD:

| DD | Gross scale | Effective portfolio |
|---|---|---|
| < 1.5% | 1.00× | 50% momentum, 50% defensive |
| 1.5%–2.5% | 0.60× | 30% momentum, 30% defensive |
| 2.5%–4.0% | 0.30× | 15% momentum, 15% defensive |
| ≥ 4.0% | 0.10× | 5% momentum, 5% defensive |

**Rationale:** Matches balaji (#1) and sankeerth (#3) approach. All top competitors scale gross by DD rather than switching portfolio composition. Our old regime-switch model created a cliff at 4% DD where the entire portfolio composition changed; gross scaling is smoother and avoids forced regime-flip trades.

### 2. Asymmetric regime confirmation

**Before:** Regime flipped on every tick. One day of score ≥ 3 → HALF_RISK. Next day of score < 3 → DEFENSIVE.

**After:** 2 consecutive ticks required to enter HALF_RISK, 1 tick to exit to DEFENSIVE.

**Rationale:** Matches balaji (2 in, 1 out) and sankeerth (2 in, 1 out). Prevents whipsaw on marginal signal days. Directly reduces unnecessary regime-flip trades.

**Module state added:** `_pending_regime: str | None`, `_pending_regime_count: int`

### 3. Name cap tightened (24% → 15%)

**Before:** `MAX_W = 0.24` — single position could reach 24% of portfolio.

**After:** `MAX_W = 0.15` — matches balaji (13%) and sankeerth (12%).

**Rationale:** Reduces single-name blowup risk. With 24% cap + 27% drift limit, a winning position could grow to 27% before forced rebalance. At 15% cap + 35% drift, positions are naturally smaller and drift only triggers as an emergency override.

### 4. Momentum skip last 5 bars

**Before:** `_mom(prices, window)` used `prices[-1] / prices[-window]`.

**After:** `_mom(prices, window, skip=5)` uses `prices[-6] / prices[-(window+5)]` — skips the most recent 5 bars.

**Rationale:** Matches balaji (`MOMENTUM_SKIP = 5`) and sankeerth. Avoids week-ending noise in momentum calculation. One-parameter change with near-zero downside.

## Parameters changed

| Parameter | Old | New |
|---|---|---|
| `MAX_W` | 0.24 | 0.15 |
| `DRIFT_LIMIT` | 0.27 | 0.35 |
| `DD_HALF`, `DD_FULL` | 0.02, 0.04 | *removed* |
| `DD_TIER_1/2/3` | — | 0.015, 0.025, 0.04 |
| `MOM_SKIP` | — | 5 |

## Preview metrics

| Window | Ret | MaxDD | Calmar | Trades |
|---|---|---|---|---|
| calm_uptrend | 8.41% | 1.40% | 26.71 | 35 |
| moderate_selloff | −3.94% | 4.49% | −6.21 | 25 |
| vol_spike_snapback | −2.34% | 3.26% | −3.45 | 15 |

### Deltas vs rev 2

| Window | Ret Δ | DD Δ | Calmar Δ |
|---|---|---|---|
| calm_uptrend | +0.13pp | −0.45pp | +6.79 |
| moderate_selloff | +0.35pp | −0.80pp | −0.55 |
| vol_spike_snapback | +1.71pp | −3.23pp | −0.55 |

Return and max drawdown improved in **every window**. The −0.55 Calmar regression in selloff/vol_spike is a formula artifact (identical Δ in both windows, ret and DD both improved).

### Local competitive rank

**Overall: #6/19** (up from #9/19 in rev 2)
- calm_uptrend: #4/20 (up from ~#9)
- moderate_selloff: #20/20 (unchanged)
- vol_spike_snapback: #16/19 (slightly improved)

## Safety bar (all PASS)
- [PASS] runs clean, no errors
- [PASS] no leverage breach (peak gross 0.95× ≤ 1.5×)
- [PASS] no concentration breach (peak 15%)
- [PASS] no blow-up (worst drawdown 4.5% < 50%)

## Test suite
- ✓ strategy_selftest.py — 7/7 checks passed
- ✓ test_compare.py --check — no regressions against baseline
- ✓ selfcheck.py — 9 well-formed orders, 12 clean steps

## Deferred (candidates for rev 4, one per change)

- Correlation sector cap (ticker→sector dict, cap at 30% per cluster)
- Exit-only momentum filter (sell positions with negative 5d return in bottom half)
- Adaptive rebalance (vol-triggered, not calendar)
- Hard brake (QQQ 1d −2%, 3d −4%, 10d vol > 40%) — tested locally, zero impact on sample windows
- DRIFT_LIMIT reduction back to 0.20 if trade count is too low
