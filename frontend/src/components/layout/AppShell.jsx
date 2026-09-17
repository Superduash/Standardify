import { Header } from './Header'
import { Footer } from './Footer'
import { RouteFocusManager } from './RouteFocusManager'

export function AppShell({ children }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      {/* Accessible Skip to Content Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-[var(--radius-md)] focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
      >
        Skip to main content
      </a>

      <RouteFocusManager />
      <Header />

      <main id="main-content" className="flex-1 focus:outline-none" tabIndex={-1}>
        {children}
      </main>

      <Footer />
    </div>
  )
}

export default AppShell
