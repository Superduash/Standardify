import { useState } from "react";
import { searchStandards } from "../lib/api";

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "ELECTRICAL", label: "Electrical Safety" },
  { value: "CONSUMER_GOODS", label: "Consumer Goods" },
  { value: "TOYS", label: "Toy Safety" },
  { value: "FOOD_PACKAGING", label: "Food & Packaging" },
  { value: "SAFETY_EQUIPMENT", label: "Safety Equipment" },
];

export default function SearchPanel() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const data = await searchStandards(query.trim(), category, 15);
      setResults(data.results || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message || "Search failed. Please ensure the backend is running.");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSearch = () => {
    setQuery("");
    setResults([]);
    setTotal(null);
    setHasSearched(false);
    setError(null);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-slate-900 text-slate-100 p-6">
      <div className="max-w-4xl w-full mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Standards Search
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Search across indexed Bureau of Indian Standards (BIS) clauses, mandates, and technical specs.
          </p>
        </div>

        {/* Search Bar & Filters */}
        <form onSubmit={handleSearch} className="space-y-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., earthing requirements, phthalates limit, pressure relief valve..."
                className="w-full pl-10 pr-10 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-inner"
              />
              <svg
                className="w-5 h-5 absolute left-3 top-3.5 text-slate-400"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {query && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-200"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl shadow transition"
            >
              {isLoading ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto py-1">
            <span className="text-xs text-slate-400 font-medium whitespace-nowrap">Filter:</span>
            {CATEGORIES.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => setCategory(cat.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  category === cat.value
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </form>

        {/* Error message */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
            {error}
          </div>
        )}

        {/* Results stats */}
        {hasSearched && !isLoading && !error && (
          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>
              Found <strong className="text-white">{total}</strong> {total === 1 ? "result" : "results"} for "{query}"
            </span>
            {category && (
              <span className="bg-slate-800 px-2 py-0.5 rounded text-indigo-400">
                Category: {category}
              </span>
            )}
          </div>
        )}

        {/* Results List */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-5 rounded-xl bg-slate-800 border border-slate-700 animate-pulse space-y-2">
                <div className="h-4 bg-slate-700 rounded w-1/4"></div>
                <div className="h-4 bg-slate-700 rounded w-3/4"></div>
                <div className="h-3 bg-slate-700 rounded w-full"></div>
              </div>
            ))}
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-4">
            {results.map((res, i) => (
              <div
                key={i}
                className="p-5 rounded-xl bg-slate-800/80 border border-slate-700/80 hover:border-slate-600 transition shadow-sm space-y-2"
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-indigo-400 text-sm">
                      {res.standard_code || "BIS Standard"}
                    </span>
                    {res.clause_number && (
                      <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono">
                        Cl. {res.clause_number}
                      </span>
                    )}
                    {res.category && (
                      <span className="text-xs bg-slate-700/60 text-slate-400 px-2 py-0.5 rounded">
                        {res.category}
                      </span>
                    )}
                  </div>
                  {res.similarity_score !== undefined && (
                    <span className="text-xs text-slate-400">
                      Match: {(res.similarity_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <p className="text-sm text-slate-200 leading-relaxed">
                  {res.text || res.content || res.excerpt}
                </p>

                {res.clause_title && (
                  <p className="text-xs text-slate-400 italic">
                    Title: {res.clause_title}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : hasSearched && !isLoading ? (
          <div className="text-center py-12 border border-dashed border-slate-700 rounded-2xl">
            <p className="text-slate-400 text-sm">No matching standard clauses found.</p>
            <p className="text-slate-500 text-xs mt-1">Try broader terms or select "All Categories".</p>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500 text-sm">
            Enter a standard code, keyword, or compliance requirement above to search.
          </div>
        )}
      </div>
    </div>
  );
}
