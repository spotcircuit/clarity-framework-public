# Acme Integration

An enterprise client engagement built across four sessions using the Clarity Framework. AI-assisted flow generation and deployment for a Node-RED-based trade compliance platform. Different project type from site-builder (enterprise integration, not web app) but the same framework patterns.

## What the framework produced

`expertise.yaml` grew from 15 lines after Session 1 to a complete operational reference covering: Node-RED architecture with 14 custom nodes, 4 core flow specifications, full Node-RED Admin API documentation with 7 gotchas, a push agent deployment pipeline, Playwright test suites, and 3 architectural decisions with rationale.

## Architecture (from expertise.yaml)

```
Platform:  Node-RED 3.x (self-hosted, multi-tenant)
Runtime:   Node.js 18 LTS
Database:  PostgreSQL 15 (shipment records, compliance audit trail)
Messaging: MQTT (warehouse sensor events, status updates)
Auth:      OAuth2 + API keys per integration partner
Testing:   Playwright against Node-RED runtime endpoints
```

## The four core flows

| Flow | Nodes | Trigger | What it does |
|------|-------|---------|-------------|
| receiving_intake | 23 | MQTT from warehouse | Parses EDI 856, validates against PO, creates receiving record |
| compliance_check | 31 | HTTP from receiving flow | Denied party screening, HTS code validation, restricted items check |
| customs_filing | 38 | compliance_check CLEARED | Assembles documents, calculates duties, submits to customs broker API |
| status_tracking | 18 | Change events via MQTT | Aggregates events into unified shipment timeline |

AI generated each flow in ~3 minutes. Manual creation: 3+ hours per flow.

## The compliance flow bug

This is the most important story from this engagement.

AI generated the `compliance_check` flow. 31 nodes. Deployed to staging. Opened in editor -- looked correct after layout normalization. Nodes arranged left-to-right: denied party screening, then HTS lookup, then restricted items check.

Playwright test failed. One HTS lookup API call happened before denied-party rejection.

The bug: wires in the flow JSON connected the HTS lookup node to execute first, THEN denied party screening. Visual layout showed the correct order, but execution follows wires, not visual position. In a compliance system, denied party screening is fail-fast by regulation.

This bug would NOT have been caught by:
- Visual inspection in the editor (nodes were in the right position)
- JSON structure validation (all nodes and wires were valid)
- Manual trigger testing (both orders produce REJECTED, but side effects differ)

Only an integration test checking for the *absence* of downstream calls caught it. This is why the team chose Playwright against the runtime instead of unit tests on flow JSON.

## Push agent pipeline

The automated deployment pipeline, spec-to-production in ~7 minutes:

```
Generation:        2:47  (Claude produces flow JSON)
Layout norm:       0:03  (topological sort, grid snap)
Validation:        0:03  (node types, wire refs, credentials)
Staging deploy:    0:08  (Node-RED Admin API)
Playwright tests:  3:52  (30 tests against staging)
Production deploy: 0:08  (same API, production tenant)
Verification:      0:02
─────────────────────────
Total:             7:03
```

## Real API gotchas (from expertise.yaml)

- `PUT /flow/:id` replaces the ENTIRE flow. Omitting a node deletes it. Always GET first, modify, then PUT.
- Credential nodes are NOT returned by GET /flows. Must be created separately.
- Deploy type `nodes` only pushes changed nodes but does NOT restart message routing. Flows depending on deploy-time initialization need full deploy.
- Customs broker API returns HTTP 200 with error in response body for auth failures. Must check `response.status` field, not HTTP status code.
- ERP timestamps must be ISO 8601 with timezone. Sending without timezone offset causes silent data corruption (defaults to UTC-12).

## The rendering incident

Session 2: AI-generated flow was functionally correct but nodes overlapped in the editor. Team reaction: "AI slop." Nobody ran the flow or checked tests. Visual appearance was enough to reject it.

Lesson: when humans evaluate AI-generated artifacts through a visual editor, visual quality trumps functional correctness. Built a layout normalization post-processor (topological sort, 200px horizontal spacing, 20px grid snap). After normalization: indistinguishable from hand-built flows.

## Related

- [Site Builder](site-builder.md) -- Different project type (web app), same framework patterns
- [The Self-Learn Loop](../how-it-works/self-learn-loop.md) -- How the compliance bug became a permanent gotcha
- [Idempotency Guard](../patterns/idempotency-guard.md) -- Pattern used in the customs filing flow
