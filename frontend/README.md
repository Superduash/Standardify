# Standardify — Frontend

React + Tailwind CSS frontend for **Standardify**, Team Trailblazers' entry for **SIH26107**
(AI-powered Intelligent Assistant for Indian Standards and BIS Services).

This is the frontend foundation + Home page (Frontend Phase 0). See `frontendplan.md` for the
full plan — backend contract mapping, locked folder structure, and the phased roadmap for the
remaining pages (Standards Search, Standard Detail, Gap Checker, Relationship Graph).

## Stack

- React 19 + Vite
- Tailwind CSS v4 (`@tailwindcss/vite`, CSS-first `@theme` config — see `src/index.css`)
- React Router
- Axios
- IBM Plex Sans / IBM Plex Mono, self-hosted via `@fontsource`
- lucide-react for icons

No state management library — see `frontendplan.md` §4 for why.

## Getting started

```bash
npm install
cp .env.example .env        # point VITE_API_BASE_URL at your running backend
npm run dev
```

The app expects a running Standardify backend (see `backendplan.md` in the backend repo) at
whatever `VITE_API_BASE_URL` points to. Without one running, the Ask box will correctly show a
network-error toast and an inline retry state — that's expected behavior, not a bug: the frontend
always makes a real request and handles the real failure mode rather than faking a response.

## Scripts

- `npm run dev` — local dev server
- `npm run build` — production build to `dist/`
- `npm run preview` — preview the production build locally
- `npm run lint` — oxlint

## Project structure

See `frontendplan.md` §3 for the full locked folder structure and the reasoning behind it.

## Deployment

Static build (`npm run build` → `dist/`), deployable to Vercel per the project's tech stack. The
only required environment variable is `VITE_API_BASE_URL`, pointed at the deployed backend.
