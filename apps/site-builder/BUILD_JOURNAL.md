# Site Builder: Build Journal

How the Clarity Framework was used to build a full-stack AI site generator in roughly 8 hours.

**What was built:** Paste a Google Maps URL, get a deployed React website in 60 seconds. 7-step async pipeline, 13-section inline editor, deployed to Cloudflare Pages.

**Stack:** FastAPI + Vue 3 + React 18 + Claude Sonnet + Gemini Flash + Playwright

**Source:** [github.com/spotcircuit/site-builder](https://github.com/spotcircuit/site-builder)

---

## Hour 1-2: Discovery & Architecture

### Creating the app entry

```
> /se:create site-builder
```

This created the `apps/site-builder/` directory and prompted for the `app.yaml` config. The key decisions went in here -- not in a design doc, not in a Slack thread, in the structured config:

```yaml
# apps/site-builder/app.yaml
app:
  name: site-builder
  type: tool

codebase:
  framework: FastAPI (backend) + Vue 3 (frontend) + React 18 (generated sites)

environment:
  dev:
    ports:
      backend: 9405
      frontend: 5177
  prod:
    backend: Railway
    frontend: Vercel

goal: >
  Search any business on Google Maps, get a premium React website in 60 seconds.
  Scrape listing, generate AI content with Claude, build React + Tailwind site,
  deploy to Cloudflare Pages, provide inline editor for customization.

dependencies:
  - "ANTHROPIC_API_KEY (Claude content generation)"
  - "GEMINI_API_KEY (image generation, optional)"
  - "CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID (deployment)"
  - "VITE_GOOGLE_MAPS_API_KEY (Places autocomplete)"
```

Every dependency is listed. Every port is declared. If someone picks this project up cold, they know what they need before reading a single line of code.

### Running discover

```
> /se:discover site-builder
```

Since this is an internal app (not a client with Jira/Slack/tenant), `/discover` adapted. It scanned the codebase path, read the existing README and source files, and generated the Phase 0 document. Output looked like:

```
Clarity Discover: site-builder

Sources Queried:
  Jira:    -- N/A (internal app)
  Slack:   -- N/A (internal app)
  Tenant:  -- N/A (internal app)
  Code:    Found -- FastAPI + Vue 3 + React 18

Phase 0 Document: apps/site-builder/phase-0-discovery.md
  Fields auto-filled:       14
  Fields requiring input:    3

Expertise File: apps/site-builder/expertise.yaml
  Architecture: seeded from codebase scan
  Pipeline: 7 steps identified from modules/
  Known issues: 0 (fresh build)
```

The Phase 0 doc captured the architecture before a single feature was complete. This matters because by hour 4, the architecture had already evolved twice -- and without the Phase 0 baseline, those decisions would have been invisible.

### Initial expertise.yaml

At this point, expertise.yaml was skeletal:

```yaml
app: site-builder
last_updated: 2026-04-07

architecture:
  frontend: Vue 3 + TypeScript + Pinia + Tailwind CSS
  backend: FastAPI + Python 3.13 + asyncio
  generated_sites: React 18 + Tailwind CSS (Vite build)

pipeline:
  steps: []  # not built yet

unvalidated_observations:
  - "Initial discover run -- codebase scaffolded, no pipeline modules yet (2026-04-07)"
  - "Decision: Claude for content, Gemini for images -- Claude better at structured JSON, Gemini better at on-brand imagery"
  - "Decision: Cloudflare Pages primary deploy, Vercel fallback -- CF has faster edge propagation"
```

Three observations sitting in the unvalidated queue. The framework doesn't pretend decisions are facts -- they sit in `unvalidated_observations` until `/improve` can verify them against reality.

---

## Hour 3-4: Core Pipeline

### The 7 steps

Each pipeline module was built individually and tested in isolation. The async pipeline looks like this in the backend:

```
Parse URL -> Scrape Maps -> Scrape Website -> Generate Content -> Generate Images -> Build Site -> Deploy
```

The modules, in order:

| Step | Module | Lines | What it does |
|------|--------|-------|-------------|
| 1 | `maps_url_parser.py` | 293 | Parses Google Maps URLs, extracts place ID, handles 15+ URL formats |
| 2 | `maps_scraper.py` | 1137 | Playwright browser scraping of the full business listing |
| 3 | `website_scraper.py` | 475 | Optionally scrapes the business's own website for extra content |
| 4 | `site_generator.py` | 1039 | Claude generates structured JSON content for all 13 sections |
| 5 | `image_generator.py` | 302 | Gemini generates hero + section images matching the business |
| 6 | `react_builder.py` | 471 | Assembles React components, injects content, runs `npm build` |
| 7 | `cloudflare_deployer.py` | 258 | Deploys dist/ to Cloudflare Pages via wrangler CLI |

### What /improve caught

After building the scraper and content generator, observations were piling up. Running `/improve` processed them:

```
> /se:improve site-builder

Self-Improve: site-builder

Observations processed: 7
  Confirmed + integrated: 5
  Stale + discarded:      1
  Left unverified:        1

expertise.yaml: 38 lines / 1000

Integrated into:
  - architecture: added ai_content and ai_images model names
  - pipeline: populated all 7 steps with module names
  - unvalidated: kept "Cloudflare has 100 project limit" for verification
```

Here is what that actually looked like. Before `/improve`:

```yaml
unvalidated_observations:
  - "Google Maps scraper needs Playwright -- headless Chrome required for JS-rendered content"
  - "Maps URL has 15+ formats: /maps/place/, /maps?cid=, shortened goo.gl, place_id param, etc."
  - "Claude returns markdown in JSON strings sometimes -- need post-processing to strip ```json fences"
  - "Gemini 2.5 Flash can generate images -- cheaper than DALL-E, good enough for hero sections"
  - "Cloudflare Pages has a 100 project limit per account -- need auto-cleanup"
  - "Website scraping is optional -- many small businesses don't have websites"
  - "React build takes 8-12 seconds locally -- acceptable for 60-second target"
```

After `/improve` promoted confirmed observations:

```yaml
architecture:
  ai_content: Claude Sonnet (claude-sonnet-4-20250514)
  ai_images: Gemini 2.5 Flash Image

pipeline:
  steps:
    - parsing_url: maps_url_parser.py
    - scraping_profile: maps_scraper.py (Playwright)
    - scraping_website: website_scraper.py (optional)    # <-- "optional" came from observation
    - generating_content: site_generator.py (Claude)
    - generating_images: image_generator.py (Gemini)
    - building_site: react_builder.py (npm build)
    - deploying: cloudflare_deployer.py / vercel_deployer.py

deployment:
  cloudflare_limit: auto-deletes oldest project when limit hit  # <-- promoted from observation

unvalidated_observations:
  - "React build takes 8-12 seconds locally -- need to verify in Railway container"
```

Six observations became structured knowledge. One stayed unvalidated because it hadn't been tested in production yet. The Cloudflare 100-project limit became a documented deployment constraint with its mitigation (auto-delete oldest) baked right into the expertise file.

### The gotchas that would have been lost

Without the framework, these would have been forgotten by the next session:

- **Maps URL parsing:** Google Maps has at least 15 URL formats. The parser handles `/maps/place/`, `/maps?cid=`, `goo.gl` shortlinks, bare place IDs, `@lat,lng` coordinates, and the new `/maps/search/` format. This was a full day of edge cases compressed into one module.

- **Claude JSON fencing:** Claude sometimes wraps JSON responses in triple-backtick markdown fences even when told not to. The content generator strips these automatically. This got captured as an observation, confirmed through testing, and promoted into the architecture notes.

- **Playwright async patterns:** Maps scraping requires waiting for specific DOM elements that load after multiple JS re-renders. The scraper uses a custom wait strategy, not just `page.wait_for_load_state("networkidle")` -- because Google Maps never truly reaches network idle.

---

## Hour 5-6: Editor & Frontend

### The 13-section editor

The inline editor lets users customize every section of the generated site before deploying. Each section maps to a React component:

```
Hero, About, Services, Gallery, CTA, FAQ, Testimonials,
Why Choose Us, How It Works, Contact, Design, SEO, Visibility
```

The Vue frontend uses Pinia for state management. The store (`siteBuilderStore.ts`) handles the full lifecycle: input -> progress tracking via WebSocket -> result display -> editing -> rebuild -> redeploy.

### What /improve caught this time

```
> /se:improve site-builder

Self-Improve: site-builder

Observations processed: 4
  Confirmed + integrated: 4
  Stale + discarded:      0

Integrated into:
  - editor: sections list, feature list
  - editor: dirty detection mechanism documented
```

The observations that got promoted:

```yaml
# Before (unvalidated)
unvalidated_observations:
  - "Dirty detection uses JSON.stringify comparison of current vs saved content"
  - "Device preview: desktop/tablet/mobile iframe widths with transition animation"
  - "Theme system: 5 presets (Modern, Classic, Bold, Minimal, Elegant) apply via CSS variables"
  - "AI regeneration: can regenerate individual sections via Claude without rebuilding whole site"

# After (structured)
editor:
  sections: 13 (Hero, About, Services, Gallery, CTA, FAQ, Testimonials,
                 Why Choose Us, How It Works, Contact, Design, SEO, Visibility)
  features:
    - live iframe preview with device switching
    - AI section regeneration via Claude
    - theme presets (Modern, Classic, Bold, Minimal, Elegant)
    - dirty detection via JSON comparison
    - quick preview vs full rebuild vs redeploy
```

The dirty detection detail matters. It's not obvious that JSON comparison is the mechanism -- a future developer might try to implement deep object comparison or a diff library. The expertise file records the actual implementation decision.

---

## Hour 7: Testing

### ACT-LEARN-REUSE

The test suite uses a self-improving pattern:

1. **ACT** -- Run all tests, collect results
2. **LEARN** -- Analyze failures, identify patterns
3. **REUSE** -- Update expertise with test patterns so future test runs are informed

98 tests across 4 layers:

| Layer | Framework | Tests | What they cover |
|-------|-----------|-------|----------------|
| Backend unit | pytest + httpx | 33 | API endpoints, Pydantic models, pipeline modules |
| Frontend store | Vitest | 33 | Pinia store actions, state transitions, WebSocket handling |
| E2E smoke | Playwright | 21 | Full UI flow without hitting external APIs |
| E2E full gen | Playwright | 11 | Full pipeline including real API calls (~5 min) |

After the test suite was solid:

```
> /se:improve site-builder

Self-Improve: site-builder

Observations processed: 3
  Confirmed + integrated: 3

Integrated into:
  - testing: test counts and frameworks per layer
  - testing: pattern name (ACT-LEARN-REUSE)
```

```yaml
# Promoted to structured testing section
testing:
  backend_unit: 33 tests (pytest + httpx)
  frontend_store: 33 tests (vitest)
  e2e_smoke: 21 tests (Playwright)
  e2e_full_gen: 11 tests (Playwright, ~5 min)
  pattern: ACT-LEARN-REUSE (self-improving)
```

---

## Hour 8: Deployment & Polish

### The deployment chain

Three platforms, one sync mechanism:

```
Monorepo (agent-experts/apps/site_builder/)
    |
    | GitHub Action (on push to main)
    v
Standalone repo (spotcircuit/site-builder)
    |
    +----> Railway (auto-deploy backend)
    +----> Vercel (auto-deploy frontend)
```

Generated sites deploy to Cloudflare Pages (primary) or Vercel (fallback).

The GitHub Action extracts just the `apps/site_builder/` subtree and pushes it to the standalone repo. Railway and Vercel watch that repo and auto-deploy on push.

### Final /improve and /brief

```
> /se:improve site-builder

Self-Improve: site-builder

Observations processed: 2
  Confirmed + integrated: 2

Integrated into:
  - deployment: Railway + Vercel + sync mechanism
  - deployment: cloudflare auto-cleanup on limit
```

```
> /se:brief site-builder

--- Site Builder Brief ---

Status: Deployed and functional
Backend: Railway (auto-deploy from standalone repo)
Frontend: Vercel (auto-deploy from standalone repo)

Architecture: FastAPI + Vue 3 + React 18
AI: Claude Sonnet (content) + Gemini Flash (images)
Pipeline: 7 async steps, URL to deployed site in ~60 seconds

Editor: 13 sections, 5 themes, live preview, AI regeneration
Testing: 98 tests (33 backend + 33 frontend + 21 E2E smoke + 11 E2E full)

Open questions:
  - Revenue model: demo tool vs productized service?
  - Expert system migration: move .claude/commands/experts/ into Clarity?
  - Orchestrator cleanup: pre-Paperclip code still in monorepo
```

The brief pulls everything from expertise.yaml and notes.md. No digging through code, no checking deployment dashboards. One command, full project status.

---

## The Final expertise.yaml

After 8 hours and roughly 5 `/improve` cycles, the expertise file went from empty to this:

```yaml
app: site-builder
last_updated: 2026-04-08

architecture:
  frontend: Vue 3 + TypeScript + Pinia + Tailwind CSS
  backend: FastAPI + Python 3.13 + asyncio
  generated_sites: React 18 + Tailwind CSS (Vite build)
  ai_content: Claude Sonnet (claude-sonnet-4-20250514)
  ai_images: Gemini 2.5 Flash Image
  deploy_primary: Cloudflare Pages (wrangler CLI)
  deploy_fallback: Vercel REST API
  realtime: WebSocket (/ws)

pipeline:
  steps:
    - parsing_url: maps_url_parser.py
    - scraping_profile: maps_scraper.py (Playwright)
    - scraping_website: website_scraper.py (optional)
    - generating_content: site_generator.py (Claude)
    - generating_images: image_generator.py (Gemini)
    - building_site: react_builder.py (npm build)
    - deploying: cloudflare_deployer.py / vercel_deployer.py

testing:
  backend_unit: 33 tests (pytest + httpx)
  frontend_store: 33 tests (vitest)
  e2e_smoke: 21 tests (Playwright)
  e2e_full_gen: 11 tests (Playwright, ~5 min)
  pattern: ACT-LEARN-REUSE (self-improving)

editor:
  sections: 13 (Hero, About, Services, Gallery, CTA, FAQ, Testimonials,
                 Why Choose Us, How It Works, Contact, Design, SEO, Visibility)
  features:
    - live iframe preview with device switching
    - AI section regeneration via Claude
    - theme presets (Modern, Classic, Bold, Minimal, Elegant)
    - dirty detection via JSON comparison
    - quick preview vs full rebuild vs redeploy

deployment:
  backend: Railway (auto-deploy from standalone repo)
  frontend: Vercel (auto-deploy from standalone repo)
  sync: GitHub Action syncs monorepo -> standalone repo on push to main
  cloudflare_limit: auto-deletes oldest project when limit hit

unvalidated_observations: []
```

46 lines. Every section populated. Zero unvalidated observations remaining. A new developer reading this file knows the full system in 2 minutes.

---

## Key Takeaways

### What the framework caught that would have been lost

1. **The Cloudflare 100-project limit.** Discovered during hour 4, would have been a production outage weeks later. Instead it became a deployment constraint with auto-cleanup built in.

2. **Claude's JSON fencing behavior.** An LLM quirk that causes silent content corruption. Caught during content generation testing, promoted to architecture knowledge.

3. **Google Maps URL format diversity.** 15+ formats. Without structured capture, the next person to touch the parser would rediscover each format one support ticket at a time.

4. **The "optional" annotation on website scraping.** A small word in the pipeline config that prevents someone from treating a scraping failure as a pipeline failure. Many small businesses simply don't have websites.

### How expertise.yaml grew

```
Hour 1:  3 lines   (app name + date + empty sections)
Hour 2:  12 lines  (architecture seeded by /discover)
Hour 4:  28 lines  (pipeline + deployment after /improve)
Hour 6:  38 lines  (editor section after /improve)
Hour 7:  42 lines  (testing section after /improve)
Hour 8:  46 lines  (deployment finalized, observations cleared)
```

The file grew only when observations were confirmed. It never contained speculation. Every line was validated against the running system.

### The self-learn loop in practice

The pattern that emerged:

1. **Build something** -- write code, hit a wall, find a workaround
2. **Observation gets appended** -- the workaround or gotcha goes into `unvalidated_observations`
3. **Run /improve** -- observations get checked against reality
4. **Confirmed facts get promoted** -- they move from the unvalidated queue into structured sections
5. **Stale observations get discarded** -- things that were true during development but not in production

This is the opposite of documentation-first. You don't stop building to write docs. The framework captures knowledge as a side effect of working, then structures it later. The expertise file is always accurate because it only contains things that have been verified.

The build took 8 hours. The expertise file took zero additional hours -- it was a byproduct of the process.
