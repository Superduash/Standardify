const EXAMPLE_PROMPTS = [
  'What are the microbiological requirements for packaged drinking water?',
  'Which standard applies to ceiling fans?',
  'What is the drop test height for plastic water bottles?',
  'What are the key safety requirements under IS 374?',
]

/**
 * @param {{ onSelect: (prompt: string) => void, disabled?: boolean }} props
 */
export function ExamplePrompts({ onSelect, disabled }) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {EXAMPLE_PROMPTS.map((prompt) => (
        <button
          key={prompt}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(prompt)}
          className="rounded-full border border-border bg-surface px-3.5 py-1.5 text-left text-xs font-medium text-text-body transition-colors hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-50 sm:text-sm"
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}
