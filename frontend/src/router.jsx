import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { QuotaDebugPanel } from './components/dev/QuotaDebugPanel'

// Non-Home routes are lazy-loaded so the initial bundle only pays for what
// the Home page needs (frontendplan.md §7). They currently resolve to the
// same honest placeholder component with page-specific copy; each becomes a
// real page in its own phase (§8).
const StandardsSearchPage = lazy(() => import('./pages/StandardsSearchPage'))
const StandardDetailPage = lazy(() => import('./pages/StandardDetailPage'))
const GapCheckerPage = lazy(() => import('./pages/GapCheckerPage'))
const GraphPage = lazy(() => import('./pages/GraphPage'))


const NotFoundPlaceholder = lazy(() =>
  Promise.resolve({
    default: () => (
      <PlaceholderPage
        title="Page not found"
        description="That page doesn't exist. Head back and ask a question instead."
        phase="404"
      />
    ),
  })
)

function RouteFallback() {
  return (
    <div
      className="mx-auto max-w-4xl px-4 py-16 sm:px-6 sm:py-24 text-center space-y-4"
      role="status"
      aria-label="Loading page content"
    >
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-primary-light text-primary">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
      </div>
      <p className="font-technical text-xs font-semibold uppercase tracking-wider text-text-muted">
        Loading Standardify Module...
      </p>
    </div>
  )
}

export function AppRouter() {
  return (
    <AppShell>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/standards" element={<StandardsSearchPage />} />
          <Route path="/standards/:standardNo" element={<StandardDetailPage />} />
          <Route path="/gap-check" element={<GapCheckerPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="*" element={<NotFoundPlaceholder />} />
        </Routes>
      </Suspense>

      {/* Phase 10 debug panel — self-gates on VITE_SHOW_DEBUG_PANEL, invisible in production */}
      <QuotaDebugPanel />
    </AppShell>
  )
}
