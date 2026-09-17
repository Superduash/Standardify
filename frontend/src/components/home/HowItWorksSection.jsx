import { FileSearch2, MessageCircleQuestion, ShieldCheck } from 'lucide-react'

const STEPS = [
  {
    icon: MessageCircleQuestion,
    step: '01',
    title: 'Ask in plain language',
    description:
      'State your engineering or compliance question naturally — no need to know the specific standard number or clause in advance.',
  },
  {
    icon: FileSearch2,
    step: '02',
    title: 'We retrieve the exact clause',
    description:
      'Standardify executes hybrid dense + keyword search over indexed Indian Standards to isolate the governing clause, table, or amendment.',
  },
  {
    icon: ShieldCheck,
    step: '03',
    title: 'You get a cited, scored answer',
    description:
      'Answers are synthesized strictly from the retrieved evidence, complete with standard number, clause ID, page reference, and confidence score.',
  },
]

export function HowItWorksSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16" aria-labelledby="how-it-works-heading">
      <div className="mx-auto mb-10 max-w-xl text-center">
        <h2 id="how-it-works-heading" className="text-xl font-semibold tracking-tight text-text sm:text-2xl">
          How an answer gets built
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-text-muted sm:text-base">
          Every response is grounded in verified clause text — synthesized strictly from retrieved evidence.
        </p>
      </div>

      <ol className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {STEPS.map(({ icon: Icon, step, title, description }, i) => (
          <li
            key={step}
            className="relative flex flex-col rounded-[var(--radius-lg)] border border-border/80 bg-surface p-5 text-left shadow-2xs transition-all duration-150 ease-out hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-card-hover sm:p-6"
          >
            {/* Header: Icon + Step Badge */}
            <div className="mb-4 flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-primary-light text-primary">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <span className="rounded bg-bg px-2 py-0.5 font-technical text-xs font-semibold text-text-muted border border-border/60">
                STEP {step}
              </span>
            </div>

            {/* Content */}
            <h3 className="text-base font-semibold text-text">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-text-body/90">{description}</p>

            {/* Subtle Connector arrow for large screens */}
            {i < STEPS.length - 1 && (
              <div
                className="pointer-events-none absolute -right-3.5 top-1/2 -translate-y-1/2 hidden md:flex h-7 w-7 items-center justify-center rounded-full border border-border bg-bg text-text-muted text-xs shadow-2xs z-10"
                aria-hidden="true"
              >
                &rarr;
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
