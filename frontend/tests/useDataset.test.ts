import { describe, it, expect, beforeEach } from "vitest";
import { useDataset } from "@/hooks/useDataset";

describe("useDataset persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    useDataset.getState().clear();
  });

  it("stores datasetId and filename", () => {
    useDataset.getState().set("ds-001", "sales.csv");
    expect(useDataset.getState().datasetId).toBe("ds-001");
    expect(useDataset.getState().filename).toBe("sales.csv");
  });

  it("persists to localStorage on set", () => {
    useDataset.getState().set("ds-abc", "data.csv");
    const raw = localStorage.getItem("datalens-dataset");
    expect(raw).not.toBeNull();
    const stored = JSON.parse(raw!);
    expect(stored.state.datasetId).toBe("ds-abc");
    expect(stored.state.filename).toBe("data.csv");
  });

  it("restores datasetId and filename from localStorage on rehydrate", () => {
    localStorage.setItem(
      "datalens-dataset",
      JSON.stringify({ state: { datasetId: "ds-xyz", filename: "restored.csv" }, version: 0 })
    );
    useDataset.persist.rehydrate();
    expect(useDataset.getState().datasetId).toBe("ds-xyz");
    expect(useDataset.getState().filename).toBe("restored.csv");
  });

  it("clears in-memory state and persists null on clear", () => {
    useDataset.getState().set("ds-001", "test.csv");
    useDataset.getState().clear();
    expect(useDataset.getState().datasetId).toBeNull();
    expect(useDataset.getState().filename).toBeNull();
    const stored = JSON.parse(localStorage.getItem("datalens-dataset") || "{}");
    expect(stored.state?.datasetId ?? null).toBeNull();
  });
});
