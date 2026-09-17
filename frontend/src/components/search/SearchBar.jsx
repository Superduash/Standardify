import { useEffect, useRef, useState } from 'react'
import { FileText, Loader2, Search, X } from 'lucide-react'
import { suggestStandards } from '../../api/endpoints'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

/**
 * Accessible ARIA combobox with debounced typeahead suggestions and full
 * keyboard navigation support (Arrow keys, Enter, Escape).
 *
 * @param {{
 *   value: string,
 *   onChange: (val: string) => void,
 *   onSubmit: (query: string) => void,
 *   loading?: boolean,
 *   placeholder?: string,
 *   className?: string,
 *   autoFocus?: boolean,
 * }} props
 */
export function SearchBar({
  value = '',
  onChange,
  onSubmit,
  loading = false,
  placeholder = 'Search by standard number (e.g. IS 374), title, or keyword...',
  className,
  autoFocus = false,
}) {
  const [suggestions, setSuggestions] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const [isSuggesting, setIsSuggesting] = useState(false)

  const inputRef = useRef(null)
  const containerRef = useRef(null)
  const abortControllerRef = useRef(null)
  const debounceTimerRef = useRef(null)

  // Debounced suggest fetch
  useEffect(() => {
    const trimmed = value.trim()

    // Clear any previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Abort previous in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    if (!trimmed || trimmed.length < 2) {
      debounceTimerRef.current = setTimeout(() => {
        setSuggestions([])
        setIsOpen(false)
        setIsSuggesting(false)
        setActiveIndex(-1)
      }, 0)
      return
    }


    debounceTimerRef.current = setTimeout(async () => {
      const controller = new AbortController()
      abortControllerRef.current = controller
      setIsSuggesting(true)

      try {
        const data = await suggestStandards(trimmed, { signal: controller.signal })
        if (!controller.signal.aborted) {
          const items = Array.isArray(data?.suggestions) ? data.suggestions : []
          setSuggestions(items)
          setIsOpen(items.length > 0)
          setActiveIndex(-1)
        }
      } catch (err) {
        // Ignore aborted requests
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError' && err?.code !== 'ERR_CANCELED') {
          setSuggestions([])
          setIsOpen(false)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsSuggesting(false)
        }
      }
    }, 250) // ~250ms debounce per frontendplan.md §9 Phase 1

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [value])

  // Handle outside clicks to close dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
        setActiveIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    setIsOpen(false)
    setActiveIndex(-1)
    if (value.trim()) {
      onSubmit(value.trim())
    }
  }

  const handleSelectSuggestion = (item) => {
    const selectedQuery = item.standard_no || item.title
    onChange(selectedQuery)
    setIsOpen(false)
    setActiveIndex(-1)
    onSubmit(selectedQuery)
  }

  const handleKeyDown = (e) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === 'ArrowDown' && suggestions.length > 0) {
        setIsOpen(true)
        setActiveIndex(0)
        e.preventDefault()
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0))
        break

      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1))
        break

      case 'Enter':
        if (activeIndex >= 0 && activeIndex < suggestions.length) {
          e.preventDefault()
          handleSelectSuggestion(suggestions[activeIndex])
        } else {
          handleSubmit(e)
        }
        break

      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setActiveIndex(-1)
        break

      case 'Tab':
        setIsOpen(false)
        setActiveIndex(-1)
        break

      default:
        break
    }
  }

  const handleClear = () => {
    onChange('')
    setSuggestions([])
    setIsOpen(false)
    setActiveIndex(-1)
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      <form onSubmit={handleSubmit} className="relative flex items-center" role="search">
        <div className="relative flex-1">
          {/* Left search icon */}
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-muted">
            <Search className="h-4 w-4" aria-hidden="true" />
          </div>

          {/* Search Input */}
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (suggestions.length > 0) setIsOpen(true)
            }}
            placeholder={placeholder}
            autoFocus={autoFocus}
            autoComplete="off"
            aria-autocomplete="list"
            aria-expanded={isOpen && suggestions.length > 0}
            aria-haspopup="listbox"
            aria-controls="search-suggestions-list"
            aria-activedescendant={
              activeIndex >= 0 ? `suggestion-item-${activeIndex}` : undefined
            }
            className="h-12 w-full rounded-[var(--radius-md)] border border-border bg-surface pl-10 pr-24 text-sm text-text placeholder:text-text-muted transition-colors hover:border-primary/50 focus-visible:border-primary"
          />

          {/* Right action buttons inside input */}
          <div className="absolute inset-y-0 right-0 flex items-center gap-1.5 pr-2">
            {isSuggesting && (
              <Loader2 className="h-4 w-4 animate-spin text-text-muted" aria-label="Loading suggestions" />
            )}

            {value && (
              <button
                type="button"
                onClick={handleClear}
                className="flex h-7 w-7 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-bg hover:text-text"
                aria-label="Clear search input"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            )}

            <Button
              type="submit"
              size="sm"
              loading={loading}
              disabled={loading || !value.trim()}
              className="h-8 px-3 text-xs"
            >
              Search
            </Button>
          </div>
        </div>
      </form>

      {/* Typeahead Suggestions Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <ul
          id="search-suggestions-list"
          role="listbox"
          aria-label="Search suggestions"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded-[var(--radius-lg)] border border-border bg-surface py-1 shadow-lg ring-1 ring-black/5"
        >
          {suggestions.map((item, index) => {
            const isSelected = index === activeIndex
            return (
              <li
                key={`${item.standard_no}-${index}`}
                id={`suggestion-item-${index}`}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => handleSelectSuggestion(item)}
                className={cn(
                  'flex cursor-pointer items-center justify-between gap-3 px-3.5 py-2.5 text-left transition-colors',
                  isSelected ? 'bg-primary-light text-primary-dark' : 'text-text hover:bg-bg'
                )}
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <FileText
                    className={cn(
                      'h-4 w-4 shrink-0',
                      isSelected ? 'text-primary' : 'text-text-muted'
                    )}
                    aria-hidden="true"
                  />
                  <div className="min-w-0">
                    <span className="font-technical text-xs font-semibold">
                      {item.standard_no}
                    </span>
                    <p className="truncate text-xs text-text-body">{item.title}</p>
                  </div>
                </div>
                <span className="shrink-0 font-technical text-[10px] text-text-muted">
                  Press ↵
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
