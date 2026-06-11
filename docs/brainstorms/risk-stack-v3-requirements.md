# Risk Stack v3 — Final (SUBMITTED)

**Date:** 2026-06-11 · **Revision:** 2 of 4 spent (Round 1)
**Shipped:** v1: Panic state gate (A) + Hard 8% DD cap (I) + HALF_RISK regime cap
            v2: Dynamic HALF_RISK split + HARD_CAP ordering fix
**Status:** Submitted to submit@builderr.ai · all admission gates PASS for rev 2
**SHA:** `7fce699` (pushed main Jun 11)

## Final preview metrics (submitted build)

| Window | Ret | MaxDD | Calmar | Trades |
|---|---|---|---|---|
| calm_uptrend | 8.26% | 1.86% | 19.71 | 48 |
| moderate_selloff | -5.26% | 6.24% | -5.70 | 33 |
| vol_spike_snapback | -4.05% | 6.49% | -2.90 | 14 |

## Regime finding (do not "fix" without re-testing)

**Maximum risk-on state is HALF_RISK (50/50 momentum/defensive) by design.**
FULL_RISK empirically loses on Calmar even in bull windows:

| Posture | calm Calmar | vol_spike DD |
|---|---|---|
| Full risk-on (rejected) | 13.78 | 8.67% |
| 50/50 HALF_RISK (shipped) | 16.52–19.71 | 6.49–7.16% |

v2's apparent 18.4 came from a path-dependent frozen-regime bug (the 2-tick
asymmetry counter could never arm, so strong-signal days froze the regime).
Removed as untestable; replaced with explicit `score >= 3 → HALF_RISK`.
The FULL_RISK branch was deleted from `_targets()` — any revision
reintroducing it must re-run the comparison above first.

## Helper semantics (v3 baseline — changing these changes live behavior)

- `_rvol`: **simple returns** (not log returns)
- `_days_since`: **calendar days** (REBALANCE_EVERY=7 ≈ 5 trading days →
  more rebalances than bar-indexed counting; this drove the calm-window gain)
- `_score`: **4-factor composite** (`0.50 × m60 + 0.25 × m20 + 0.15 × tg + 0.10 × rs`) vol-normalized.
  Not plain 60d — the composite shipped with v3 and was never changed.
- `_cap`: enforces per-name 24% AND beta-gross ≤ 1.32 (DQ buffer under 1.5×)
- Module state: `_peak_equity` (DD governor + hard cap), `_cb_remaining/_cb_date`
  (circuit breaker), `_last_date/_last_regime` (cadence). Panic gate is stateless.

## Tested and rejected (do not re-litigate)

| Feature | calm Calmar Δ | vol_spike DD Δ | Verdict |
|---|---|---|---|
| B — Permanent 8% TLT hedge | 18.40 → 13.34 | 7.8% → 8.54% | Daily drag; TLT correlated with selloff instead of hedging |
| G — Inverted asymmetry (1-in/2-out) | 18.40 → 13.67 | 7.8% → 8.67% | DD widened on its own home-turf V-bounce scenario |
| D — VIX breaker | — | — | Infeasible: VIX not in market_state |
| FULL_RISK regime | 19.71 → 13.78 | worse | See regime finding |
| CB −2.0% tighten | 19.92 → 19.92 | −2.90 → −2.90 | Zero effect on any window; locally undeterminable. Kept at −2.5% (no change from baseline). |

## Revision 2 (2026-06-11, submitted)

### Changes
1. **Dynamic HALF_RISK split** — momentum budget = `0.50 * max(0, 1 - dd/(2 × DD_HALF))`. Glides from 50/50 at 0% DD to 25/75 at 2% DD to 0/100 at 4% DD (converging with DD_FULL governor). Single-line change to `_targets()`.
2. **HARD_CAP ordering fix** — moved before vol-scale so cash-out (QQQ vol ≥ 25%) is the final word. Bug existed in v3 but never exercised (vol-scale ran after HARD_CAP, potentially re-entering market at max stress).

**CB unchanged** (stays at −2.5%, the v3 baseline). A tightening to −2.0% was explored and dropped: it has zero observable effect on any preview window and no first-principles justification, which is the same evidence profile that killed B and G.

### Preview deltas vs v3

| Window | v3 Ret/DD/Calmar | Rev2 Ret/DD/Calmar | Δ |
|---|---|---|---|
| calm_uptrend | 8.26% / 1.86% / 19.71 | 8.28% / 1.85% / 19.92 | +0.21 Calmar |
| moderate_selloff | −5.26% / 6.24% / −5.70 | −4.29% / 5.29% / −5.66 | +0.97pp ret, −0.95pp DD |
| vol_spike_snapback | −4.05% / 6.49% / −2.90 | −4.05% / 6.49% / −2.90 | 0 (unchanged) |

### Mechanism note (why each window moved the way it did)
- **vol_spike unchanged** (−2.90): DD breaches DD_FULL (4%) rapidly, forcing DEFENSIVE regime — the new split branch never executes. Correctly irrelevant.
- **selloff improved** (DD 6.24% → 5.29%): DD builds gradually through 1–4%, where HALF_RISK is active and the split trims momentum *before* the DD_FULL governor fires — shallower trough. Continuous convergence to the 4% governor, confirmed.
- **calm tiny improvement** (19.71 → 19.92): DD stays near zero, split barely engages. Marginal win from slightly more efficient convergence.

### Correction note (Jun 2026)
The v3 baseline was previously misreported as having vol_spike Calmar −2.72. The true value is **−2.90** (verified by running `git stash; python preview.py` on commit `7cfe2e0`). The phantom −2.72 was a measurement error. The CB-threshold attribution (that tightening caused a −2.72 → −2.90 regression) was built on this wrong baseline — no regression existed.

### Live watch criteria
- Down days: daily loss should be smaller than dual-momentum-rotation (the house all-weather bot)
- Up days: track within noise of rev 1 behavior
- Trade count: should be similar to rev 1 (~18 trades in first 8 days). If significantly higher, investigate

## Deferred (candidates for revisions 3–4, one falsifiable change each)

- E — Correlation sector cap: if live leaderboard shows crowding losses
- J — QQQ 1d/3d sudden-drop brake: if circuit breaker proves too slow live
- C/F — Universe/sizing refinements: only with evidence

### IMC Prosperity-inspired hypothesis backlog (from competition research)

*All candidates are in the same evidence state CB was: plausible story, zero local data. Bar for rev 3 is a symptom observed live + one candidate tested alone.*

- (a) Reduce momentum count from 4 to 3 (Seven Deuce "simpler is better")
- (b) TLT timing overlay (recession-trend entry, not static)
- (c) Asymmetric vol scaling (scale down faster than up)
- (d) Clean up stale-YAGNI in `_panic()` and `_regime()`
- (e) Circuit breaker as exit-only (drop cooldown to avoid missing snapbacks)
- (f) Trailing-stop DD management (escape hatch on intraday blows)
- (g) QQQ vol as direct regime input (if QQQ rvol > 0.40 → DEFENSIVE)
