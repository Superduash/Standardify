import { AskExperience } from '../ask/AskExperience'


export function HeroSection() {
  return (
    <section className="border-b border-border bg-gradient-to-b from-primary-light/50 via-primary-light/20 to-bg px-4 pb-12 pt-10 sm:px-6 sm:pb-14 sm:pt-14">
      <div className="mx-auto max-w-3xl text-center">
        {/* Domain Badge */}
        <div className="animate-hero-badge inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-surface px-3.5 py-1 text-xs font-medium text-primary shadow-2xs">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
          <span>SIH26107 · Indian Standards &amp; BIS Services</span>
        </div>

        {/* Headline */}
        <h1 className="animate-hero-title mt-4 text-3xl font-semibold leading-[1.18] tracking-tight text-text sm:text-4xl lg:text-[2.65rem]">
          Find the right standard.
          <br className="hidden sm:inline" />
          <span className="text-primary-dark"> Understand the exact requirement.</span>
        </h1>

        {/* Supporting Copy */}
        <p className="animate-hero-sub mx-auto mt-3.5 max-w-xl text-sm leading-relaxed text-text-body sm:text-base">
          Ask technical compliance questions and get grounded answers with verified clause,
          table, and page references across Indian Standards.
        </p>

        {/* Primary Ask Workspace */}
        <div className="animate-hero-ask mt-6 sm:mt-7">
          <AskExperience />
        </div>
      </div>
    </section>
  )
}
