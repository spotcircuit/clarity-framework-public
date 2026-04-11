# Site Builder Dev Session Notes

**Date:** 2026-04-04 (Session 3 of 4)
**Who:** Brian (solo, ~3 hours)

## Where we left off

Last session ended with maps_scraper.py working for basic profiles but Google Maps was serving the "limited view" (only Overview + About tabs) because Playwright had no session cookies. Reviews tab never appeared. Spent an hour on that before realizing it was a session/consent issue, not a selector issue.

## What got done today

### Maps scraper -- persistent browser context (maps_scraper.py)

- Fixed the limited view problem. Root cause: Google Maps shows full experience (Reviews, Photos, Menu tabs) only when the browser has an established Google session. Without consent cookies, you get a stripped-down page.
- Solution: `launch_persistent_context` with a base profile dir. Visit google.com first, accept the "Accept all" cookie consent button, THEN navigate to the Maps URL. Night and day difference.
- Had to add concurrent scrape support -- copy base profile to a per-job temp dir so two jobs don't stomp on each other's cookies. See `job_profile_dir` logic around line 738.
- Review extraction capped at 20 seconds to avoid blocking the pipeline. Good enough, we get 5-10 reviews which is plenty for testimonials.
- Selectors ported from the getrankedlocal production scrapers. The `data-item-id="address"` and `data-item-id^="phone:tel:"` patterns are solid. Rating/review count comes from aria-labels like "4.3 stars 523 reviews".

### Claude JSON formatting issue (site_generator.py)

- Wasted 45 minutes on this. The system prompt says "respond with a single JSON object, no markdown fences, no preamble" but Claude still wraps output in ```json fences maybe 30% of the time.
- Built `_extract_json_from_response()` with a 3-tier fallback: try raw parse, try stripping markdown fences via regex, try extracting first `{...}` block. Works every time now but it's ugly.
- The SiteContent pydantic model is huge -- hero, about, services, why_choose_us, process_steps, testimonials, FAQ, CTA, SEO fields, color tokens, typography. Claude handles it fine with Sonnet, never truncates.

### Website scraper enrichment (website_scraper.py)

- New module. Runs AFTER maps scraper, hits the business's actual website to pull branding, colors, fonts, logo, about text, social links.
- WebsiteData model captures: brand_colors (hex from CSS), fonts, nav_structure, detected_sections, contact_confidence.
- Key insight: franchise detection. If we find multiple street addresses on the site, it's probably a franchise and we should NOT use the website's generic contact info. Set `contact_confidence: "low"` and prefer Maps data instead. Maps data is always location-specific so it gets `contact_confidence: "high"`.
- The backfill logic in main.py (~line 490) merges website data into business_data -- phone, email, hours, address only if Maps didn't have them.

### Cloudflare Pages deploy (cloudflare_deployer.py)

- Hit the free tier project limit immediately. Cloudflare caps at 100 projects per account.
- Built auto-cleanup: when error code 8000027 comes back from project creation, list all projects, sort by created_at, delete the oldest one, retry. See `_ensure_project_exists()`.
- Deploy itself uses `npx wrangler pages deploy` shelled out as a subprocess. Tried the REST API first but direct upload via wrangler is way more reliable.
- Fallback chain in main.py: Cloudflare fails -> try Vercel. Vercel fails -> try Cloudflare. Deploy failure is non-fatal, site still works locally.

## Architecture decisions

- **In-memory job storage** -- no database. Jobs dict lives in main.py, TTL cleanup runs hourly. Deployed jobs get 7 days, undeployed get 3. Good enough for a tool, not a SaaS.
- **WebSocket for progress** -- every pipeline step broadcasts status via websocket_manager.py. Frontend ProgressPanel subscribes and shows real-time step completion. Way better UX than polling.
- **React template system** -- react_builder.py copies templates/react/ to a temp dir, writes data.json with all content + business data, runs `npm run build`. The only file that changes per generation is data.json. Three templates now: modern, bold, elegant (TEMPLATE_REGISTRY dict).
- **Gemini for images, Claude for content** -- image_generator.py uses gemini-2.5-flash-image. Generates hero, about, gallery, services images. Non-fatal if GEMINI_API_KEY not set, site just uses Google Maps photos or placeholders.
- **Two input paths** -- GenerateSiteRequest accepts maps_url OR website_url. Maps path runs full pipeline (parse -> scrape Maps -> scrape website -> generate). Website-only path skips Maps, requires business_name in the request.

## Still broken / open questions

- [ ] Photos extraction is flaky -- Google uses both `/p/` and `/gps-cs-s/` paths for business photos on googleusercontent.com, and the selectors sometimes miss the grid thumbnails
- [ ] Rate limiter is in-memory (rate_limiter.py), resets on deploy. Need Redis or at least a file-backed store for Railway
- [ ] The error_log.jsonl and deploy_log.jsonl persist on disk but Railway's ephemeral filesystem means they vanish on redeploy. Should push to S3 or a DB eventually
- [ ] Website scraper subpage crawling -- currently visits homepage + a few nav links. Should we go deeper? Risk of slow scrapes on big sites
- [ ] Editor has 17 Vue components and 13 editable sections. Rebuild flow calls rebuild_react_site() which re-runs npm build. Takes ~8 seconds. Can we cache node_modules across rebuilds?
- [ ] Claude OAuth fallback in site_generator.py reads ~/.claude/.credentials.json directly. Works locally but won't exist on Railway. Fine for now since we set ANTHROPIC_API_KEY in Railway env.

## Action items for next session

- [ ] Add Playwright stealth / randomized user-agent rotation -- current hardcoded UA string will get flagged eventually
- [ ] Set up the GitHub Action to sync apps/site_builder/ from monorepo to the standalone spotcircuit/site-builder repo
- [ ] Write actual tests -- test_api.py and test_models.py exist but need to cover the scraping edge cases
- [ ] Try the bold and elegant templates on 10 different business types, see which generates better content
