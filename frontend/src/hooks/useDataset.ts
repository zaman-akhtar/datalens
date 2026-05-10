import { create } from "zustand";

interface DatasetState {
  datasetId: string | null;
  filename: string | null;
  set: (id: string, filename: string) => void;
  clear: () => void;
}

export const useDataset = create<DatasetState>((set) => ({
  datasetId: null,
  filename: null,
  set: (id, filename) => set({ datasetId: id, filename }),
  clear: () => set({ datasetId: null, filename: null }),
}));
