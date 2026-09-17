import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { FileSearch, Menu, MessageSquareText, Network, ShieldCheck } from 'lucide-react'
import { cn } from '../../lib/utils'
import { MobileNav } from './MobileNav'

const NAV_ITEMS = [
  { to: '/', label: 'Ask', icon: MessageSquareText, end: true },
  { to: '/standards', label: 'Standards', icon: FileSearch },
  { to: '/gap-check', label: 'Gap Check', icon: ShieldCheck },
  { to: '/graph', label: 'Graph', icon: Network },
]


export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <NavLink to="/" className="flex items-center gap-2" aria-label="Standardify home">
          <span className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-primary text-sm font-semibold text-white">
            S
          </span>
          <span className="text-base font-semibold tracking-tight text-text">Standardify</span>
        </NavLink>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-1.5 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-light text-primary-dark'
                    : 'text-text-body hover:bg-bg hover:text-text'
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="https://github.com/Superduash/Standardify"
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-[var(--radius-md)] border border-border px-3 py-2 text-sm font-medium text-text-body transition-colors hover:bg-bg sm:inline-flex"
          >
            View source
          </a>
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] text-text-body hover:bg-bg md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation menu"
            aria-expanded={mobileOpen}
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>

      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} items={NAV_ITEMS} />
    </header>
  )
}
