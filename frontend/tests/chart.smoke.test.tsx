import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { BarView } from "@/components/chart/Bar";
import { LineView } from "@/components/chart/Line";
import { HistogramView } from "@/components/chart/Histogram";
import { ScatterView } from "@/components/chart/Scatter";
import { KpiView } from "@/components/chart/Kpi";

const data = [
  { label: "a", value: 10 },
  { label: "b", value: 7 },
  { label: "c", value: 3 },
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
});
