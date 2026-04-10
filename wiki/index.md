# Clarity Wiki

The knowledge base for SpotCircuit's agentic AI engineering practice. Built on the Karpathy LLM Wiki pattern.

---

- [[linkedin-post-2026-04-08]] -- LinkedIn post: clarity (2026-04-08)
- [[linkedin-post-2026-04-09]] -- LinkedIn post: clarity (2026-04-09)
- [[social-post-2026-04-10]] -- Social post: casestudy (2026-04-10)
## Platform
The framework, orchestration, and infrastructure that everything runs on.
- [[clarity-framework]] -- Open-source agentic intelligence framework. Self-learn loop, 9 commands, 3 knowledge systems.
- [[paperclip-integration]] -- Paperclip agent orchestration: 5 agents, heartbeats, issue routing.
- [[infrastructure]] -- Deployment map: Railway, Vercel, Cloudflare, Neon, GitHub Pages. Full repo inventory.

## Apps
Products and tools we build and ship.
- [[spotcircuit-services]] -- The 6 revenue streams: framework licensing, AI consulting, Claude Code, knowledge bases, pipelines, build in public.
- [[site-builder-overview]] -- Google Maps to deployed React site in 60s. Full pipeline.
- [[getrankedlocal]] -- Google Maps 169-point grid ranking analysis + lead gen platform.
- [[ai-content-pipeline]] -- Claude for copy + Gemini for images. Config-driven, model-swappable.
- [[drcoins]] -- Oh Deer Coins. LiveMe Coins e-commerce platform. Next.js 15.5 + React 19.
- [[seosnap]] -- AI-powered SEO audit tool. Playwright + Lighthouse + GPT-5 Nano recommendations.
- [[service-marketplace]] -- Niche-agnostic service marketplace. Directory + lead gen + Stripe subscriptions.
- [[leadfinder-overview]] -- Production lead gen. Google Maps scraping + AI enrichment + FastAPI.
- [[invoicedb]] -- Invoice database with agentic AI workflows (ADW system).
- [[agentic-agent]] -- Multi-agent orchestration platform. WebSocket streaming + PostgreSQL + cost tracking.
- [[sopify]] -- Loom video to Notion SOP converter via n8n webhooks.
- [[tube2link]] -- YouTube to LinkedIn post converter. Caption extraction + AI generation.
- [[airecruiter]] -- AI recruiting platform. ATS Kanban, resume parsing, smart matching, Stripe.
- [[weatherproof-overview]] -- Construction weather delay tracking + insurance claim PDF generation.
- [[atlasly]] -- Schema-driven business directory. Mapbox + Typesense geo search + Stripe.
- [[bidgeniusai]] -- AI-powered RFP bidding tool for government/enterprise contracts.
- [[aduplanner]] -- ADU planning with GPT-4 Vision satellite imagery analysis + Google Maps.
- [[make-2-n8n]] -- Make.com to n8n workflow converter and pricing calculator.
- [[lead-finder]] -- (Reference) Multi-source lead scraper + AI pitch gen.
- [[listing-launch]] -- (Reference) Real estate multi-channel content generator.
- [[orchestrator-3-stream]] -- (Reference) Pre-Paperclip multi-agent orchestrator. Superseded.

## Patterns
Reusable engineering patterns across all apps.
- [[correlation-id]] -- Track execution across services and logs.
- [[idempotency-guard]] -- Status gate prevents duplicate processing.
- [[error-handling]] -- Catch errors, log them, write status back to source record.
- [[config-driven-routing]] -- Routing logic in config records, not code.
- [[mock-data-strategy]] -- Mock toggle for external APIs without sandboxes.
- [[pre-release-checklist]] -- Every production release gate.
- [[cloudflare-pages-deploy]] -- Deploy static sites to CF Pages with auto project limit management.
- [[websocket-progress-pattern]] -- Real-time pipeline progress via WebSocket broadcast.
- [[inline-editor-pattern]] -- Post-generation editing with live iframe preview + rebuild.
- [[act-learn-reuse-testing]] -- Self-improving test loop: run, extract failures, feed knowledge back.
- [[scout-build-verify]] -- Three-agent workflow: scout analyzes, builder implements, verifier validates.

## Decisions
Architectural decisions with rationale.
- [[karpathy-wiki-comparison]] -- LLM Wiki vs Clarity. Gaps, advantages, bridge plan.
- [[multi-format-ingest-strategy]] -- Config-driven + AI hybrid for normalizing data formats.
