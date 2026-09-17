import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SearchBar } from '../components/search/SearchBar'
import { SearchResultsList } from '../components/search/SearchResultsList'
import { searchStandards } from '../api/endpoints'
import { normalizeApiError } from '../api/client'
import { useToast } from '../context/ToastContext'

export function StandardsSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { showToast } = useToast()

  // Read filter & sort state directly from searchParams (Single Source of Truth)
  const selectedCategory = searchParams.get('category') || ''
  const selectedStatus = searchParams.get('status') || ''
  const sortBy = searchParams.get('sort') || 'relevance'
  const urlQuery = (searchParams.get('q') || '').trim()

  // Input state (for user typing in the box)
  const [queryInput, setQueryInput] = useState(urlQuery)
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  // API Data & UX state
  const [rawResults, setRawResults] = useState([])
  const [totalResults, setTotalResults] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const abortControllerRef = useRef(null)

  // Sync state changes back to URL search params
  const updateUrlParams = useCallback(
    (newQ, newCat, newStat, newSort) => {
      const params = new URLSearchParams()
      if (newQ) params.set('q', newQ)
      if (newCat) params.set('category', newCat)
      if (newStat) params.set('status', newStat)
      if (newSort && newSort !== 'relevance') params.set('sort', newSort)
      setSearchParams(params)
    },
    [setSearchParams]
  )

  // Execute Search API call (only on explicit query submit / URL change)
  const executeSearch = useCallback(
    async (searchQuery) => {
      const trimmed = searchQuery.trim()
      if (!trimmed) return

      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      const controller = new AbortController()
      abortControllerRef.current = controller

      setLoading(true)
      setError(null)
      setHasSearched(true)
      setSubmittedQuery(trimmed)

      try {
        const data = await searchStandards(trimmed, { signal: controller.signal })
        if (!controller.signal.aborted) {
          const results = Array.isArray(data?.results) ? data.results : []
          setRawResults(results)
          setTotalResults(typeof data?.total_results === 'number' ? data.total_results : results.length)
        }
      } catch (err) {
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError' && err?.code !== 'ERR_CANCELED') {
          const normalized = normalizeApiError(err)
          setError(normalized)
          setRawResults([])
          setTotalResults(0)
          showToast(normalized.message, 'error')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    },
    [showToast]
  )

  // Execute search when URL `?q=` changes (including initial load & back/forward navigation)
  useEffect(() => {
    if (urlQuery) {
      setQueryInput(urlQuery)
      executeSearch(urlQuery)
    } else {
      setQueryInput('')
      setSubmittedQuery('')
      setRawResults([])
      setTotalResults(0)
      setHasSearched(false)
    }
  }, [urlQuery, executeSearch])

  // Handle Search Submission
  const handleSubmit = (queryToSearch) => {
    const trimmed = queryToSearch.trim()
    if (!trimmed) return
    setQueryInput(trimmed)
    updateUrlParams(trimmed, selectedCategory, selectedStatus, sortBy)
    executeSearch(trimmed)
  }

  // Handle Filter / Sort changes (NO API CALL — client-side URL update only!)
  const handleCategoryChange = (cat) => {
    updateUrlParams(submittedQuery || urlQuery, cat, selectedStatus, sortBy)
  }

  const handleStatusChange = (status) => {
    updateUrlParams(submittedQuery || urlQuery, selectedCategory, status, sortBy)
  }

  const handleSortChange = (sort) => {
    updateUrlParams(submittedQuery || urlQuery, selectedCategory, selectedStatus, sort)
  }

  const handleResetFilters = () => {
    updateUrlParams(submittedQuery || urlQuery, '', '', 'relevance')
  }


  // Extract unique categories from raw result set
  const categories = useMemo(() => {
    const set = new Set()
    rawResults.forEach((r) => {
      if (r.category && typeof r.category === 'string') {
        set.add(r.category)
      }
    })
    return Array.from(set).sort()
  }, [rawResults])

  // Compute filtered and sorted result list purely in-memory
  const filteredAndSortedResults = useMemo(() => {
    let list = [...rawResults]

    // Category filter
    if (selectedCategory) {
      list = list.filter((r) => r.category === selectedCategory)
    }

    // Status filter (case-insensitive check)
    if (selectedStatus) {
      list = list.filter(
        (r) => (r.status || '').toLowerCase() === selectedStatus.toLowerCase()
      )
    }

    // Sort order
    if (sortBy === 'standard_asc') {
      list.sort((a, b) =>
        (a.standard_no || '').localeCompare(b.standard_no || '', undefined, {
          numeric: true,
          sensitivity: 'base',
        })
      )
    } else if (sortBy === 'standard_desc') {
      list.sort((a, b) =>
        (b.standard_no || '').localeCompare(a.standard_no || '', undefined, {
          numeric: true,
          sensitivity: 'base',
        })
      )
    }
    // Default 'relevance' retains the server's ranking

    return list
  }, [rawResults, selectedCategory, selectedStatus, sortBy])

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      {/* Page Header */}
      <header className="mb-6 text-center sm:text-left">
        <span className="inline-flex items-center rounded-full border border-primary/20 bg-primary-light px-3 py-1 text-xs font-medium text-primary">
          BIS Repository
        </span>
        <h1 className="mt-2 text-2xl font-bold text-text sm:text-3xl">
          Indian Standards Search
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Search and filter verified Bureau of Indian Standards (BIS) documents by standard number,
          product title, or technical keywords.
        </p>
      </header>

      {/* Search Input Bar */}
      <section aria-label="Search controls" className="mb-8">
        <SearchBar
          value={queryInput}
          onChange={setQueryInput}
          onSubmit={handleSubmit}
          loading={loading}
          autoFocus={!initialQuery}
        />
      </section>

      {/* Results / UX States List */}
      <SearchResultsList
        key={`${submittedQuery}-${selectedCategory}-${selectedStatus}-${sortBy}`}
        results={filteredAndSortedResults}
        totalResults={totalResults}
        loading={loading}
        error={error}
        onRetry={() => executeSearch(submittedQuery)}
        query={submittedQuery}
        hasSearched={hasSearched}
        categories={categories}
        selectedCategory={selectedCategory}
        onCategoryChange={handleCategoryChange}
        selectedStatus={selectedStatus}
        onStatusChange={handleStatusChange}
        sortBy={sortBy}
        onSortChange={handleSortChange}
        onResetFilters={handleResetFilters}
        onExampleClick={(term) => {
          setQueryInput(term)
          handleSubmit(term)
        }}
      />

    </main>
  )
}

export default StandardsSearchPage
