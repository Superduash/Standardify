import { AskExperience } from '../ask/AskExperience'


export function HeroSection() {
  return (
    <section className="border-b border-border bg-gradient-to-b from-primary-light/60 to-bg px-4 pb-14 pt-16 sm:px-6 sm:pt-20">
      <div className="mx-auto max-w-3xl text-center">
        <span className="inline-flex items-center rounded-full border border-primary/20 bg-surface px-3 py-1 text-xs font-medium text-primary">
          SIH26107 · Indian Standards & BIS Services
        </span>

        <h1 className="mt-5 text-3xl font-semibold leading-tight text-text sm:text-4xl md:text-5xl">
          Find the right standard.
          <br />
          Understand the exact requirement.
        </h1>

        <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-text-body sm:text-lg">
          Ask questions about Indian Standards and get source-backed answers with clause and
          page references.
        </p>

        <div className="mt-8">
          <AskExperience />
        </div>
      </div>
    </section>
  )
}
