import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { BarView } from "@/components/chart/Bar";
import { LineView } from "@/components/chart/Line";
import { HistogramView } from "@/components/chart/Histogram";
import { ScatterView } from "@/components/chart/Scatter";
import { KpiView } from "@/components/chart/Kpi";
import { GeoBarView } from "@/components/chart/GeoBar";
import type { GeoRow } from "@/lib/types";

const data = [
  { label: "a", value: 10 },
  { label: "b", value: 7 },
  { label: "c", value: 3 },
];

const geoData: GeoRow[] = [
  { state: "TX", count: 300, fraud_count: 15, fraud_rate: 0.05 },
  { state: "CA", count: 200, fraud_count: 4, fraud_rate: 0.02 },
  { state: "NY", count: 100, fraud_count: 8, fraud_rate: 0.08 },
];

describe("chart smoke", () => {
  it("renders BarView", () => {
    const { getByTestId } = render(<BarView data={data} title="t" />);
    expect(getByTestId("chart-bar")).toBeInTheDocument();
  });
  it("renders LineView", () => {
    const { getByTestId } = render(<LineView data={data} title="t" />);
    expect(getByTestId("chart-line")).toBeInTheDocument();
  });
  it("renders HistogramView", () => {
    const { getByTestId } = render(<HistogramView data={data} title="t" />);
    expect(getByTestId("chart-bar")).toBeInTheDocument();
  });
  it("renders ScatterView", () => {
    const { getByTestId } = render(<ScatterView data={data} title="t" />);
    expect(getByTestId("chart-scatter")).toBeInTheDocument();
  });
  it("renders KpiView", () => {
    const { getByTestId } = render(<KpiView data={[{ label: "rows", value: 1234 }]} title="rows" />);
    expect(getByTestId("chart-kpi")).toBeInTheDocument();
  });
  it("renders GeoBarView", () => {
    const { getByTestId } = render(<GeoBarView data={geoData} title="Geo" />);
    expect(getByTestId("chart-map")).toBeInTheDocument();
  });
});
