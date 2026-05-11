import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProfileCard } from "@/components/ProfileCard";
import type { DatasetProfile } from "@/lib/types";

const profile: DatasetProfile = {
  dataset_id: "x",
  original_filename: "demo.csv",
  n_rows: 100,
  n_cols: 3,
  created_at: "2026-05-04T00:00:00",
  columns: [
    { name: "name", safe_name: "name", dtype: "categorical", null_pct: 0, n_unique: 5, sample_values: ["a"], is_index: false, min: null, max: null, mean: null, skew: null },
    { name: "score", safe_name: "score", dtype: "numeric", null_pct: 0, n_unique: 50, sample_values: [1], is_index: false, min: 0, max: 9, mean: 4.5, skew: 0.1 },
    { name: "Unnamed: 0", safe_name: "unnamed_0", dtype: "numeric", null_pct: 0, n_unique: 100, sample_values: [0], is_index: true, min: 0, max: 99, mean: 49.5, skew: 0 },
  ],
};

describe("ProfileCard", () => {
  it("renders visible columns", () => {
    render(<ProfileCard profile={profile} />);
    expect(screen.getByText("name")).toBeInTheDocument();
    expect(screen.getByText("score")).toBeInTheDocument();
  });
  it("hides flagged-index columns", () => {
    render(<ProfileCard profile={profile} />);
    expect(screen.queryByText("Unnamed: 0")).toBeNull();
  });
});
