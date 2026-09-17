import { FileCheck2, GitBranch, ShieldAlert } from 'lucide-react'

const PRINCIPLES = [
  {
    icon: FileCheck2,
    badge: 'Citations',
    title: 'Every factual claim is cited',
    description:
      'Standard numbers, clause IDs, tables, and page numbers are presented alongside each answer — never hidden in ambiguous footnotes.',
  },
  {
    icon: ShieldAlert,
    badge: 'Groundedness',
    title: 'No evidence, no fabrication',
    description:
      'When indexed standards do not contain relevant clauses, the engine explicitly reports insufficient evidence rather than inventing requirements.',
  },
  {
    icon: GitBranch,
    badge: 'Integrity',
    title: 'Status & lifecycle aware',
    description:
      'Superseded, withdrawn, or amended standards are proactively flagged in the response to prevent outdated compliance decisions.',
  },
]

export function EvidenceSection() {
  return (
    <section className="border-t border-border bg-surface px-4 py-12 sm:px-6 sm:py-16">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <div className="mb-2 inline-flex items-center gap-1 font-technical text-xs font-semibold uppercase tracking-wider text-teal">
            Source &middot; Evidence &middot; Assistance
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-text sm:text-2xl">
            The source is primary. AI is the assistance layer.
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-text-muted sm:text-base">
            Standardify is engineered to make verified Indian Standards easier to locate, cross-reference, and audit — keeping original clause text at the center.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {PRINCIPLES.map(({ icon: Icon, badge, title, description }) => (
            <div
              key={title}
              className="flex flex-col rounded-[var(--radius-lg)] border border-border/80 bg-bg p-5 text-left shadow-2xs transition-all duration-150 ease-out hover:-translate-y-0.5 hover:shadow-card-hover sm:p-6"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-teal-light text-teal">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <span className="font-technical text-[11px] font-semibold uppercase tracking-wider text-teal bg-teal-light/60 px-2 py-0.5 rounded border border-teal/20">
                  {badge}
                </span>
              </div>
              <h3 className="text-base font-semibold text-text">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-body/90">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
