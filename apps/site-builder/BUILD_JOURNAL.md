# Site Builder — Build Journal

How a working product was built across four Claude Code sessions using the Clarity framework to accumulate context between them.

This is raw. Some things broke. The framework caught those breakages and turned them into knowledge.

---

## Session 1 — Foundation (Day 1, ~3 hours)

### Bootstrapping

Started with `/create site-builder`. Clarity prompted for the basics:

```
> App name: site-builder
> One-line purpose: Generate and deploy business websites from a Google Maps URL
> Tech stack (frontend): Vue 3 + TypeScript
> Tech stack (backend): FastAPI + Python
> Status: building
```

Created `apps/site-builder/app.yaml`. Mostly empty at this point — just the scaffold.

Ran `/discover site-builder`. Phase 0 came back with a reasonable decomposition:

```
Phase 0 identified:
  - URL parsing (extract place_id from Maps URLs)
  - Data scraping (business name, address, hours, reviews, photos)
  - Content generation (Claude, section-by-section)
  - Static site output (React + Tailwind, Vite build)
  - Deploy target TBD
```

### First pipeline

Built four files:
- `maps_url_parser.py` — regex for the 4 different Maps URL formats (short links, search results, place links, CID links)
- `maps_scraper.py` — Playwright, navigate to the listing, pull structured data
- `site_generator.py` — prompt Claude with business data, get back section content
- `react_builder.py` — template React app, inject content, `npm run build`

First end-to-end generation worked on attempt #3. The first two failures:

1. Maps URL parser didn't handle the `maps/place/` format with `!3d` latitude embedded. Had to add a second regex path.
2. Claude returned markdown in the hero section (### headings, **bold**) which broke the React template. Added a post-processing strip.

The generated site rendered. But it was... bad. Generic small business copy. "Welcome to [Business Name], your trusted partner in [industry]." Zero personality.

### expertise.yaml after Session 1

```yaml
app: site-builder
last_updated: 2026-04-05

architecture:
  frontend: Vue 3 + TypeScript
  backend: FastAPI + Python 3.13
  ai_content: Claude Sonnet (claude-sonnet-4-20250514)

pipeline:
  steps:
    - parsing_url: maps_url_parser.py
    - scraping_profile: maps_scraper.py (Playwright)
    - generating_content: site_generator.py (Claude)
    - building_site: react_builder.py (npm build)

unvalidated_observations:
  - "Maps URL parser fails on !3d-embedded lat/lng format — fixed, needs more format testing"
  - "Claude returns markdown formatting in content sections — strip_markdown post-processor added"
  - "Generated content is generic, reads like template fill-in-the-blank. Needs richer business context."
  - "Reviews contain the real voice of the business — should feed top reviews into content prompt"
  - "No image generation yet — hero section looks empty without a banner"
```

Ran `/improve`:

```
/improve site-builder

Reviewing 5 unvalidated observations...

✓ PROMOTED: "Maps URL parser fails on !3d-embedded lat/lng format"
  → Added to pipeline.known_issues
  Reason: Confirmed in maps_url_parser.py, regex updated to handle 4 URL formats.

✓ PROMOTED: "Claude returns markdown formatting in content sections"
  → Added to pipeline.known_issues
  Reason: strip_markdown() exists in site_generator.py, confirmed behavior.

✓ PROMOTED: "Generated content is generic — needs richer business context"
  → Added to architecture notes
  Reason: Verified. Prompt only receives name + address + category. Reviews, services
  list, and website copy are not included. This is the #1 quality bottleneck.

○ DEFERRED: "Reviews contain real voice — should feed into content prompt"
  Reason: Not implemented yet. Keeping as observation until scraper captures reviews.

○ DEFERRED: "No image generation yet"
  Reason: Not implemented. Keeping as observation.

3 promoted, 0 discarded, 2 deferred.
```

---

## Session 2 — Pipeline Hardening (Day 2, ~2.5 hours)

### The scraper fight

Opened the session. Ran `/brief site-builder`:

```
/brief site-builder

Site Builder — Briefing
━━━━━━━━━━━━━━━━━━━━━━
Status: Building (Day 2)
Pipeline: 4 steps, URL→Scrape→Generate→Build
Key gap: Content quality (generic output)
Unvalidated: 2 deferred observations (reviews, images)
Next priority: Enrich business data before generation step

Suggested focus:
  1. Add review scraping to maps_scraper.py
  2. Consider website scraping as supplementary data source
  3. Image generation for hero/gallery sections
```

Good brief. Started on review scraping immediately.

Then the scraper started failing. Google Maps had started returning a cookie consent interstitial that wasn't there yesterday. Playwright would click "Accept All" but the page would reload into a different layout.

Tried three approaches:
1. **Wait for selector** — flaky. The consent button has dynamic class names.
2. **Set cookies beforehand** — worked for one run, then Google rotated the consent cookie format.
3. **Playwright stealth plugin** — `playwright-stealth`. This was the fix. Patches the navigator object, WebGL fingerprint, etc. Maps loads cleanly.

Lost about 45 minutes to this. But the framework captured it.

### Website scraper

Added `website_scraper.py` as an optional enrichment step. If the Maps listing has a website URL, we scrape it for:
- Services/products mentioned
- About page copy
- Any testimonials or review snippets
- Color scheme (pulls primary/secondary from CSS custom properties)

This was the unlock for content quality. The Claude prompt now receives:

```
Business: {name}
Category: {category}
Address: {address}
Hours: {hours}
Rating: {rating} ({review_count} reviews)
Top Reviews: {top_5_reviews}
Services Found: {services_from_website}
About Copy: {about_text_from_website}
```

Night and day difference in generated content. The sites actually sounded like the business.

### Image generation

Added Gemini 2.5 Flash for image generation. First attempt used complex scene descriptions and Gemini would timeout at the default 10-second limit. Bumped to 30 seconds with retry logic (exponential backoff, max 3 attempts).

Even at 30s, about 15% of generations fail on the first attempt. The retry handles it. Added a fallback to gradient placeholder images so the build never blocks on image generation.

### expertise.yaml after Session 2

```yaml
app: site-builder
last_updated: 2026-04-06

architecture:
  frontend: Vue 3 + TypeScript
  backend: FastAPI + Python 3.13 + asyncio
  ai_content: Claude Sonnet (claude-sonnet-4-20250514)
  ai_images: Gemini 2.5 Flash Image
  deploy_primary: TBD

pipeline:
  steps:
    - parsing_url: maps_url_parser.py
    - scraping_profile: maps_scraper.py (Playwright + stealth)
    - scraping_website: website_scraper.py (optional)
    - generating_content: site_generator.py (Claude)
    - generating_images: image_generator.py (Gemini)
    - building_site: react_builder.py (npm build)
  known_issues:
    - "Maps URL parser: 4 URL formats handled, may be more edge cases"
    - "Claude markdown in output: strip_markdown post-processor handles this"
    - "Google Maps blocks headless Chrome without stealth plugin"
    - "Gemini timeouts on complex prompts — 30s timeout + retry (3 attempts)"

scraping:
  maps_data: name, category, address, hours, rating, review_count, top_reviews, photos, website_url
  website_data: services, about_text, testimonials, color_scheme
  stealth: playwright-stealth required (consent interstitial + bot detection)

unvalidated_observations:
  - "Website scraper color extraction is brittle — only works with CSS custom properties, not inline styles"
  - "Gemini prompt for hero images works best with simple subject descriptions, not scene compositions"
  - "WebSocket progress reporting would be useful — generation takes 45-90 seconds"
  - "Need to handle Maps listings with no website URL gracefully (skip website scraper, don't error)"
```

Ran `/improve`:

```
/improve site-builder

Reviewing 4 unvalidated observations...

✓ PROMOTED: "Website scraper color extraction is brittle"
  → Added to scraping.known_limitations
  Reason: Confirmed. Only checks :root and body CSS custom properties.
  Many sites use Tailwind classes or inline hex — these are missed.

✓ PROMOTED: "Gemini hero images: simple subjects > scene compositions"
  → Added to pipeline.ai_images notes
  Reason: Confirmed via testing. "A modern plumbing company" generates better
  than "An aerial view of a plumbing van parked outside a suburban home at golden hour."

✓ PROMOTED: "Need to handle Maps listings with no website URL"
  → Added to pipeline.steps (website scraper now correctly marked "optional")
  Reason: Confirmed. Added conditional skip in orchestrator.

○ DISCARDED: "WebSocket progress reporting would be useful"
  Reason: Already implemented. ws_manager.py sends stage-by-stage progress.
  This observation was stale — written before the WebSocket endpoint was added
  later in the same session.

3 promoted, 1 discarded, 0 deferred.
```

The discarded observation is a good example. I added WebSocket progress later in the session but had written the observation earlier. `/improve` caught that it was already done.

---

## Session 3 — Editor (Day 3, ~1.5 hours)

### The problem

Generated sites were good, but every business wants to tweak "just a few things." Running the whole pipeline again for a word change is wasteful (45-90 second generation, API costs). Needed an inline editor.

### 13-section editor

Built the editor panel in Vue with 13 collapsible sections:

| # | Section | Editable Fields |
|---|---------|----------------|
| 1 | Hero | headline, subheadline, CTA text, CTA link, background image |
| 2 | About | title, body text, image |
| 3 | Services | list of {name, description, icon} |
| 4 | Gallery | list of images with captions |
| 5 | CTA | headline, body, button text, button link |
| 6 | FAQ | list of {question, answer} |
| 7 | Testimonials | list of {name, text, rating} |
| 8 | Why Choose Us | list of {title, description, icon} |
| 9 | How It Works | list of {step, title, description} |
| 10 | Contact | address, phone, email, hours, map embed |
| 11 | Design | theme preset, primary color, secondary color, font |
| 12 | SEO | title tag, meta description, OG image |
| 13 | Visibility | toggle sections on/off |

Each section can be independently regenerated with AI (sends just that section's context to Claude, not the whole site).

### Live preview

iframe with `srcdoc` injection. Three device widths:
- Desktop (1280px)
- Tablet (768px)
- Mobile (375px)

The tricky part was getting the preview to update without full page reloads. Used `postMessage` to send section-level updates to the iframe, which patches the DOM. Full rebuild only happens on theme change or explicit "Rebuild" click.

### Dirty detection

This was a small but important detail. Before triggering a rebuild, compare current editor state to last-built state via `JSON.stringify` comparison. If nothing changed, skip the build. If only content changed (not theme/design), do a quick rebuild (inject content, no full Vite build). If theme changed, full rebuild.

```
Quick preview: ~2 seconds (content injection)
Full rebuild:  ~15 seconds (Vite build)
Redeploy:      ~30 seconds (Cloudflare push)
```

### Theme presets

Five presets, each defining colors, font stack, border radius, shadow style:

- **Modern** — Inter, blue-600 primary, clean shadows, rounded-lg
- **Classic** — Georgia, navy primary, no shadows, sharp corners
- **Bold** — Montserrat, orange-500 primary, heavy shadows, rounded-xl
- **Minimal** — System UI, gray-900 primary, no shadows, no borders
- **Elegant** — Playfair Display, gold primary, subtle shadows, rounded-sm

### expertise.yaml after Session 3

```yaml
app: site-builder
last_updated: 2026-04-07

architecture:
  frontend: Vue 3 + TypeScript + Pinia + Tailwind CSS
  backend: FastAPI + Python 3.13 + asyncio
  generated_sites: React 18 + Tailwind CSS (Vite build)
  ai_content: Claude Sonnet (claude-sonnet-4-20250514)
  ai_images: Gemini 2.5 Flash Image
  realtime: WebSocket (/ws)

pipeline:
  steps:
    - parsing_url: maps_url_parser.py
    - scraping_profile: maps_scraper.py (Playwright + stealth)
    - scraping_website: website_scraper.py (optional)
    - generating_content: site_generator.py (Claude)
    - generating_images: image_generator.py (Gemini)
    - building_site: react_builder.py (npm build)
    - deploying: TBD

editor:
  sections: 13 (Hero, About, Services, Gallery, CTA, FAQ, Testimonials, Why Choose Us, How It Works, Contact, Design, SEO, Visibility)
  features:
    - live iframe preview with device switching
    - AI section regeneration via Claude
    - theme presets (Modern, Classic, Bold, Minimal, Elegant)
    - dirty detection via JSON comparison
    - quick preview vs full rebuild vs redeploy

scraping:
  maps_data: name, category, address, hours, rating, review_count, top_reviews, photos, website_url
  website_data: services, about_text, testimonials, color_scheme
  stealth: playwright-stealth required

unvalidated_observations:
  - "Pinia store for editor state makes dirty detection trivial — just compare $state snapshots"
  - "iframe postMessage for live preview is faster than srcdoc replacement but needs origin checking"
  - "AI section regen should include surrounding sections as context to maintain tone consistency"
  - "Theme preset switch sometimes leaves stale CSS variables — need to clear before applying new theme"
```

Ran `/improve`:

```
/improve site-builder

Reviewing 4 unvalidated observations...

✓ PROMOTED: "Pinia store makes dirty detection trivial"
  → Added to editor.features (dirty detection via JSON comparison)
  Reason: Confirmed. useSiteStore.$state is snapshotted after each build.
  Comparison is just JSON.stringify(current) !== JSON.stringify(lastBuilt).

✓ PROMOTED: "iframe postMessage faster than srcdoc replacement"
  → Added to editor.implementation_notes
  Reason: Confirmed. srcdoc causes full iframe reload (~800ms flicker).
  postMessage patches DOM in-place (~50ms, no flicker).

✓ PROMOTED: "AI section regen should include surrounding sections for tone"
  → Added to pipeline.ai_content notes
  Reason: Confirmed and implemented. Section regen prompt now includes
  prev_section and next_section summaries for context.

○ DISCARDED: "Theme preset switch leaves stale CSS variables"
  Reason: Fixed during this session. clearThemeVariables() called before
  applyTheme(). No longer reproducible.

3 promoted, 1 discarded, 0 deferred.
```

---

## Session 4 — Testing + Deploy (Day 4, ~1 hour)

### Test suite

Built 98 tests across four layers using the ACT-LEARN-REUSE pattern (test failures inform future test generation):

**Backend unit (33 tests, pytest + httpx):**
- URL parser: all 4 Maps URL formats + 6 edge cases
- Scraper: mock responses for Maps and website data extraction
- Generator: prompt construction, markdown stripping, section isolation
- Builder: template injection, Vite build invocation
- API routes: all endpoints, error handling, auth

**Frontend store (33 tests, vitest):**
- Pinia stores: pipeline state machine, editor state, theme application
- Dirty detection: changed vs unchanged, content-only vs theme changes
- WebSocket: connection, reconnection, message parsing

**E2E smoke (21 tests, Playwright):**
- Navigation, form submission, editor interactions
- Device preview switching
- Theme preset application
- Section visibility toggles

**E2E full generation (11 tests, Playwright, ~5 min):**
- Full pipeline: URL input through deployed site
- Error paths: invalid URL, scraper failure, generation timeout
- Editor: edit, preview, rebuild, redeploy cycle

One test caught a real bug: the "redeploy" button was enabled even when the site hadn't been rebuilt after an edit. The dirty detection was checking editor state vs last-built state, but "last deployed" state was a separate concept. Added a third state snapshot.

### Deployment

Set up the deploy pipeline:

- **Backend**: Railway (auto-deploy from `spotcircuit/site-builder` standalone repo)
- **Frontend**: Vercel (auto-deploy from same standalone repo, different root)
- **Generated sites**: Cloudflare Pages (wrangler CLI from backend)

The standalone repo is synced from the monorepo via a GitHub Action that runs on push to main. It extracts just the `apps/site_builder/` subtree and force-pushes to `spotcircuit/site-builder`.

Hit one issue: Cloudflare Pages has a project limit (varies by plan). Added auto-cleanup that deletes the oldest project when the limit is hit. Not ideal — should probably use subdomains under one project instead. Logged as observation.

### Final /brief

```
/brief site-builder

Site Builder — Briefing
━━━━━━━━━━━━━━━━━━━━━━
Status: Deployed and functional
Pipeline: 7 steps (URL → Scrape Maps → Scrape Website → Generate Content → Generate Images → Build → Deploy)
Editor: 13 sections, live preview, 5 themes, dirty detection
Tests: 98 across 4 layers (33 unit + 33 store + 21 smoke + 11 full)
Deploy: Railway (API) + Vercel (UI) + Cloudflare Pages (sites)

No unvalidated observations.
All promoted or discarded via /improve.

Architecture is stable. Open question: productization path
(demo tool vs paid service vs white-label).
```

### Final expertise.yaml

This is what ended up in `expertise.yaml` — the version checked into this repo:

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
  sections: 13 (Hero, About, Services, Gallery, CTA, FAQ, Testimonials, Why Choose Us, How It Works, Contact, Design, SEO, Visibility)
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

### Wiki capture

Ran `/wiki-file deployment-pattern-monorepo-to-standalone` to capture the GitHub Action sync pattern as a wiki page. This is a reusable pattern — any monorepo app could use the same approach:

```
wiki/patterns/monorepo-standalone-sync.md created
  - Describes the GitHub Action subtree extraction
  - Links to [[site-builder-architecture]], [[deployment-patterns]]
  - Tagged: #deployment #github-actions #monorepo
```

---

## What the framework actually did

Across four sessions, Clarity:

1. **Kept context alive between sessions.** Each `/brief` at session start gave a clean summary of where things stood, what was unvalidated, and what to focus on next. No re-reading code to remember what happened yesterday.

2. **Caught stale observations.** Two observations were discarded because they described problems that got fixed later in the same session. Without `/improve`, those would have lingered as "known issues" that weren't issues anymore.

3. **Forced specificity.** The observation format pushes you toward concrete statements ("Gemini timeouts on complex prompts, need 30s timeout + retry") instead of vague notes ("image gen is slow sometimes"). The promotion step verifies these against actual code.

4. **Grew `expertise.yaml` naturally.** It started with 5 lines of architecture and ended with a complete operational reference. No one sat down and wrote documentation — it accumulated through the build process.

5. **Created reusable knowledge.** The wiki page for monorepo-to-standalone sync isn't site-builder-specific. Next time any app needs that pattern, it's already documented with the gotchas included.

Total build time: ~8 hours across 4 sessions. Of that, maybe 30 minutes was framework overhead (running commands, reviewing promotions). The rest was actual building. The payoff is that anyone picking this up — human or AI — can read `expertise.yaml` and `BUILD_JOURNAL.md` and have full context in minutes instead of hours.
