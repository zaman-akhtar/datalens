import { describe, it, expect, beforeEach } from "vitest";
import { useFilters } from "@/hooks/useFilters";

describe("useFilters", () => {
  beforeEach(() => {
    localStorage.clear();
    useFilters.getState().clear();
  });

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

  it("persists filters to localStorage on setFilter", () => {
    useFilters.getState().setFilter("state", "TX");
    const raw = localStorage.getItem("datalens-filters");
    expect(raw).not.toBeNull();
    const stored = JSON.parse(raw!);
    expect(stored.state.filters.state).toBe("TX");
  });

  it("restores filters from localStorage on rehydrate", () => {
    localStorage.setItem(
      "datalens-filters",
      JSON.stringify({ state: { filters: { category: "grocery_pos" } }, version: 0 })
    );
    useFilters.persist.rehydrate();
    expect(useFilters.getState().filters).toEqual({ category: "grocery_pos" });
  });
});
