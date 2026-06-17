"""Adaptive Calmar Shield rev 5 — concentrated momentum + QQQ gate.

Copies sumegh's approach: QQQ < SMA100 -> cash, top N momentum, concentrated.
Improves: inverse-vol weighting (instead of equal weight), skip 5 momentum.
Goal: beat sumegh on Calmar by same return but lower drawdown.
"""
from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev

# ── Concentrated universe ─────────────────────────────────────────────

_UNIVERSE = (
    "NVDA", "AMD", "MU", "MRVL", "AVGO", "SMH",
    "AAPL", "MSFT", "META", "GOOGL", "AMZN",
    "QQQ", "SPY",
)

# ── Parameters ────────────────────────────────────────────────────────

MOM_WINDOW = 60
MOM_SKIP = 5
SMA_STOCK = 50
SMA_MARKET = 100
TOP_N = 5
NAME_CAP = 0.25
MIN_TRADE_PCT = 0.02
DEAD_BAND = 0.03
REBALANCE_EVERY = 5

VOL_WIN = 20

# ── State ─────────────────────────────────────────────────────────────

_last_date: str | None = None

# ── Helpers ───────────────────────────────────────────────────────────

def _closes(series):
    if not series:
        return []
    return [float(d["close"]) for d in series]

def _sma(prices, n):
    if len(prices) < n:
        return None
    return mean(prices[-n:])

def _mom(prices, n, skip=0):
    if len(prices) < n + skip + 1:
        return None
    return prices[-(skip + 1)] / prices[-(n + skip + 1)] - 1

def _rvol(prices, n):
    if len(prices) < n + 1:
        return None
    rets = [prices[i] / prices[i-1] - 1 for i in range(-n, 0)]
    if len(rets) < 5:
        return None
    return pstdev(rets) * sqrt(252)

def _bar_date(ms):
    for anchor in ("QQQ", "SPY"):
        bars = ms.get(anchor) or []
        if bars:
            ts = bars[-1].get("ts")
            return str(ts)[:10] if ts is not None else str(len(bars))
    return None

def _equity(ps, cash):
    eq = float(ps.get("cash", cash))
    lp = ps.get("last_prices") or {}
    for raw in ps.get("positions") or []:
        t = str(raw.get("ticker", "")).upper()
        q = float(raw.get("quantity", 0))
        p = float(lp.get(t, 0))
        if t and q > 0 and p > 0:
            eq += q * p
    return max(eq, 0)

def _positions(ps):
    out = {}
    for raw in ps.get("positions") or []:
        t = str(raw.get("ticker", "")).upper()
        q = float(raw.get("quantity", 0))
        if t and q > 0:
            out[t] = out.get(t, 0) + q
    return out

def _prices(ms):
    return {
        t.upper(): float(bars[-1]["close"])
        for t, bars in ms.items()
        if bars and bars[-1].get("close", 0) > 0
    }

# ── Core logic ────────────────────────────────────────────────────────

def decide(market_state, portfolio_state, cash):
    global _last_date

    if not market_state:
        return []

    today = _bar_date(market_state)
    if today is None:
        return []

    # Day 1 lock
    if _last_date is None:
        _last_date = today
        return []

    eq = _equity(portfolio_state, cash)
    if eq <= 0:
        return []

    px = _prices(market_state)
    pos = _positions(portfolio_state)

    # ── MACRO GATE: QQQ below SMA100 → cash ──────────────────────────
    qqq = _closes(market_state.get("QQQ"))
    if len(qqq) < SMA_MARKET:
        return []

    qqq_sma = _sma(qqq, SMA_MARKET)
    if qqq_sma is None or qqq[-1] < qqq_sma:
        # Liquidate
        orders = [
            {"ticker": t, "side": "sell", "quantity": int(q)}
            for t, q in pos.items()
            if px.get(t, 0) > 0 and int(q) > 0
        ]
        _last_date = today
        return orders[:45]

    # ── MOMENTUM RANKING ──────────────────────────────────────────────
    scored = []
    for t in _UNIVERSE:
        cs = _closes(market_state.get(t))
        if len(cs) < max(MOM_WINDOW + MOM_SKIP, SMA_STOCK) + 1:
            continue
        sma50 = _sma(cs, SMA_STOCK)
        mom = _mom(cs, MOM_WINDOW, MOM_SKIP)
        if sma50 is None or mom is None:
            continue
        if cs[-1] <= sma50 or mom <= 0:
            continue
        scored.append((mom, t))

    scored.sort(reverse=True)
    winners = [t for _, t in scored[:TOP_N]]
    if not winners:
        return []

    # ── Inverse-vol weighting ─────────────────────────────────────────
    inv = {}
    for t in winners:
        cs = _closes(market_state.get(t))
        v = _rvol(cs, VOL_WIN) if cs else None
        inv[t] = 1.0 / max(float(v or 0.20), 0.05)
    total_inv = sum(inv.values()) or 1
    targets = {t: min(NAME_CAP, iv / total_inv * 0.95) for t, iv in inv.items()}

    total = sum(targets.values())
    if total > 0.95:
        targets = {t: w * 0.95 / total for t, w in targets.items()}

    # ── Rebalance check ───────────────────────────────────────────────
    from datetime import datetime
    days = None
    if _last_date and today:
        try:
            d1 = datetime.strptime(_last_date, "%Y-%m-%d")
            d2 = datetime.strptime(today, "%Y-%m-%d")
            days = (d2 - d1).days
        except Exception:
            pass

    if days is not None and days < REBALANCE_EVERY:
        return []

    # ── Orders ────────────────────────────────────────────────────────
    min_v = eq * MIN_TRADE_PCT
    orders = []
    proceeds = 0.0

    for t, q in pos.items():
        price = px.get(t)
        if not price or price <= 0:
            continue
        cur_v = q * price
        tgt_v = eq * targets.get(t, 0)
        if t not in targets:
            s = int(q)
            if s > 0 and cur_v >= min_v:
                orders.append({"ticker": t, "side": "sell", "quantity": s})
                proceeds += s * price
        elif cur_v - tgt_v > min_v:
            s = min(int(abs(cur_v - tgt_v) / price), int(q))
            if s > 0:
                orders.append({"ticker": t, "side": "sell", "quantity": s})
                proceeds += s * price

    spendable = max(float(cash), 0) + proceeds * 0.98

    for t, w in sorted(targets.items(), key=lambda x: -x[1]):
        price = px.get(t)
        if not price or price <= 0:
            continue
        cur = pos.get(t, 0)
        cur_v = cur * price
        tgt_v = eq * w
        delta = tgt_v - cur_v
        if delta < min_v:
            continue
        buy_v = min(delta, spendable)
        qty = int(buy_v / price)
        if qty > 0:
            orders.append({"ticker": t, "side": "buy", "quantity": qty})
            spendable -= qty * price

    if orders:
        _last_date = today
    return orders[:45]
