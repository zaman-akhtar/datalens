import { create } from "zustand";
import { persist } from "zustand/middleware";

interface DatasetState {
  datasetId: string | null;
  filename: string | null;
  set: (id: string, filename: string) => void;
  clear: () => void;
}

export const useDataset = create<DatasetState>()(
  persist(
    (set) => ({
      datasetId: null,
      filename: null,
      set: (id, filename) => set({ datasetId: id, filename }),
      clear: () => set({ datasetId: null, filename: null }),
    }),
    { name: "datalens-dataset" }
  )
);
