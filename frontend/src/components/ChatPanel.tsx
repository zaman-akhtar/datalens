import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import type { ChatMessageRecord, ToolCallRecord } from "@/lib/types";

interface UIMessage {
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCallRecord[];
}

export function ChatPanel() {
  const datasetId = useDataset((s) => s.datasetId);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [convId, setConvId] = useState<string | null>(null);

  useEffect(() => {
    setMessages([]);
    setConvId(null);
    if (!datasetId) return;
    api.chatHistory(datasetId).then((rows: ChatMessageRecord[]) => {
      const ui: UIMessage[] = rows
        .filter((r) => r.role === "user" || r.role === "assistant")
        .map((r) => ({ role: r.role as "user" | "assistant", content: r.content }));
      setMessages(ui);
    });
  }, [datasetId]);

  async function send() {
    if (!datasetId || !input.trim() || busy) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    try {
      const r = await api.chat(datasetId, text, convId);
      setConvId(r.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: r.answer, toolCalls: r.tool_calls },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `(error: ${e instanceof Error ? e.message : String(e)})` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  if (!datasetId)
    return <div className="p-3 text-sm text-gray-500">Upload a CSV to start chatting.</div>;

  return (
    <div data-testid="chat-panel" className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3 flex flex-col h-full">
      <div data-testid="chat-messages" className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <p className="text-xs text-gray-500">
            Ask a question — try "which category has the most rows?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={
                "inline-block rounded-lg px-3 py-1.5 text-sm max-w-[90%] " +
                (m.role === "user"
                  ? "bg-indigo-600/70 text-white"
                  : "bg-gray-800/80 text-gray-200")
              }
            >
              {m.content}
            </div>
            {m.toolCalls?.length ? (
              <details className="mt-1 text-xs text-gray-500">
                <summary className="cursor-pointer">Tool calls ({m.toolCalls.length})</summary>
                <pre className="bg-gray-800/60 border border-gray-700/30 rounded p-2 mt-1 overflow-x-auto whitespace-pre-wrap break-words text-gray-400">
                  {m.toolCalls
                    .map((t) => `→ ${t.name}(${JSON.stringify(t.args)})\n${t.result_preview}`)
                    .join("\n\n")}
                </pre>
              </details>
            ) : null}
          </div>
        ))}
      </div>
      <form
        className="flex gap-2 mt-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          data-testid="chat-input"
          className="flex-1 bg-gray-800/60 border border-gray-700/50 rounded-lg px-3 py-1.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500/60"
          placeholder="Ask anything…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
        />
        <button
          type="submit"
          data-testid="chat-send"
          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm disabled:opacity-40 transition-colors"
          disabled={busy || !input.trim()}
        >
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
