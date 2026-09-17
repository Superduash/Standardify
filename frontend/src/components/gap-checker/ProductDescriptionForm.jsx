import { useRef } from 'react'
import { AlertCircle, ArrowRight, FileCheck, Sparkles, X } from 'lucide-react'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { cn } from '../../lib/utils'

const SAMPLE_PRESETS = [
  {
    label: 'PET Water Bottles',
    text: 'We manufacture 1-liter plastic drinking water bottles from virgin food-grade PET polymer. The containers are intended for packaged drinking water and undergo drop impact resistance and hydrostatic pressure testing.',
  },
  {
    label: 'Electric Ceiling Fans',
    text: 'Electric ceiling fans with 1200mm sweep, 230V 50Hz single phase induction motor, copper winding, and insulated wiring for domestic and commercial installation.',
  },
  {
    label: 'Polymer Food Packaging',
    text: 'Multilayer flexible pouches for packaging pasteurized liquid milk and dairy products, manufactured using co-extruded virgin polyethylene films without pigments or heavy metals.',
  },
]

const SOFT_CHAR_LIMIT = 2000

/**
 * Product description input form with character guidance, rate-limit cooldown, and quick sample presets.
 *
 * @param {{
 *   value: string,
 *   onChange: (val: string) => void,
 *   onSubmit: (val: string) => void,
 *   loading: boolean,
 *   isCoolingDown?: boolean,
 *   cooldownRemaining?: number,
 *   className?: string,
 * }} props
 */
export function ProductDescriptionForm({
  value = '',
  onChange,
  onSubmit,
  loading = false,
  isCoolingDown = false,
  cooldownRemaining = 0,
  className,
}) {
  const textareaRef = useRef(null)
  const charCount = value.length
  const isOverLimit = charCount > SOFT_CHAR_LIMIT
  const isTooShort = value.trim().length > 0 && value.trim().length < 10

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    if (!value.trim() || loading || isCoolingDown) return
    onSubmit(value.trim())
  }

  const handleSelectPreset = (presetText) => {
    onChange(presetText)
    textareaRef.current?.focus()
  }

  const handleClear = () => {
    onChange('')
    textareaRef.current?.focus()
  }

  return (
    <Card className={cn('p-5 sm:p-6 space-y-4 text-left shadow-[var(--shadow-card)]', className)}>
      <form onSubmit={handleSubmit} className="space-y-4" aria-label="Product compliance gap check form">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <label htmlFor="product-description" className="text-sm font-semibold text-text">
            Product Specifications & Material Details
          </label>
          <span
            id="char-count"
            className={cn(
              'font-technical text-xs transition-colors',
              isOverLimit ? 'text-warning font-semibold' : 'text-text-muted'
            )}
          >
            {charCount} / {SOFT_CHAR_LIMIT} chars {isOverLimit && '(soft guidance)'}
          </span>
        </div>

        <div className="relative">
          <textarea
            id="product-description"
            ref={textareaRef}
            rows={5}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={loading || isCoolingDown}
            placeholder="Describe your product, its components, materials used (e.g. virgin food-grade polymer), intended use, and existing testing parameters..."
            aria-describedby="char-count product-form-hint"
            className={cn(
              'w-full resize-y min-h-[120px] rounded-[var(--radius-md)] border border-border bg-bg p-3.5 text-sm text-text placeholder:text-text-muted transition-colors hover:border-primary/50 focus-visible:border-primary focus-visible:bg-surface',
              isOverLimit && 'border-warning/60'
            )}
          />

          {value && !loading && !isCoolingDown && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-3 rounded-full p-1 text-text-muted hover:bg-surface hover:text-text"
              aria-label="Clear product description"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Short warning notice if below 10 chars */}
        {isTooShort && (
          <div className="flex items-center gap-1.5 text-xs text-text-muted" role="status">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-text-muted" aria-hidden="true" />
            <span>
              Please provide at least 10 characters describing the product for reliable clause matching.
            </span>
          </div>
        )}

        {/* Soft warning notice if above 2000 chars */}
        {isOverLimit && (
          <div className="flex items-center gap-1.5 text-xs text-warning" role="status">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>
              Description is detailed. Analysis may take slightly longer, but submission is fully allowed.
            </span>
          </div>
        )}

        {/* Rate limit cooldown notice */}
        {isCoolingDown && (
          <div
            className="flex items-center gap-2 rounded-[var(--radius-md)] border border-amber-300 bg-amber-50 p-3 text-xs text-warning"
            role="status"
            aria-live="polite"
          >
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>
              Rate limit active. Please wait{' '}
              <strong className="font-technical font-bold">{cooldownRemaining}s</strong> before submitting another analysis.
            </span>
          </div>
        )}

        {/* Sample presets */}
        <div className="space-y-1.5 pt-1">
          <p id="product-form-hint" className="text-xs font-medium text-text-muted">
            Or load a sample product specification:
          </p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                disabled={loading || isCoolingDown}
                onClick={() => handleSelectPreset(preset.text)}
                className="rounded-[var(--radius-sm)] border border-border bg-bg px-2.5 py-1 text-xs font-medium text-text-body transition-colors hover:border-primary/40 hover:bg-primary-light/50 hover:text-primary disabled:opacity-50"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Form Action Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-t border-border/60 pt-4">
          <span className="text-xs text-text-muted flex items-center gap-1">
            <Sparkles className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            Deterministic embedding matching against BIS clause repository
          </span>

          <Button
            type="submit"
            size="md"
            loading={loading}
            disabled={loading || !value.trim() || isTooShort || isCoolingDown}
            className="font-semibold shadow-xs"
          >
            {!loading && (
              <>
                <FileCheck className="h-4 w-4" aria-hidden="true" />
                {isCoolingDown ? `Wait (${cooldownRemaining}s)` : 'Analyze Compliance Gaps'}
                {!isCoolingDown && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  )
}
