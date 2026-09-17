import { Link } from 'react-router-dom'
import { ArrowLeft, Construction } from 'lucide-react'
import { buttonClasses } from '../components/ui/Button'

/**
 * Honest "coming next" page for routes whose feature isn't built yet in
 * this phase (see frontendplan.md §8). Real navigation, real content about
 * what's coming — never a broken link, never fake data.
 * @param {{ title: string, description: string, phase: string }} props
 */
export function PlaceholderPage({ title, description, phase }) {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center px-4 py-16 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary-light text-primary">
        <Construction className="h-5 w-5" aria-hidden="true" />
      </div>
      <h1 className="text-xl font-semibold text-text">{title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-text-muted">{description}</p>
      <p className="mt-1 font-technical text-xs text-text-muted">{phase}</p>
      <Link to="/" className={buttonClasses({ variant: 'secondary', size: 'sm', className: 'mt-6' })}>
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
        Back to Ask
      </Link>
    </div>
  )
}

export default PlaceholderPage
