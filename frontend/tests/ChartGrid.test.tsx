import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChartGrid } from "@/components/ChartGrid";
import { useDataset } from "@/hooks/useDataset";

vi.mock("@/lib/api", () => ({
  api: {
    chartPicks: vi.fn().mockResolvedValue([]),
    runQuery: vi.fn().mockResolvedValue({ sql: "", n_rows: 0, rows: [] }),
    geo: vi.fn().mockResolvedValue([]),
  },
}));

beforeEach(() => {
  useDataset.getState().clear();
});

describe("ChartGrid", () => {
  it("renders nothing when no dataset is selected", () => {
    const { container } = render(<ChartGrid />);
    expect(container.firstChild).toBeNull();
  });

  it("shows loading skeleton while chart specs are fetching", () => {
    useDataset.getState().set("ds-smoke", "smoke.csv");
    render(<ChartGrid />);
    expect(screen.getByTestId("chart-grid-loading")).toBeInTheDocument();
  });
});
