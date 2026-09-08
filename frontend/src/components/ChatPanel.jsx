import { useState, useRef, useEffect } from "react";
import { queryStandards } from "../lib/api";

const MODE_LABELS = {
  groq: { label: "Groq AI", cls: "mode-badge-groq" },
  gemini: { label: "Gemini AI", cls: "mode-badge-gemini" },
  extractive: { label: "Extractive", cls: "mode-badge-extractive" },
  no_match: { label: "No Match", cls: "mode-badge-no_match" },
};

const CONF_LABELS = {
  high: "confidence-high",
  medium: "confidence-medium",
  low: "confidence-low",
};

const SAMPLE_QUESTIONS = [
  "What are the insulation resistance requirements for household electrical appliances?",
  "What labelling information is required on packaged drinking water containers?",
  "What impact absorption standard must a motorcycle helmet meet?",
  "What are the chemical migration limits for toy paints and coatings?",
  "What luminous efficacy is required for LED street lights?",
];

function ModeBadge({ mode }) {
  const info = MODE_LABELS[mode] || MODE_LABELS.no_match;
  return (
    <span className={`mode-badge ${info.cls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {info.label}
    </span>
  );
}

function ConfidenceBadge({ confidence }) {
  return (
    <span className={`mode-badge ${CONF_LABELS[confidence] || "confidence-low"}`}>
      {confidence} confidence
    </span>
  );
}

function Citation({ citation, index }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="citation-pill flex-col items-start !px-3 !py-2 gap-1 !rounded-lg w-full">
      <div className="flex items-center gap-2 w-full">
        <span className="text-indigo-600 dark:text-indigo-400 font-semibold">[{index}]</span>
        <span className="font-semibold text-zinc-700 dark:text-zinc-300">{citation.standard_no}</span>
        {citation.clause_no && (
          <span className="text-zinc-500 dark:text-zinc-400">· {citation.clause_no}</span>
        )}
        {citation.chunk_text && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-auto text-zinc-400 hover:text-indigo-500 transition-colors"
            aria-label="Toggle citation text"
          >
            <svg className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>
      {citation.title && (
        <span className="text-zinc-500 dark:text-zinc-400 text-xs">{citation.title}</span>
      )}
      {expanded && citation.chunk_text && (
        <p className="text-zinc-600 dark:text-zinc-400 text-xs mt-1 leading-relaxed font-mono">
          {citation.chunk_text}
        </p>
      )}
    </div>
  );
}

function AssistantMessage({ msg }) {
  const isExtractive = msg.mode === "extractive";
  return (
    <div className="flex flex-col gap-2 animate-slide-up">
      <div className="chat-bubble-assistant">
        {isExtractive && (
          <p className="text-xs text-amber-600 dark:text-amber-400 font-medium mb-2 pb-2 border-b border-zinc-200 dark:border-zinc-700">
            ⚠ Showing best-matching clause directly — AI summarization unavailable
          </p>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{msg.answer}</p>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-2 flex-wrap ml-1">
        <ModeBadge mode={msg.mode} />
        <ConfidenceBadge confidence={msg.confidence} />
      </div>

      {/* Citations */}
      {msg.citations && msg.citations.length > 0 && (
        <div className="space-y-1.5 mt-1">
          <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 ml-1">Sources</p>
          {msg.citations.map((c, i) => (
            <Citation key={i} citation={c} index={i + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function UserMessage({ text }) {
  return (
    <div className="flex justify-end animate-fade-in">
      <div className="chat-bubble-user">{text}</div>
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { type: "user", text: q }]);
    setLoading(true);

    try {
      const data = await queryStandards(q);
      setMessages((prev) => [...prev, { type: "assistant", ...data }]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [...prev, {
        type: "assistant",
        answer: `Error: ${err.message}`,
        citations: [],
        confidence: "low",
        mode: "no_match",
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="panel-header">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Ask a Question</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
          Query Indian BIS standards in natural language. Responses cite the exact clause.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="animate-fade-in">
            <p className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3">Try asking:</p>
            <div className="grid gap-2">
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSubmit(q)}
                  disabled={loading}
                  className="text-left px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700
                             bg-white dark:bg-zinc-900 text-sm text-zinc-700 dark:text-zinc-300
                             hover:border-indigo-300 dark:hover:border-indigo-700 hover:text-indigo-700 dark:hover:text-indigo-300
                             transition-colors duration-150 disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) =>
          msg.type === "user" ? (
            <UserMessage key={i} text={msg.text} />
          ) : (
            <AssistantMessage key={i} msg={msg} />
          )
        )}

        {loading && (
          <div className="flex items-center gap-3 animate-fade-in">
            <div className="flex gap-1">
              {[0, 1, 2].map((d) => (
                <div
                  key={d}
                  className="w-2 h-2 rounded-full bg-indigo-400"
                  style={{ animation: `bounce 1.2s ease-in-out ${d * 0.2}s infinite` }}
                />
              ))}
            </div>
            <span className="text-xs text-zinc-400">Searching standards…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-8 py-5 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about any BIS standard, clause, or requirement…"
            rows={2}
            disabled={loading}
            className="app-textarea !min-h-0 h-[60px] resize-none flex-1"
          />
          <button
            id="chat-submit"
            onClick={() => handleSubmit()}
            disabled={loading || !input.trim()}
            className="btn-primary flex-shrink-0 h-[60px] px-6"
          >
            {loading ? (
              <span className="spinner" />
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            )}
            {loading ? "Searching…" : "Ask"}
          </button>
        </div>
        <p className="mt-2 text-xs text-zinc-400">Press Enter to send · Shift+Enter for new line</p>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-8px); }
        }
      `}</style>
    </div>
  );
}
