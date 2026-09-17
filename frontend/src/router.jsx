import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { PlaceholderPage } from './pages/PlaceholderPage'

// Non-Home routes are lazy-loaded so the initial bundle only pays for what
// the Home page needs (frontendplan.md §7). They currently resolve to the
// same honest placeholder component with page-specific copy; each becomes a
// real page in its own phase (§8).
const StandardsSearchPage = lazy(() => import('./pages/StandardsSearchPage'))
const StandardDetailPage = lazy(() => import('./pages/StandardDetailPage'))
const GapCheckerPage = lazy(() => import('./pages/GapCheckerPage'))


const GraphPlaceholder = lazy(() =>
  Promise.resolve({
    default: () => (
      <PlaceholderPage
        title="Standards Relationship Graph"
        description="Explore which standards a given one supersedes, references, or shares a category with."
        phase="Coming in Frontend Phase 4"
      />
    ),
  })
)

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
    <div className="flex min-h-[40vh] items-center justify-center" role="status" aria-label="Loading page">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-primary" />
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


          <Route path="/graph" element={<GraphPlaceholder />} />
          <Route path="*" element={<NotFoundPlaceholder />} />

        </Routes>
      </Suspense>
    </AppShell>
  )
}
