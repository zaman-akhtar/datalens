import { describe, it, expect, beforeEach } from "vitest";
import { useFilters } from "@/hooks/useFilters";

describe("useFilters", () => {
  beforeEach(() => useFilters.getState().clear());

  it("sets a filter", () => {
    useFilters.getState().setFilter("state", "NY");
    expect(useFilters.getState().filters).toEqual({ state: "NY" });
  });

  it("removes a filter when value is null", () => {
    useFilters.getState().setFilter("state", "NY");
    useFilters.getState().setFilter("state", null);
    expect(useFilters.getState().filters).toEqual({});
  });

  it("clears all filters", () => {
    useFilters.getState().setFilter("a", "1");
    useFilters.getState().setFilter("b", "2");
    useFilters.getState().clear();
    expect(useFilters.getState().filters).toEqual({});
  });
});
