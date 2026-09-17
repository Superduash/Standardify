import { Filter, RotateCcw } from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'


const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'Active', label: 'Active' },
  { value: 'Superseded', label: 'Superseded' },
  { value: 'Withdrawn', label: 'Withdrawn' },
  { value: 'Under Revision', label: 'Under Revision' },
]

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Most relevant' },
  { value: 'standard_asc', label: 'Standard No. (A → Z)' },
  { value: 'standard_desc', label: 'Standard No. (Z → A)' },
]

/**
 * @param {{
 *   categories: string[],
 *   selectedCategory: string,
 *   onCategoryChange: (cat: string) => void,
 *   selectedStatus: string,
 *   onStatusChange: (status: string) => void,
 *   sortBy: string,
 *   onSortChange: (sort: string) => void,
 *   totalResults: number,
 *   filteredCount: number,
 *   onReset: () => void,
 *   className?: string
 * }} props
 */
export function SearchFilters({
  categories = [],
  selectedCategory = '',
  onCategoryChange,
  selectedStatus = '',
  onStatusChange,
  sortBy = 'relevance',
  onSortChange,
  totalResults = 0,
  filteredCount = 0,
  onReset,
  className,
}) {
  const isFiltered = Boolean(selectedCategory || selectedStatus || sortBy !== 'relevance')

  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-border bg-surface p-4 shadow-[var(--shadow-card)]',
        className
      )}
      role="region"
      aria-label="Search results filters and sorting"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Results count indicator */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-primary" aria-hidden="true" />
          <span className="text-sm font-medium text-text">
            {isFiltered ? (
              <>
                Showing <strong className="font-technical text-primary">{filteredCount}</strong> of{' '}
                <strong className="font-technical">{totalResults}</strong> standards
              </>
            ) : (
              <>
                <strong className="font-technical text-primary">{totalResults}</strong> standard
                {totalResults === 1 ? '' : 's'} found
              </>
            )}
          </span>
        </div>

        {/* Filter & Sort Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="filter-category" className="text-xs font-medium text-text-muted">
              Category:
            </label>
            <select
              id="filter-category"
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="h-8 rounded-[var(--radius-md)] border border-border bg-surface px-2.5 text-xs font-medium text-text transition-colors hover:border-primary/50 focus-visible:border-primary"
            >
              <option value="">All categories ({categories.length})</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="filter-status" className="text-xs font-medium text-text-muted">
              Status:
            </label>
            <select
              id="filter-status"
              value={selectedStatus}
              onChange={(e) => onStatusChange(e.target.value)}
              className="h-8 rounded-[var(--radius-md)] border border-border bg-surface px-2.5 text-xs font-medium text-text transition-colors hover:border-primary/50 focus-visible:border-primary"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="filter-sort" className="text-xs font-medium text-text-muted">
              Sort:
            </label>
            <div className="relative">
              <select
                id="filter-sort"
                value={sortBy}
                onChange={(e) => onSortChange(e.target.value)}
                className="h-8 rounded-[var(--radius-md)] border border-border bg-surface px-2.5 text-xs font-medium text-text transition-colors hover:border-primary/50 focus-visible:border-primary"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Reset Filters button */}
          {isFiltered && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              className="h-8 px-2 text-xs text-text-muted hover:text-text"
              title="Reset all filters and sort to default"
            >
              <RotateCcw className="h-3 w-3" aria-hidden="true" />
              Reset
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
