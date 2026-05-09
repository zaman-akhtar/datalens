import { BarView } from "./Bar";
import type { QueryRow } from "@/lib/types";
export function HistogramView({ data, title }: { data: QueryRow[]; title: string }) {
  return <BarView data={data} title={title} />;
}
