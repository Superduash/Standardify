import { Sparkles } from 'lucide-react'

const EXAMPLE_PROMPTS = [
  'What are the microbiological limits in IS 14543?',
  'Which standard applies to electric ceiling fans?',
  'What is the drop test height for packaged drinking water containers?',
  'What are the mandatory marking requirements under IS 374?',
]

/**
 * @param {{ onSelect: (prompt: string) => void, disabled?: boolean }} props
 */
export function ExamplePrompts({ onSelect, disabled }) {
  return (
    <div className="animate-hero-prompts flex flex-col items-center gap-2 sm:flex-row sm:items-baseline sm:justify-center">
      <span className="flex items-center gap-1 font-technical text-[11px] font-medium uppercase tracking-wider text-text-muted shrink-0">
        <Sparkles className="h-3 w-3 text-primary/70" aria-hidden="true" />
        Try asking:
      </span>
      <div className="flex flex-wrap justify-center gap-1.5 sm:gap-2">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(prompt)}
            className="group inline-flex items-center rounded-full border border-border/80 bg-surface px-3 py-1 text-left text-xs text-text-body shadow-2xs transition-all duration-150 ease-out hover:-translate-y-px hover:border-primary/40 hover:bg-primary-light/30 hover:text-primary active:scale-[0.985] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span>{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
