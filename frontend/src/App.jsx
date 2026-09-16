import { Routes, Route, Navigate } from 'react-router-dom'

/**
 * Root application component.
 * Routes are wired here as each frontend phase adds its pages.
 * Phase 0: minimal placeholder — routes filled in per-phase.
 */
export default function App() {
  return (
    <Routes>
      {/* Phase 0 placeholder — replace with real pages in later phases */}
      <Route
        path="/"
        element={
          <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
            <div className="text-center space-y-4">
              <h1 className="text-4xl font-bold tracking-tight">Standardify</h1>
              <p className="text-gray-400 text-lg">
                AI Assistant for Indian Bureau of Standards — Phase 0 Scaffold
              </p>
              <p className="text-sm text-gray-600">
                Frontend structure is in place. UI components will be built in later phases.
              </p>
            </div>
          </div>
        }
      />
      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
