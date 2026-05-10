import { create } from "zustand";
import type { FilterMap } from "@/lib/types";

interface FilterState {
  filters: FilterMap;
  setFilter: (column: string, value: string | number | null) => void;
  clear: () => void;
}

export const useFilters = create<FilterState>((set) => ({
  filters: {},
  setFilter: (column, value) =>
    set((s) => {
      const next = { ...s.filters };
      if (value === null || value === "") delete next[column];
      else next[column] = value;
      return { filters: next };
    }),
  clear: () => set({ filters: {} }),
}));
