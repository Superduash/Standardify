import { Link } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, FileSearch, MessageSquareText, ShieldCheck, Waypoints } from 'lucide-react'

const FEATURES = [
  {
    icon: MessageSquareText,
    title: 'Ask Grounded Q&A',
    description: 'Pose natural-language engineering questions and get answers cited with exact BIS clause IDs.',
    actionText: 'Ask a question',
    to: '/',
  },
  {
    icon: FileSearch,
    title: 'Standards Registry',
    description: 'Filter and inspect active, superseded, or withdrawn standards by domain, standard number, or title.',
    actionText: 'Browse registry',
    to: '/standards',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance Gap Checker',
    description: 'Evaluate technical product specifications against mandatory requirements to flag missing parameters.',
    actionText: 'Run gap analysis',
    to: '/gap-check',
  },
  {
    icon: Waypoints,
    title: 'Relationship Graph',
    description: 'Trace supersession lineages, normative references, and cross-standard dependencies visually.',
    actionText: 'Explore topology',
    to: '/graph',
  },
]

export function FeatureHighlights() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="mx-auto mb-10 max-w-xl text-center">
        <h2 className="text-xl font-semibold tracking-tight text-text sm:text-2xl">
          One workspace, four ways in
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-text-muted sm:text-base">
          Whether starting from an engineering question, a standard number, product specs, or dependency exploration.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, description, actionText, to }) => (
          <Link
            key={title}
            to={to}
            className="group flex flex-col justify-between rounded-[var(--radius-lg)] border border-border/80 bg-surface p-5 shadow-2xs transition-all duration-150 ease-out hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-card-hover active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
          >
            <div>
              <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-primary-light text-primary transition-transform duration-150 group-hover:scale-105">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="flex items-center justify-between text-sm font-semibold text-text group-hover:text-primary transition-colors">
                <span>{title}</span>
                <ArrowUpRight
                  className="h-4 w-4 text-text-muted opacity-60 transition-all duration-150 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary"
                  aria-hidden="true"
                />
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-text-body/85">{description}</p>
            </div>

            <div className="mt-5 border-t border-border/50 pt-3">
              <span className="inline-flex items-center gap-1 font-technical text-xs font-medium text-primary">
                <span>{actionText}</span>
                <ArrowRight className="h-3 w-3 transition-transform duration-150 group-hover:translate-x-1" aria-hidden="true" />
              </span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
