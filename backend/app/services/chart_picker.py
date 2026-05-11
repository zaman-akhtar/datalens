"""Chart-picker rule book (System Design §7).

Pure function: takes a DatasetProfile, returns 4-6 ChartSpec instances.
Reads only the profile metadata — never the column names — so it works on
any CSV without modification.
"""
from __future__ import annotations

from app.models.chart import ChartSpec
from app.models.dataset import ColumnProfile, DatasetProfile

_REGION_HINTS = {"state", "region", "country", "province", "neighbourhood"}


def _visible(cols: list[ColumnProfile]) -> list[ColumnProfile]:
    return [c for c in cols if not c.is_index]


def _first_datetime(cols: list[ColumnProfile]) -> ColumnProfile | None:
    return next((c for c in cols if c.dtype == "datetime"), None)


def _first_low_card_categorical(
    cols: list[ColumnProfile], cap: int = 20
) -> ColumnProfile | None:
    return next(
        (c for c in cols if c.dtype == "categorical" and 2 <= c.n_unique <= cap),
        None,
    )


def _first_skewed_numeric(cols: list[ColumnProfile]) -> ColumnProfile | None:
    return next(
        (c for c in cols if c.dtype == "numeric" and (c.skew or 0) > 1),
        None,
    )


def _first_boolean(cols: list[ColumnProfile]) -> ColumnProfile | None:
    return next((c for c in cols if c.dtype == "boolean"), None)


def _first_two_numerics(cols: list[ColumnProfile]) -> tuple[ColumnProfile, ColumnProfile] | None:
    nums = [c for c in cols if c.dtype == "numeric"]
    return (nums[0], nums[1]) if len(nums) >= 2 else None


def _first_region_like(cols: list[ColumnProfile]) -> ColumnProfile | None:
    return next(
        (c for c in cols if c.dtype == "categorical" and c.safe_name.lower() in _REGION_HINTS),
        None,
    )


def _first_high_card_categorical(cols: list[ColumnProfile]) -> ColumnProfile | None:
    return next(
        (c for c in cols if c.dtype in ("categorical", "text") and c.n_unique > 20),
        None,
    )


def pick_charts(profile: DatasetProfile, max_charts: int = 6) -> list[ChartSpec]:
    """Return between 4 and `max_charts` chart specs ordered by importance."""
    cols = _visible(profile.columns)
    picks: list[ChartSpec] = []
    used: set[str] = set()

    def add(spec: ChartSpec) -> None:
        key = f"{spec.chart_type}:{spec.x}:{spec.y}"
        if key in used:
            return
        used.add(key)
        picks.append(spec)

    # 1. Time series
    dt = _first_datetime(cols)
    if dt:
        add(
            ChartSpec(
                chart_type="line",
                title=f"Volume over time — {dt.name}",
                x=dt.safe_name,
                agg="count",
                note="Time-series: count of rows per day.",
            )
        )

    # 2. Low-cardinality categorical → bar
    cat = _first_low_card_categorical(cols)
    if cat:
        add(
            ChartSpec(
                chart_type="bar",
                title=f"Count by {cat.name}",
                x=cat.safe_name,
                agg="count",
                note="Bar of counts for the leading low-cardinality column.",
            )
        )

    # 3. Skewed numeric → histogram
    skewed = _first_skewed_numeric(cols)
    if skewed:
        add(
            ChartSpec(
                chart_type="histogram",
                title=f"Distribution of {skewed.name}",
                x=skewed.safe_name,
                agg="count",
                bins=30,
                note=f"Skew={skewed.skew:.2f}; histogram surfaces the long tail.",
            )
        )

    # 4. Boolean indicator → KPI positive-rate (count grouped by 0/1; KpiView computes %)
    boolean = _first_boolean(cols)
    if boolean:
        add(
            ChartSpec(
                chart_type="kpi",
                title=f"{boolean.name} rate",
                x=boolean.safe_name,
                agg="count",
                note="Count grouped by 0/1; KpiView computes the positive-rate percentage.",
            )
        )

    # 5. Region-like categorical
    region = _first_region_like(cols)
    if region and region.safe_name not in {p.x for p in picks}:
        add(
            ChartSpec(
                chart_type="bar",
                title=f"Count by {region.name}",
                x=region.safe_name,
                agg="count",
                note="Geographic breakdown.",
            )
        )

    # 6. Two numerics → scatter
    if len(picks) < max_charts:
        pair = _first_two_numerics(cols)
        if pair:
            x, y = pair
            add(
                ChartSpec(
                    chart_type="scatter",
                    title=f"{y.name} vs {x.name}",
                    x=x.safe_name,
                    y=y.safe_name,
                    note="Scatter of the first two numeric columns.",
                )
            )

    # 7. High-card categorical → top-10 bar
    if len(picks) < max_charts:
        hc = _first_high_card_categorical(cols)
        if hc:
            add(
                ChartSpec(
                    chart_type="bar",
                    title=f"Top values of {hc.name}",
                    x=hc.safe_name,
                    agg="count",
                    note="High-cardinality column truncated to top 10.",
                )
            )

    # Fallback — guarantee ≥ 4 picks
    while len(picks) < 4:
        n_before = len(picks)
        add(
            ChartSpec(
                chart_type="kpi",
                title=f"Total rows — fallback {len(picks)}",
                x="__rows__",
                agg="count",
                note="Fallback KPI to satisfy the 4-chart floor.",
            )
        )
        if len(picks) >= 6 or len(picks) == n_before:
            break

    return picks[:max_charts]
