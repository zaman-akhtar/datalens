# ADR-002: Charting Library — Recharts

- **Status:** Accepted
- **Date:** 2026-05-04
- **Deciders:** Zaman + project partner
- **Supersedes:** —

---

## Context

The dashboard renders 4–6 visualizations chosen by the chart-picker. Filters propagate to all charts and must update them within 500 ms. The course rubric explicitly allows **Recharts** or **Plotly** and discourages others. We need:

- Five chart types: bar, line, histogram, scatter, KPI tile.
- Re-renders cheap enough to fit the 500 ms global-filter budget across 6 simultaneous charts.
- Easy to test with Vitest + React Testing Library (no canvas/WebGL surprises).
- Bundle size that doesn't make `npm run build` painful.

## Options considered

| Option | Bundle | Render style | Test ergonomics | Built-in interactivity |
|---|---|---|---|---|
| **Recharts** | ~95 KB gzipped | SVG (React-native) | Excellent — components are real React | Tooltip, legend, basic zoom |
| Plotly.js (react-plotly) | ~3 MB | Custom canvas + WebGL | Awkward — requires `--canvas` mocks | Zoom, pan, hover-on-trace, lasso-select |
| Chart.js (react-chartjs-2) | ~150 KB | Canvas | OK | Tooltip, legend |
| visx | ~50 KB (per chart) | SVG | Excellent but lower-level | DIY |

## Decision

**Recharts 2.12**.

- It is React-native: charts are real components, props are real props, refs work, snapshot tests are trivial. This is worth a lot for a small team writing Vitest tests.
- Bundle size (~95 KB) is 30× smaller than Plotly. The dashboard ships in one Vite chunk and stays under 250 KB total.
- All five chart types are first-class: `<BarChart>`, `<LineChart>`, `<Histogram>` (via `<BarChart>` of binned data), `<ScatterChart>`, custom `<KPI>` div.
- Ananya's persona (a fraud analyst triaging in 5 minutes) does not need Plotly's lasso-select or 3-D plots.

## Trade-offs

- **Less interactive out of box than Plotly.** Mitigated: tooltips and legend are enough for the persona; zoom/pan are not in SPEC §8.
- **Worse on > 50,000 data points per chart.** Mitigated: every chart query is server-aggregated to ≤ 5,000 rows (`limit` cap in query engine). Scatter samples to 5,000.
- **Less geographic chart support.** The credit-card dataset has lat/long but the chart-picker treats them as numerics, not maps. Maps are out of MVP per SPEC §9.

## Consequences

- Add `recharts` to `frontend/package.json`.
- All chart components live under `frontend/src/components/chart/` and accept the same `{spec, data}` props.
- The histogram is implemented as a `<BarChart>` of pre-binned data; binning happens server-side in the query engine when `chart_type == "histogram"`.
- Vitest configures `jsdom` (default) — no canvas mocking needed.

## Revisit conditions

- If a future dataset requires a geographic chart in MVP scope → consider adding `react-simple-maps` (still smaller than Plotly).
- If a chart needs to render > 5,000 points client-side → revisit Plotly's WebGL traces.
