# Acme Integration — Session Notes

---

## Session 1 — Discovery & Flow Mapping (2026-03-08, ~2.5 hours)

### What happened

Ran `/create acme-integration` and `/discover acme-integration`. Phase 0 generated cleanly.

Spent most of the session mapping existing manual flows. The client has 200+ flows in production but the four core ones handle 80% of shipment volume:

1. **Receiving intake** — EDI 856 parsing, PO validation
2. **Compliance check** — denied party + HTS code + restricted items
3. **Customs filing** — document assembly, duty calculation, broker submission
4. **Status tracking** — event aggregation from all flows into timeline

Key discovery: the engineering team spends more time arranging nodes in the editor than writing actual logic. The visual layout is a significant time sink because reviewers judge flows by how they look in the editor, not by whether they execute correctly.

Explored the Node-RED Admin API. It is more capable than expected — full CRUD on flows, node inventory, deployment control. The `GET /flows` endpoint returns the entire configuration. You can modify it and `POST /flows` to redeploy everything. Also supports per-flow operations via `/flow/:id`.

### Gotcha found

`GET /flows` does NOT return credential node values. Credentials are stored separately and only referenced by ID in the flow JSON. This means you cannot simply GET a flow, modify it, and PUT it back if it involves credential changes. You have to manage credentials through a separate mechanism.

### Observations logged

- "Node-RED Admin API supports full flow CRUD — can replace manual editor work"
- "Credential nodes are excluded from GET responses — need separate credential management"
- "Team spends significant time on visual layout that has zero impact on execution"
- "Four core flows handle 80% of volume — start with these for AI generation"

---

## Session 2 — First AI-Generated Flow (2026-03-10, ~3 hours)

### What happened

Built the first AI-generated flow: `receiving_intake`. Gave Claude the specification in natural language:

```
Generate a Node-RED flow JSON that:
- Triggers on MQTT message to topic "warehouse/shipments/inbound"
- Parses the EDI 856 payload (JSON, already converted from raw EDI)
- Validates shipment against PO in PostgreSQL (query by PO number)
- If PO match: create receiving record, publish MQTT to "compliance/check/new"
- If no PO match: log warning, send webhook alert to operations
- Error handling: catch node on every branch, log to PostgreSQL error table
```

Claude generated the flow JSON in about 3 minutes. 23 nodes, correctly wired.

Deployed to staging via Admin API. First test: MQTT message in, receiving record created, compliance check triggered. Worked.

Then someone opened it in the Node-RED editor.

### The rendering issue

The flow was functionally correct, but visually it looked wrong in the editor. Nodes were overlapping. The MQTT input node sat on top of the JSON parser. The PostgreSQL query node was below the visible canvas area. You had to scroll and rearrange to see the full flow.

This is because Node-RED node positions are stored as `x` and `y` coordinates in the JSON. Claude generated reasonable coordinates but did not account for the editor's grid snapping or the visual conventions the team uses (left-to-right, top-to-bottom, consistent spacing).

The reaction: "This looks like AI slop."

Nobody ran it. Nobody checked if it worked. The visual layout was enough to dismiss it.

### The fix

Wrote a post-processor that takes AI-generated flow JSON and normalizes the layout:
- Nodes arranged left-to-right following wire connections
- Consistent 200px horizontal spacing between connected nodes
- Vertical stacking for parallel branches
- Grid-snapped to Node-RED's 20px grid

After normalization, the flow looks indistinguishable from a hand-built flow in the editor. Same logic, same wires, just neater coordinates.

### Observations logged

- "AI generates functional flow JSON in ~3 min vs 3+ hours manual — 60x speedup"
- "Node visual layout in editor requires post-processing — x/y coordinates must follow team conventions"
- "Node-RED grid is 20px — all node positions should snap to multiples of 20"
- "Visual quality of flows in editor affects review acceptance regardless of functional correctness"

---

## Session 3 — Playwright Testing (2026-03-12, ~2 hours)

### What happened

Built Playwright test suite for all four core flows. The approach: test against the running Node-RED runtime, not the flow JSON structure.

Each test:
1. Sends a trigger (MQTT message or HTTP POST) to the flow's entry point
2. Waits for the expected output (database record, MQTT message, HTTP response, webhook call)
3. Asserts correctness of the output

### The execution-order bug

This is where testing earned its keep.

AI-generated `compliance_check` flow had all the right nodes: denied party screening, HTS code lookup, restricted items check. Visually, in the editor, they were arranged left-to-right in the correct order: denied party first, then HTS, then restricted items.

But the wires told a different story. The HTS lookup node was wired to execute FIRST, with denied party screening second. The visual arrangement was correct but the execution order was wrong.

Why this matters: denied party screening is a fail-fast check. If an entity is on the denied party list, you must stop processing immediately. Running HTS lookup first wastes time and API calls on a shipment that will be rejected anyway. Worse, if HTS lookup modifies the shipment record (it adds the HTS code), a denied-party rejection after that point leaves a partially-processed record in the database.

Playwright caught this because the test sent a known denied-party entity and expected a REJECTED status with zero HTS lookups. Instead, the test saw one HTS lookup API call before the rejection.

Fixed the wire order. Added a specific test case: "denied party entity must produce REJECTED with no downstream API calls."

### Test suite

```
Flow execution tests:        12 (3 per core flow)
Compliance logic tests:        8 (denied party, HTS, restricted items edge cases)
Filing integration tests:      6 (mock broker API, verify payload structure)
Status aggregation tests:      4 (multi-flow event timeline)
Total:                        30 tests, ~4 min runtime
```

### Observations logged

- "Playwright tests against runtime catch execution-order bugs that JSON validation and visual inspection miss"
- "AI-generated wires do not always match visual node arrangement — execution order follows wires, not x/y position"
- "Denied party screening must be fail-fast — test specifically that no downstream API calls happen on rejection"
- "Test runtime is ~4 min against staging. Acceptable for deploy pipeline, too slow for rapid iteration."

---

## Session 4 — Push Agent & Deploy Pipeline (2026-03-15, ~2 hours)

### What happened

Built the push agent — an automated pipeline that takes a flow specification, generates the flow JSON, validates it, deploys to staging, runs tests, and promotes to production.

### Push agent pipeline

```
Specification (natural language)
        │
        ▼
   AI Generation (Claude, ~3 min)
        │
        ▼
   Layout Normalization (post-processor)
        │
        ▼
   Structural Validation
   - All node types exist (GET /nodes)
   - All wires reference valid node IDs
   - Credential nodes present for nodes that need them
   - No duplicate node IDs
        │
        ▼
   Deploy to Staging (POST /flow via Admin API)
        │
        ▼
   Playwright Tests (~4 min)
        │  PASS                    │ FAIL
        ▼                          ▼
   Deploy to Production       Log failure, rollback staging
   (POST /flow via Admin API)
        │
        ▼
   Verify (GET /flow, compare)
```

### Admin API gotchas encountered

**Deploy type header matters.** `Node-RED-Deployment-Type: flows` redeploys everything (full restart). `Node-RED-Deployment-Type: nodes` only pushes changed nodes but does NOT reinitialize flow context stores or reconnect MQTT. The status tracking flow depends on context store initialization at deploy time, so it needs full deploy. But full deploy causes a 15-30 second MQTT reconnection gap.

Solution: deploy new/changed flows with `nodes` type first, then do a full deploy only if the status tracking flow was modified.

**Rollback via snapshot.** Before every production deploy, GET the current flow configuration and store it. If anything fails, PUT the snapshot back. Tested this by intentionally deploying a broken flow to staging, verifying the failure, then restoring the snapshot. Works, but the restore takes about 10 seconds during which the flow is unavailable.

**Credential persistence.** Credential nodes created via the API persist across redeploys. You do not need to re-create them each time. But if you delete a flow that references a credential node, the credential node becomes orphaned. Built a cleanup step that checks for orphaned credentials after flow deletion.

### First production deploy

Used the push agent to deploy an updated `receiving_intake` flow to production. The update added handling for a new EDI field (estimated arrival date).

Pipeline ran end-to-end:
- Generation: 2 min 47 sec
- Validation: 3 sec
- Staging deploy: 8 sec
- Playwright tests: 3 min 52 sec
- Production deploy: 8 sec
- Verify: 2 sec

Total: ~7 minutes from specification to production. Previous process (manual build, manual test, manual deploy with change request): 3-4 hours minimum, often spanning two days due to review queue.

### Observations logged

- "Push agent full pipeline: ~7 min from spec to production. Manual process: 3-4 hours minimum."
- "Node-RED-Deployment-Type 'nodes' does not reinitialize context stores. Status tracking flow needs full deploy."
- "Rollback via GET/PUT snapshot works but has ~10 sec unavailability window."
- "Orphaned credential nodes accumulate after flow deletion. Need periodic cleanup."
- "MQTT reconnection gap (15-30s) on full deploy. Status tracking flow misses events during this window."
