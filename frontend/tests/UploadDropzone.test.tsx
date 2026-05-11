import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UploadDropzone } from "@/components/UploadDropzone";
import { useDataset } from "@/hooks/useDataset";

beforeEach(() => useDataset.getState().clear());

describe("UploadDropzone", () => {
  it("renders a button", () => {
    render(<UploadDropzone />);
    expect(screen.getByText(/choose a file/i)).toBeInTheDocument();
  });

  it("uploads a file and stores dataset id", async () => {
    const fakeAck = { dataset_id: "abc", original_filename: "f.csv", n_rows: 1, n_cols: 1 };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(fakeAck), { status: 201 }))
    );
    render(<UploadDropzone />);
    const input = screen.getByTestId("upload-input") as HTMLInputElement;
    const file = new File(["a,b\n1,2"], "f.csv", { type: "text/csv" });
    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);
    await waitFor(() => expect(useDataset.getState().datasetId).toBe("abc"));
  });
});
