# SpotCircuit - Phase 0 Discovery

## Overview
SpotCircuit is pivoting from an AI marketing agency (serving contractors, local businesses) to an agentic AI engineering practice. The website at www.spotcircuit.com needs to reflect this new positioning.

## Current State (2026-04-08)
- Site retooled: homepage, /services, /clarity, /about pages rewritten
- Header/footer slimmed to 5-link nav
- 34 Vercel redirects handle all old indexed URLs
- SEO audit issues fixed: hreflang, sitemap, schema, robots.txt
- Blog infrastructure (Ghost CMS) retained

## Tech Stack
- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Vercel hosting, auto-deploy on push to main
- Ghost CMS for blog (headless API)
- Ahrefs + Microsoft Clarity + Google Analytics

## Remaining Work
1. Delete old page directories to reduce build size
2. Fix Ghost blog orphan links (2 deleted posts)
3. First blog post (Karpathy wiki extension or agentic session walkthrough)
4. LinkedIn presence (announce pivot)
5. Portfolio site retool
6. Clarity Framework GitHub README polish
