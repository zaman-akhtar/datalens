import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { useDataset } from "@/hooks/useDataset";

beforeEach(() => {
  useDataset.getState().clear();
  vi.restoreAllMocks();
});

describe("ExecutiveSummary", () => {
  it("renders text from the API", async () => {
    useDataset.getState().set("ds1", "demo.csv");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ dataset_id: "ds1", text: "summary 42 rows", generated_at: "2026" }), { status: 200 })
      )
    );
    render(<ExecutiveSummary />);
    await waitFor(() => expect(screen.getByText(/summary 42 rows/)).toBeInTheDocument());
  });
  it("calls refresh=true when regenerate is clicked", async () => {
    useDataset.getState().set("ds1", "demo.csv");
    const fetchMock = vi.fn(async (url: string) =>
      new Response(JSON.stringify({ dataset_id: "ds1", text: "x", generated_at: "2026" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<ExecutiveSummary />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    fireEvent.click(screen.getByTestId("summary-regenerate"));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("refresh=true"))).toBe(true)
    );
  });
});
