import { useState } from "react";
import { runGapCheck } from "../lib/api";

const SAMPLE_DESCRIPTIONS = [
  "We manufacture plastic water bottles (500 mL) made from PET for consumer use. The bottles feature a screw cap and are intended for storing drinking water. We apply a paper label with brand name and manufacturing date.",
  "Our product is a battery-operated toy car for children aged 4–10. It has a plastic body, rubber wheels, and uses 4 AA batteries. The vehicle can reach speeds up to 5 km/h and has LED headlights.",
  "We are launching an LED bulb rated at 9W, 800 lumens, 3000K warm white, operating at 220V AC. The product will be sold as a replacement for 60W incandescent bulbs.",
];

function ApplicableStandardCard({ std }) {
  const pct = Math.round(std.similarity_score * 100);
  return (
    <div className="std-card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-indigo-600 dark:text-indigo-400">
              {std.standard_no}
            </span>
            <span className="text-xs text-zinc-400">·</span>
            <span className="text-xs text-zinc-500">{pct}% match</span>
          </div>
          <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200 leading-snug">
            {std.title}
          </p>
        </div>
        <div className="flex-shrink-0">
          <div className="relative w-10 h-10">
            <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e4e4e7" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15.9" fill="none"
                stroke={pct >= 70 ? "#10b981" : pct >= 45 ? "#f59e0b" : "#f87171"}
                strokeWidth="3"
                strokeDasharray={`${pct} ${100 - pct}`}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-zinc-700 dark:text-zinc-300">
              {pct}
            </span>
          </div>
        </div>
      </div>

      {std.matched_clauses && std.matched_clauses.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {std.matched_clauses.map((cl, i) => (
            <span key={i} className="citation-pill">{cl}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function GapItem({ gap }) {
  return (
    <div className="gap-item">
      <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs font-mono font-semibold text-zinc-600 dark:text-zinc-400">
            {gap.standard_no}
          </span>
          {gap.clause_no && (
            <span className="citation-pill">{gap.clause_no}</span>
          )}
        </div>
        <p className="text-sm text-amber-800 dark:text-amber-200 leading-snug">
          {gap.description}
        </p>
      </div>
    </div>
  );
}

export default function GapCheckPanel() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCheck = async () => {
    const text = description.trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await runGapCheck(text);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="panel-header">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Compliance Gap Checker</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
          Describe your product and find applicable BIS standards and potential compliance gaps.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {/* Input area */}
        <div className="space-y-3">
          <label htmlFor="gap-description" className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            Product Description
          </label>
          <textarea
            id="gap-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your product in detail — materials used, intended users, key features, operating conditions…"
            rows={5}
            disabled={loading}
            className="app-textarea w-full"
          />
          <div className="flex items-center gap-3">
            <button
              id="gap-check-submit"
              onClick={handleCheck}
              disabled={loading || description.trim().length < 10}
              className="btn-primary"
            >
              {loading ? <><span className="spinner" /> Analysing…</> : "Check Compliance"}
            </button>
            <button
              onClick={() => { setResult(null); setError(null); setDescription(""); }}
              className="btn-secondary"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Sample descriptions */}
        {!result && !loading && (
          <div>
            <p className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-2">
              Sample descriptions
            </p>
            <div className="space-y-2">
              {SAMPLE_DESCRIPTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setDescription(s)}
                  className="text-left w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700
                             bg-zinc-50 dark:bg-zinc-900 text-sm text-zinc-600 dark:text-zinc-400
                             hover:border-indigo-300 dark:hover:border-indigo-700 hover:text-zinc-800 dark:hover:text-zinc-200
                             transition-colors duration-150"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6 animate-slide-up">
            {/* Applicable standards */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                  Applicable Standards
                </h3>
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                  {result.applicable_standards?.length || 0}
                </span>
              </div>
              {result.applicable_standards?.length > 0 ? (
                <div className="grid gap-3">
                  {result.applicable_standards.map((std, i) => (
                    <ApplicableStandardCard key={i} std={std} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  No applicable standards found for this product description.
                </p>
              )}
            </div>

            {/* Gaps */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                  Potential Compliance Gaps
                </h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                  result.gaps?.length > 0
                    ? "bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300"
                    : "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300"
                }`}>
                  {result.gaps?.length || 0} found
                </span>
              </div>

              {result.mode === "extractive" && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mb-3 flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  AI unavailable — showing matched clauses for manual review
                </p>
              )}

              {result.gaps?.length > 0 ? (
                <div className="space-y-2">
                  {result.gaps.map((gap, i) => (
                    <GapItem key={i} gap={gap} />
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-2 p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800">
                  <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-emerald-700 dark:text-emerald-300">
                    No gaps identified — product description appears to address all matched clauses.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
