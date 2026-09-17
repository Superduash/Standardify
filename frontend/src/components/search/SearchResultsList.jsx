import { useState } from 'react'
import { ChevronDown, Search, SearchX } from 'lucide-react'

import { SearchResultCard } from './SearchResultCard'
import { SearchFilters } from './SearchFilters'
import { EmptyState } from '../ui/EmptyState'
import { ErrorState } from '../ui/ErrorState'
import { SearchResultsSkeleton } from '../ui/Skeleton'
import { Button } from '../ui/Button'

const PAGE_SIZE = 10

/**
 * Renders search results, filter toolbar, pagination reveal ("show more"),
 * and all 4 UX states (loading, empty, error, success).
 *
 * @param {{
 *   results: import('../../api/types').SearchResult[],
 *   totalResults: number,
 *   loading: boolean,
 *   error: import('../../api/client').NormalizedApiError | null,
 *   onRetry: () => void,
 *   query: string,
 *   hasSearched: boolean,
 *   categories: string[],
 *   selectedCategory: string,
 *   onCategoryChange: (cat: string) => void,
 *   selectedStatus: string,
 *   onStatusChange: (status: string) => void,
 *   sortBy: string,
 *   onSortChange: (sort: string) => void,
 *   onResetFilters: () => void,
 *   onExampleClick?: (term: string) => void,
 * }} props
 */
export function SearchResultsList({
  results = [],
  totalResults = 0,
  loading = false,
  error = null,
  onRetry,
  query = '',
  hasSearched = false,
  categories = [],
  selectedCategory = '',
  onCategoryChange,
  selectedStatus = '',
  onStatusChange,
  sortBy = 'relevance',
  onSortChange,
  onResetFilters,
  onExampleClick,
}) {
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)


  // 1. Loading State
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-text-muted">
          <span>Searching Indian Standards repository...</span>
        </div>
        <SearchResultsSkeleton count={4} />
      </div>
    )
  }

  // 2. Error State
  if (error) {
    return (
      <ErrorState
        message={error.message || 'Failed to fetch standards. Please check your network and try again.'}
        requestId={error.requestId}
        onRetry={onRetry}
      />
    )
  }

  // 3. Idle / Initial State (No search performed yet)
  if (!hasSearched) {
    return (
      <div className="rounded-[var(--radius-lg)] border border-dashed border-border bg-surface p-8 text-center sm:p-12">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-light text-primary">
          <Search className="h-6 w-6" aria-hidden="true" />
        </div>
        <h2 className="mt-4 text-base font-semibold text-text">
          Search the Indian Standards Repository
        </h2>
        <p className="mx-auto mt-1 max-w-md text-sm text-text-muted">
          Look up standards by standard number (e.g. <span className="font-technical">IS 374</span>),
          product category, or technical keywords.
        </p>

        {onExampleClick && (
          <div className="mt-6">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Popular Searches
            </p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              {['IS 374', 'IS 9001', 'Drinking water', 'Electric fans', 'Packaging'].map((term) => (
                <button
                  key={term}
                  type="button"
                  onClick={() => onExampleClick(term)}
                  className="rounded-[var(--radius-sm)] border border-border bg-bg px-2.5 py-1 text-xs font-medium text-text-body transition-colors hover:border-primary/40 hover:bg-primary-light/50 hover:text-primary"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // 4. Empty State: Backend returned zero results for this query
  if (totalResults === 0) {
    return (
      <EmptyState
        icon={SearchX}
        title="No standards matched"
        description={`We couldn't find any Indian Standards matching "${query}". Try searching by standard number (e.g. IS 374), product name, or broader technical keywords.`}
      />
    )
  }

  // 5. Filter Empty State: Results exist from server, but client filters eliminated all
  if (results.length === 0) {
    return (
      <div className="space-y-4">
        <SearchFilters
          categories={categories}
          selectedCategory={selectedCategory}
          onCategoryChange={onCategoryChange}
          selectedStatus={selectedStatus}
          onStatusChange={onStatusChange}
          sortBy={sortBy}
          onSortChange={onSortChange}
          totalResults={totalResults}
          filteredCount={0}
          onReset={onResetFilters}
        />
        <EmptyState
          icon={SearchX}
          title="No standards match the selected filters"
          description="Try broadening your category or lifecycle status filters to see matching standards."
          action={
            <Button variant="secondary" size="sm" onClick={onResetFilters}>
              Reset all filters
            </Button>
          }
        />
      </div>
    )
  }

  // 6. Success State: Render filters, list of cards, and client-side "Show more"
  const visibleResults = results.slice(0, visibleCount)
  const hasMore = results.length > visibleCount

  return (
    <div className="space-y-4">
      {/* Filter and sorting toolbar */}
      <SearchFilters
        categories={categories}
        selectedCategory={selectedCategory}
        onCategoryChange={onCategoryChange}
        selectedStatus={selectedStatus}
        onStatusChange={onStatusChange}
        sortBy={sortBy}
        onSortChange={onSortChange}
        totalResults={totalResults}
        filteredCount={results.length}
        onReset={onResetFilters}
      />

      {/* List of search results */}
      <section
        aria-label="Standards search results"
        className="space-y-3"
      >
        {visibleResults.map((result, idx) => (
          <SearchResultCard
            key={`${result.standard_no}-${idx}`}
            result={result}
          />
        ))}
      </section>

      {/* Client-side "Show more" reveal */}
      {hasMore && (
        <div className="flex flex-col items-center justify-center pt-3">
          <Button
            variant="secondary"
            onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
            className="w-full sm:w-auto"
          >
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
            Show more standards ({visibleCount} of {results.length})
          </Button>
          <p className="mt-2 text-xs text-text-muted">
            Showing {visibleCount} of {results.length} matched standards
          </p>
        </div>
      )}
    </div>
  )
}
