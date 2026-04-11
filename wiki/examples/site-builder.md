# Site Builder

A working product built across four Claude Code sessions (~8 hours total) using the Clarity Framework to accumulate context between them. Search any business on Google Maps, get a deployed React website in 60 seconds.

## What the framework produced

By the end of four sessions, `expertise.yaml` contained a complete operational reference: architecture, a 7-step async pipeline, 16 API endpoints, 16 editor sections, 142 tests, deployment config, 10 API gotchas, and 10 architectural decisions. Nobody sat down and wrote documentation -- it accumulated through the build process.

## Architecture (from expertise.yaml)

```
Frontend:  Vue 3 + TypeScript + Pinia + Tailwind CSS (Vercel)
Backend:   FastAPI + Python 3.13 + asyncio (Railway)
Generated: React 18 + Tailwind CSS (Cloudflare Pages)
AI:        Claude Sonnet (content) + Gemini 2.5 Flash (images)
Realtime:  WebSocket for pipeline progress
```

## The pipeline

Seven async steps, each broadcasting progress via WebSocket. Full generation takes ~60 seconds.

| Step | Module | What it does |
|------|--------|-------------|
| 1 | maps_url_parser.py | Parse Google Maps URL to extract place ID |
| 2 | maps_scraper.py | Headless Playwright, extract business data (name, hours, reviews, photos) |
| 3 | website_scraper.py | Scrape business website for supplementary content (optional) |
| 4 | site_generator.py | Send scraped data to Claude Sonnet, get structured website content |
| 5 | image_generator.py | Generate visuals via Gemini 2.5 Flash (skipped if no API key) |
| 6 | react_builder.py | Copy React template, inject data.json, run Vite build |
| 7 | cloudflare_deployer.py | Deploy static dist/ to Cloudflare Pages (or Vercel fallback) |

## How expertise grew session by session

**Session 1 (3 hours)** -- Built the first 4-step pipeline. First end-to-end generation worked on attempt 3. Generated content was generic ("Welcome to [Business Name], your trusted partner..."). The framework captured 5 observations. `/improve` promoted 3, deferred 2.

**Session 2 (2.5 hours)** -- Started with `/brief`, which told the AI exactly where things stood and what to focus on. Added website scraper (the unlock for content quality -- sites now sound like the business). Added Gemini image generation. Lost 45 minutes to Google Maps cookie consent interstitial, fixed with playwright-stealth. `/improve` promoted 3 observations, discarded 1 that was already fixed.

**Session 3 (1.5 hours)** -- Built a 13-section inline editor with live iframe preview, AI section regeneration, 5 theme presets, and dirty detection. `/improve` promoted 3 observations, discarded 1 stale one.

**Session 4 (1 hour)** -- 142 tests across 4 layers. Deployment to Railway + Vercel + Cloudflare Pages. One test caught a real bug: redeploy button enabled before rebuild. Framework overhead across all sessions: ~30 minutes.

## Real API gotchas (from expertise.yaml)

These accumulated through the build process, not through documentation sessions:

- Google Maps selectors change frequently. `maps_scraper.py` has 1141 lines of CSS selectors. When Google changes markup, scraping breaks silently (empty fields, not errors).
- Playwright browser must be installed separately. `pip install playwright` does NOT install browser binaries.
- Cloudflare Pages project names must be lowercase alphanumeric with hyphens only. Business names with special characters get sanitized, which can cause collisions.
- `generate-section` only accepts specific section_type values: services, faq_items, testimonials, why_choose_us, process_steps.
- Job storage is in-memory only. All jobs lost on server restart. By design -- sites are deployed and done.

## Key decision captured

> **React for generated sites, Vue for the builder frontend.**
> React sites are standalone deliverables (client gets a React project). Vue is for the builder tool itself -- keeps concerns separate.

## Related

- [Acme Integration](acme-integration.md) -- Different project type (enterprise integration), same framework patterns
- [The Self-Learn Loop](../how-it-works/self-learn-loop.md) -- How observations became promoted facts
- [Commands](../how-it-works/commands.md) -- The commands used throughout build sessions
