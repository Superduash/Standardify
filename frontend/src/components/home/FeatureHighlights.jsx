import { Link } from 'react-router-dom'
import { ArrowUpRight, FileSearch, MessageSquareText, ShieldCheck, Waypoints } from 'lucide-react'
import { Card, CardDescription, CardTitle } from '../ui/Card'

const FEATURES = [
  {
    icon: MessageSquareText,
    title: 'Ask Grounded Q&A',
    description: 'Plain-language engineering questions answered strictly from indexed Indian Standards with clause citations.',
    to: '/',
  },
  {
    icon: FileSearch,
    title: 'Standards Registry',
    description: 'Search and filter active, superseded, and withdrawn standards by domain, number, or product title.',
    to: '/standards',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance Gap Checker',
    description: 'Evaluate product specifications against mandatory BIS requirements to detect satisfied and missing clauses.',
    to: '/gap-check',
  },
  {
    icon: Waypoints,
    title: 'Relationship Graph',
    description: 'Explore multi-hop supersession trees, norm references, and domain connections across Indian Standards.',
    to: '/graph',
  },
]

export function FeatureHighlights() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
      <div className="mx-auto mb-8 max-w-xl text-center">
        <h2 className="text-xl font-semibold text-text sm:text-2xl">
          One workspace, four ways in
        </h2>
        <p className="mt-2 text-sm text-text-muted sm:text-base">
          Whichever way you approach a standard, every answer is grounded in the same indexed
          source text.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, description, to }) => (
          <Link key={title} to={to} className="group block">
            <Card className="h-full transition-shadow duration-150 group-hover:shadow-[var(--shadow-card-hover)]">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-primary-light text-primary">
                <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
              </div>
              <CardTitle className="flex items-center gap-1">
                {title}
                <ArrowUpRight
                  className="h-3.5 w-3.5 text-text-muted opacity-0 transition-opacity group-hover:opacity-100"
                  aria-hidden="true"
                />
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  )
}
