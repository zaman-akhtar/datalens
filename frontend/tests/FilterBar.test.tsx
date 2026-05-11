import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FilterBar } from "@/components/FilterBar";
import { useFilters } from "@/hooks/useFilters";
import type { ColumnProfile } from "@/lib/types";

const cols: ColumnProfile[] = [
  { name: "state", safe_name: "state", dtype: "categorical", null_pct: 0, n_unique: 3, sample_values: ["NY", "CA"], is_index: false, min: null, max: null, mean: null, skew: null },
  { name: "merchant", safe_name: "merchant", dtype: "categorical", null_pct: 0, n_unique: 1000, sample_values: ["m1"], is_index: false, min: null, max: null, mean: null, skew: null },
];

beforeEach(() => useFilters.getState().clear());

describe("FilterBar", () => {
  it("shows only low-cardinality categoricals", () => {
    render(<FilterBar columns={cols} />);
    expect(screen.getByTestId("filter-state")).toBeInTheDocument();
    expect(screen.queryByTestId("filter-merchant")).toBeNull();
  });
  it("updates the filter store", () => {
    render(<FilterBar columns={cols} />);
    fireEvent.change(screen.getByTestId("filter-state"), { target: { value: "NY" } });
    expect(useFilters.getState().filters).toEqual({ state: "NY" });
  });
});
