import { FileSearch2, MessageCircleQuestion, ShieldCheck } from 'lucide-react'

const STEPS = [
  {
    icon: MessageCircleQuestion,
    step: '01',
    title: 'Ask in plain language',
    description: 'Type a question the way you\u2019d ask a colleague — no need to know the standard number first.',
  },
  {
    icon: FileSearch2,
    step: '02',
    title: 'We retrieve the exact clause',
    description: 'Standardify searches indexed Indian Standards and pulls the specific clause your question depends on.',
  },
  {
    icon: ShieldCheck,
    step: '03',
    title: 'You get a cited, scored answer',
    description: 'The answer is generated only from what was retrieved, with the standard, clause, page, and a confidence score attached.',
  },
]

export function HowItWorksSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6" aria-labelledby="how-it-works-heading">
      <div className="mx-auto mb-10 max-w-xl text-center">
        <h2 id="how-it-works-heading" className="text-xl font-semibold text-text sm:text-2xl">
          How an answer gets built
        </h2>
        <p className="mt-2 text-sm text-text-muted sm:text-base">
          Nothing here is generated from memory — every step is grounded in an indexed source.
        </p>
      </div>

      <ol className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {STEPS.map(({ icon: Icon, step, title, description }, i) => (
          <li key={step} className="relative flex flex-col items-center text-center sm:items-start sm:text-left">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-primary text-white">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <span className="font-technical text-sm text-text-muted">{step}</span>
            </div>
            <h3 className="text-sm font-semibold text-text">{title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-text-muted">{description}</p>

            {i < STEPS.length - 1 && (
              <div
                className="absolute right-[-12px] top-5 hidden h-px w-6 bg-border sm:block"
                aria-hidden="true"
              />
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
