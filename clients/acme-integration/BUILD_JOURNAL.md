# Acme Integration — Build Journal

How the Clarity Framework was used across four sessions to build an AI-assisted flow generation and deployment pipeline for a Node-RED-based trade compliance platform. Different type of project from site-builder — enterprise integration, not web app development — but the same framework patterns apply.

---

## Session 1 — Discovery (Day 1, ~2.5 hours)

### Bootstrapping

Started with `/create acme-integration`. Clarity prompted for the basics:

```
> Client name: acme-integration
> Display name: Acme Logistics Integration
> Industry: trade compliance / logistics
> Goal: AI-assisted flow generation and deployment for Node-RED platform
```

Created `clients/acme-integration/client.yaml`. Ran `/discover acme-integration`.

Phase 0 came back with a solid decomposition. It identified the four core flows, the Node-RED Admin API as the programmatic interface, and flagged credential management as a risk area. Good output for a discovery prompt.

```
Phase 0 identified:
  - 4 core flows (receiving, compliance, filing, tracking)
  - Node-RED Admin API as deployment target
  - Credential nodes as special case (not returned by GET)
  - MQTT as inter-flow communication
  - PostgreSQL as persistence layer
  - Playwright as test framework (against runtime, not editor)
```

### Mapping existing flows

Spent most of the session understanding how the team currently builds flows. The big insight: they spend more time arranging nodes visually in the editor than writing logic. The editor is the bottleneck, not the business logic.

Explored the Node-RED Admin API directly. Made curl calls against the staging instance:

```bash
# Get all installed node types
curl -s http://staging:1880/nodes | jq '.[].types[]' | wc -l
# Result: 127 node types available (including 14 custom)

# Get all flows
curl -s http://staging:1880/flows | jq '.[] | select(.type=="tab") | .label'
# Result: 47 flow tabs on staging
```

The Admin API is well-documented but has behaviors that are not obvious from the docs. These became the gotchas section in expertise.yaml.

### expertise.yaml after Session 1

```yaml
client: acme-integration
last_updated: 2026-03-08

architecture:
  platform: Node-RED 3.x
  custom_nodes: 14

flows:
  core_count: 4
  total_in_production: 200+

nodered_admin_api:
  explored: true
  key_finding: "Full CRUD on flows. Credential nodes excluded from GET."

unvalidated_observations:
  - "Admin API supports full flow CRUD — can replace manual editor work"
  - "Credential nodes excluded from GET responses — need separate management"
  - "Team spends significant time on visual layout with zero execution impact"
  - "Four core flows handle 80% of volume — start with these"
```

Ran `/improve`:

```
/improve acme-integration

Reviewing 4 unvalidated observations...

✓ PROMOTED: "Admin API supports full flow CRUD"
  → Added to nodered_admin_api section
  Reason: Confirmed via curl against staging. GET/POST/PUT/DELETE all work.

✓ PROMOTED: "Credential nodes excluded from GET responses"
  → Added to nodered_admin_api.gotchas
  Reason: Confirmed. GET /flows returns credential node IDs but not values.

✓ PROMOTED: "Team spends significant time on visual layout"
  → Added to key_decisions (context for why programmatic approach)
  Reason: Confirmed by observing three flow-building sessions. Layout adjustment
  accounts for ~40% of total flow creation time.

✓ PROMOTED: "Four core flows handle 80% of volume"
  → Added to flows section
  Reason: Confirmed by shipment volume data from PostgreSQL.

4 promoted, 0 discarded, 0 deferred.
```

---

## Session 2 — First AI-Generated Flow (Day 3, ~3 hours)

### The brief

```
/brief acme-integration

Acme Integration — Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: Discovery complete
Architecture: Node-RED 3.x, 14 custom nodes, Admin API explored
Core flows: 4 (receiving, compliance, filing, tracking)
Key insight: Visual layout is 40% of flow creation time
Unvalidated: 0 (all promoted)

Suggested focus:
  1. Generate first flow via AI, test against manual equivalent
  2. Build layout normalization post-processor
  3. Establish Playwright test pattern
```

### AI flow generation — the 3-minute moment

Generated the `receiving_intake` flow from a natural language spec. Claude produced 23-node flow JSON in 2 minutes 47 seconds.

Deployed to staging via the Admin API:

```bash
curl -X POST http://staging:1880/flow \
  -H "Content-Type: application/json" \
  -H "Node-RED-Deployment-Type: flows" \
  -d @receiving_intake.json
```

Sent a test MQTT message. Receiving record appeared in PostgreSQL. Compliance check was triggered downstream. It worked.

Then someone opened the editor.

### The rendering incident

The flow was functionally correct. But in the editor, nodes were overlapping. The MQTT trigger sat directly on top of the JSON parser. The PostgreSQL node was below the visible area.

Node-RED stores node positions as `x` and `y` coordinates in the flow JSON. Claude generated reasonable coordinates but did not follow the team's visual conventions. The flow looked messy.

The reaction was immediate: "AI slop." Nobody ran the flow. Nobody checked if the tests passed. The visual appearance was enough to reject it.

This is a real pattern. When humans evaluate AI-generated artifacts through a visual editor, visual quality trumps functional correctness. The output needs to look right AND be right.

### The fix — layout normalization

Built a post-processor that normalizes AI-generated flow JSON:
- Topological sort of nodes by wire connections
- Left-to-right layout following execution order
- 200px horizontal spacing, 80px vertical for parallel branches
- Grid-snapped to Node-RED's 20px grid

After normalization: indistinguishable from hand-built flows in the editor.

### expertise.yaml growing

```yaml
# New sections added after Session 2:

flows:
  receiving_intake:
    nodes: 23
    ai_generated: true
    generation_time: "~3 minutes"

nodered_admin_api:
  gotchas:
    - "Node z-order in editor determined by array position in flow JSON"
    - "AI-generated flows need layout normalization for editor acceptance"

key_decisions:
  why_programmatic_flows:
    decision: "Generate flows via API instead of manual editor work"
    rationale: "3+ hours manual vs ~3 minutes AI-generated"

unvalidated_observations:
  - "AI generates functional flow JSON in ~3 min vs 3+ hours manual"
  - "Visual layout requires post-processing for team acceptance"
  - "Node-RED grid is 20px — positions should snap to multiples of 20"
```

Ran `/improve`:

```
/improve acme-integration

Reviewing 3 unvalidated observations...

✓ PROMOTED: "AI generates functional flow in ~3 min vs 3+ hours manual"
  → Added to key_decisions.why_programmatic_flows
  Reason: Confirmed. receiving_intake generated in 2:47, deployed, tested, working.

✓ PROMOTED: "Visual layout requires post-processing"
  → Added to push_agent.steps (layout normalization step)
  Reason: Confirmed. Normalization post-processor built and tested. Team accepted
  normalized flow on visual review.

✓ PROMOTED: "Node-RED grid is 20px"
  → Added to nodered_admin_api.gotchas
  Reason: Confirmed in Node-RED source. Grid snap is 20px in all directions.

3 promoted, 0 discarded, 0 deferred.
```

---

## Session 3 — Playwright Testing (Day 5, ~2 hours)

### The brief

```
/brief acme-integration

Acme Integration — Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: First flow generated and deployed
Architecture: Node-RED + AI generation + layout normalization
Flows: 1/4 generated (receiving_intake)
Key gap: No automated testing
Unvalidated: 0

Suggested focus:
  1. Build Playwright test suite for all four core flows
  2. Generate remaining three flows
  3. Establish deploy pipeline
```

### Why Playwright, not JSON validation

Could have written tests that inspect flow JSON structure — "does the denied party node exist? do the wires connect in the right order?" Decided against it. Flow JSON can be structurally correct and execution-order wrong. The compliance flow bug proved this.

Instead: test against the running Node-RED runtime. Send real inputs, check real outputs.

### The compliance flow bug

Generated `compliance_check` flow. 31 nodes. Deployed to staging. Opened in editor — looked great after normalization. Nodes arranged left-to-right: denied party screening, then HTS lookup, then restricted items check.

Ran the Playwright tests. Test case: send a known denied-party entity, expect REJECTED status with zero downstream API calls.

Test failed. One HTS lookup API call happened before the rejection.

The bug: wires in the flow JSON connected the HTS lookup node to execute first, THEN denied party screening. The visual layout showed the correct order (denied party first) but the wires told a different story. Execution follows wires, not visual position.

This is subtle and dangerous. In a compliance system, the order of checks matters. Denied party screening is fail-fast by regulation. Running other checks first violates the fail-fast requirement and leaves partially-processed records.

Fixed the wire order. Added a dedicated test: "denied party rejection must produce zero downstream API calls."

This bug would NOT have been caught by:
- Visual inspection in the editor (nodes were in the right visual position)
- JSON structure validation (all nodes and wires were present and valid)
- Manual trigger testing (both orders produce the same final result — REJECTED — but the side effects differ)

Only an integration test checking for the absence of downstream calls caught it.

### expertise.yaml after Session 3

```yaml
# Key addition:

testing:
  framework: Playwright
  approach: "Test against Node-RED runtime, not editor UI"
  suites:
    flow_execution: 12 tests
    compliance_logic: 8 tests
    filing_integration: 6 tests
    status_aggregation: 4 tests
  key_finding: "Playwright caught execution-order bug that visual inspection missed"

key_decisions:
  why_playwright_not_unit:
    decision: "Integration tests via Playwright, not unit tests on flow JSON"
    rationale: "Flow JSON validation misses execution-order bugs."

unvalidated_observations:
  - "AI wire order doesn't always match visual layout — execution follows wires not position"
  - "Denied party screening must be fail-fast — need dedicated test for zero downstream calls on rejection"
  - "Test runtime ~4 min. Acceptable for deploy pipeline."
```

Ran `/improve`:

```
/improve acme-integration

Reviewing 3 unvalidated observations...

✓ PROMOTED: "AI wire order doesn't always match visual layout"
  → Added to nodered_admin_api.gotchas
  Reason: Confirmed by compliance flow bug. Wire-based execution order can differ
  from visual node arrangement. Must test execution order, not visual order.

✓ PROMOTED: "Denied party screening must be fail-fast"
  → Added to flows.compliance_check notes
  Reason: Confirmed. Regulatory requirement. Test added.

✓ PROMOTED: "Test runtime ~4 min"
  → Added to testing section
  Reason: Confirmed. 30 tests across 4 suites, ~4 min against staging.

3 promoted, 0 discarded, 0 deferred.
```

---

## Session 4 — Push Agent & Production (Day 8, ~2 hours)

### The brief

```
/brief acme-integration

Acme Integration — Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: 4 flows generated, tested
Architecture: Node-RED + AI generation + layout normalization + Playwright
Testing: 30 tests, all passing on staging
Key gap: No deployment pipeline, manual promotion to production
Unvalidated: 0

Suggested focus:
  1. Build push agent for automated deploy pipeline
  2. First production deploy
  3. Rollback mechanism
```

### Push agent

Built the automated deployment pipeline:

1. Generate flow JSON from specification (Claude)
2. Normalize layout (post-processor)
3. Validate structure (node types, wire references, credentials)
4. Deploy to staging (Node-RED Admin API)
5. Run Playwright tests
6. On pass: deploy to production
7. On fail: log, rollback staging

### Admin API gotchas — final collection

The push agent surfaced the remaining sharp edges:

**`PUT /flow/:id` replaces everything.** If you omit a node from the PUT body, it gets deleted. You must GET the current state, merge your changes, then PUT the complete result. There is no PATCH endpoint.

**Deploy type 'nodes' skips initialization.** `Node-RED-Deployment-Type: nodes` only pushes changed nodes. It does NOT reinitialize context stores, MQTT connections, or other deploy-time setup. The status tracking flow depends on context store initialization. If you deploy it with `nodes` type, it runs with empty context until the next full deploy.

Solution: use `nodes` type for most flows, `flows` type (full redeploy) only when status tracking flow changes.

**Credential orphans.** Deleting a flow does not delete its credential nodes. They accumulate. Built a cleanup routine that runs weekly.

### First production deploy

Pushed an updated `receiving_intake` flow (added estimated arrival date field) through the full pipeline:

```
Generation:        2:47
Layout norm:       0:03
Validation:        0:03
Staging deploy:    0:08
Playwright tests:  3:52
Production deploy: 0:08
Verification:      0:02
─────────────────────────
Total:             7:03
```

Seven minutes from specification to production. Manual process for the same change: 3-4 hours minimum, often spanning two days when the change request sat in the review queue.

### Final /brief

```
/brief acme-integration

Acme Integration — Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: Deployed and operational
Architecture: Node-RED + AI generation + layout norm + Playwright + push agent
Flows: 4 core flows generated, tested, in production
Testing: 30 tests, ~4 min runtime, all passing
Deploy: Push agent pipeline, ~7 min spec-to-production
Rollback: Snapshot-based, tested

Unvalidated: 5 observations pending next /improve cycle.
```

### expertise.yaml — final state

The expertise.yaml checked into this repo is the final version after Session 4. It grew from 15 lines after Session 1 to the full operational reference. Nobody sat down and wrote it as documentation — it accumulated through the `/improve` cycle.

The unvalidated observations at the bottom are real pending items from the last session. They represent the next session's starting point.

---

## What the framework did on this project

Acme Integration is a different kind of project from site-builder. It is enterprise integration work — Node-RED flows, customs compliance, MQTT messaging, multi-tenant deployment. But the framework patterns worked the same way.

### 1. Context survived between sessions

Each session started with `/brief`. On Day 5, the brief told me exactly where things stood: one flow generated, no testing yet, no deploy pipeline. I did not need to re-read code or check what state the staging instance was in. The brief had it.

### 2. Gotchas accumulated in one place

The Node-RED Admin API gotchas section in expertise.yaml is worth its weight. Things like "PUT replaces everything, not patches" and "credential nodes excluded from GET" and "deploy type 'nodes' skips initialization" — these would normally live in one engineer's head or scattered across Slack messages. They are in expertise.yaml, structured, searchable, and available to any engineer or AI agent that reads the file.

### 3. /improve caught the real bugs

The compliance flow execution-order bug was found by Playwright, but it was `/improve` that promoted "AI wire order doesn't always match visual layout" from an observation to a documented gotcha. That gotcha now prevents the same class of bug on every future flow generation.

### 4. The 3-minute story holds up

AI-generated flow in ~3 minutes vs 3+ hours manual. The push agent adds ~4 minutes of validation and testing. Total: ~7 minutes. The time savings are real and repeatable.

### 5. Visual acceptance matters as much as functional correctness

The rendering incident (Session 2) was the most important lesson. Functionally correct output that looks wrong in the editor will be rejected. The layout normalization post-processor was not in the original plan. It was born from an observation, promoted by `/improve`, and became a core part of the pipeline. This is the self-learn loop working as intended.
