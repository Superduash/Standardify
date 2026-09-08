import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { fetchHealth } from "../lib/api";

const NAV_ITEMS = [
  {
    to: "/",
    label: "Ask a Question",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  },
  {
    to: "/gap-check",
    label: "Gap Checker",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  {
    to: "/search",
    label: "Search Standards",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  {
    to: "/graph",
    label: "Standards Graph",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
  },
];

function StatusDot({ status }) {
  if (!status) return null;
  const isOk = status.index_loaded;
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-zinc-500 dark:text-zinc-400">
      <span className={`w-2 h-2 rounded-full ${isOk ? "bg-emerald-500" : "bg-amber-500"}`} />
      <span>
        {isOk
          ? `${status.document_count} chunks indexed`
          : "Index empty — run setup.bat"}
      </span>
    </div>
  );
}

export default function Sidebar() {
  const [health, setHealth] = useState(null);
  const location = useLocation();

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <aside className="sidebar">
      {/* Logo / Brand */}
      <div className="px-5 py-5 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 leading-tight">Standardify</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-500">BIS Standards AI</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-0.5">
        <p className="px-4 py-1.5 text-xs font-semibold text-zinc-400 dark:text-zinc-600 uppercase tracking-wider">
          Features
        </p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `sidebar-nav-item ${isActive ? "active" : ""}`
            }
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-zinc-200 dark:border-zinc-800 py-3">
        <StatusDot status={health} />
        <div className="px-4 py-1">
          <p className="text-xs text-zinc-400 dark:text-zinc-600">SIH 2026 · PS SIH26107</p>
          <p className="text-xs text-zinc-400 dark:text-zinc-600">Seed data — not official BIS</p>
        </div>
      </div>
    </aside>
  );
}
