import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FilterMap } from "@/lib/types";

interface FilterState {
  filters: FilterMap;
  setFilter: (column: string, value: string | number | null) => void;
  clear: () => void;
}

export const useFilters = create<FilterState>()(
  persist(
    (set) => ({
      filters: {},
      setFilter: (column, value) =>
        set((s) => {
          const next = { ...s.filters };
          if (value === null || value === "") delete next[column];
          else next[column] = value;
          return { filters: next };
        }),
      clear: () => set({ filters: {} }),
    }),
    { name: "datalens-filters" }
  )
);
