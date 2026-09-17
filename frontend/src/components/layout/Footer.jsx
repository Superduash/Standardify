export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-[var(--radius-sm)] bg-primary text-xs font-semibold text-white">
              S
            </span>
            <span className="text-sm font-medium text-text">Standardify</span>
          </div>
          <p className="max-w-md border-l-2 border-bis-red/60 pl-3 text-xs leading-relaxed text-text-muted">
            An independent, source-cited assistant for Indian Standards — built for SIH26107.
            Not an official <span className="font-technical text-[11px]">BIS</span> product, and answers
            do not constitute certification of compliance.
          </p>
        </div>
        <div className="mt-6 flex flex-col gap-2 border-t border-border pt-4 text-xs text-text-muted sm:flex-row sm:items-center sm:justify-between">
          <span>© {new Date().getFullYear()} Team Trailblazers · SIH26107</span>
          <div className="flex gap-4">
            <a href="https://www.bis.gov.in" target="_blank" rel="noreferrer" className="hover:text-text">
              BIS official site
            </a>
            <a
              href="https://github.com/Superduash/Standardify"
              target="_blank"
              rel="noreferrer"
              className="hover:text-text"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
