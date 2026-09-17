import { FileCheck2, GitBranch, ShieldAlert } from 'lucide-react'

const PRINCIPLES = [
  {
    icon: FileCheck2,
    title: 'Every answer is cited',
    description:
      'Standard number, clause, and page — shown alongside the answer, not buried in a footnote.',
  },
  {
    icon: ShieldAlert,
    title: 'No evidence, no answer',
    description:
      "If we don't find a confident match in the indexed standards, we say so. We never guess.",
  },
  {
    icon: GitBranch,
    title: 'Status-aware',
    description:
      'Superseded or withdrawn standards are flagged in the answer itself, not left for you to discover later.',
  },
]

export function EvidenceSection() {
  return (
    <section className="border-t border-border bg-surface px-4 py-14 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="text-xl font-semibold text-text sm:text-2xl">
            The source is primary. AI is the assistance layer.
          </h2>
          <p className="mt-2 text-sm text-text-muted sm:text-base">
            Standardify is built to make the underlying standard easier to find and understand —
            not to replace it.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {PRINCIPLES.map(({ icon: Icon, title, description }) => (
            <div key={title} className="flex flex-col items-center text-center sm:items-start sm:text-left">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-teal-light text-teal">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="text-sm font-semibold text-text">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-text-muted">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
