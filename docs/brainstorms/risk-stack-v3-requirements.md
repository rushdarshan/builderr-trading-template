# Risk Stack v3 — Final (SUBMITTED)

**Date:** 2026-06-10 · **Revision:** 1 of 4 spent (Round 1)
**Shipped:** Panic state gate (A) + Hard 8% DD cap (I) + HALF_RISK regime cap
**Status:** Submitted to submit@builderr.ai · all admission gates PASS

## Final preview metrics (submitted build)

| Window | Ret | MaxDD | Calmar | Trades |
|---|---|---|---|---|
| calm_uptrend | 8.26% | 1.86% | 19.71 | 48 |
| moderate_selloff | -5.26% | 6.24% | -5.70 | 33 |
| vol_spike_snapback | -4.20% | 6.49% | -2.72 | 14 |

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
- `_score`: **plain 60d momentum** (the 4-factor composite — m60/m20/trend-gap/RS,
  vol-normalized — was dropped during reconciliation; simpler survived testing)
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

## Deferred (candidates for revisions 2–4, one falsifiable change each)

- E — Correlation sector cap: if live leaderboard shows crowding losses
- J — QQQ 1d/3d sudden-drop brake: if circuit breaker proves too slow live
- C/F — Universe/sizing refinements: only with evidence
