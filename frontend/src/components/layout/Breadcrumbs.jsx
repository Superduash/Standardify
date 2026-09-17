import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * @typedef {Object} BreadcrumbItem
 * @property {string} label - The display text
 * @property {string} [to] - Optional navigation destination link
 * @property {boolean} [current] - Whether this item is the active/current page
 * @property {boolean} [isCode] - Whether to render with the technical monospace font
 */

/**
 * Accessible, responsive breadcrumb navigation component.
 *
 * @param {{
 *   items: BreadcrumbItem[],
 *   className?: string,
 * }} props
 */
export function Breadcrumbs({ items = [], className }) {
  if (!items || items.length === 0) return null

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center text-xs text-text-muted', className)}
    >
      <ol className="flex flex-wrap items-center gap-1.5 sm:gap-2">
        {/* Home Root */}
        <li className="inline-flex items-center">
          <Link
            to="/"
            className="inline-flex items-center gap-1 rounded-[var(--radius-sm)] text-text-muted transition-colors hover:text-primary focus-visible:ring-2 focus-visible:ring-primary"
            title="Standardify Home"
          >
            <Home className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="sr-only sm:not-sr-only">Home</span>
          </Link>
        </li>

        {items.map((item, idx) => {
          const isLast = idx === items.length - 1 || item.current

          return (
            <li key={`${item.label}-${idx}`} className="inline-flex items-center gap-1.5 sm:gap-2">
              <ChevronRight
                className="h-3 w-3 shrink-0 text-text-muted/60"
                aria-hidden="true"
              />

              {isLast ? (
                <span
                  className={cn(
                    'font-medium text-text truncate max-w-[200px] sm:max-w-[340px]',
                    item.isCode && 'font-technical'
                  )}
                  aria-current="page"
                  title={item.label}
                >
                  {item.label}
                </span>
              ) : item.to ? (
                <Link
                  to={item.to}
                  className={cn(
                    'rounded-[var(--radius-sm)] transition-colors hover:text-primary focus-visible:ring-2 focus-visible:ring-primary truncate max-w-[150px] sm:max-w-[220px]',
                    item.isCode && 'font-technical'
                  )}
                  title={item.label}
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={cn(
                    'text-text-muted truncate max-w-[150px] sm:max-w-[220px]',
                    item.isCode && 'font-technical'
                  )}
                >
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export default Breadcrumbs
