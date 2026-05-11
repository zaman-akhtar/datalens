import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatPanel } from "@/components/ChatPanel";
import { useDataset } from "@/hooks/useDataset";

beforeEach(() => {
  useDataset.getState().clear();
  vi.restoreAllMocks();
});

describe("ChatPanel", () => {
  it("shows a placeholder until a dataset is uploaded", () => {
    render(<ChatPanel />);
    expect(screen.getByText(/upload a csv/i)).toBeInTheDocument();
  });

  it("sends a message and renders the assistant reply", async () => {
    useDataset.getState().set("ds1", "demo.csv");
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        calls.push(String(url));
        if (String(url).endsWith("/history"))
          return new Response("[]", { status: 200 });
        return new Response(
          JSON.stringify({ answer: "the answer", conversation_id: "c1", tool_calls: [], partial: false }),
          { status: 200 }
        );
      })
    );
    render(<ChatPanel />);
    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "hi" } });
    fireEvent.click(screen.getByTestId("chat-send"));
    await waitFor(() => expect(screen.getByText("the answer")).toBeInTheDocument());
  });
});
