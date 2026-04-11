# Jira Export — Sprint 14 Tickets (Deployment Automation Epic)
# Project: DEMO
# Sprint: Sprint 14 (2026-04-07 to 2026-04-18)
# Export date: 2026-04-07

---

## DEMO-470 | Block Kit pagination for deploy summaries
**Status:** In Progress
**Assignee:** James Kim
**Priority:** Medium
**Story Points:** 3

**Description:**
Deploy summaries for multi-service releases exceed Slack's 50-block limit. Paginate: parent message shows summary (services, ticket count, overall status), thread reply contains full per-service details.

**Acceptance Criteria:**
- Deploy summary with >8 services renders correctly in Slack
- Parent message stays under 40 blocks
- Thread reply contains full details
- Unfurl behavior on parent message doesn't show confusing thread preview

**Blockers:** None
**Notes:** James hit an unfurl issue — Slack shows a preview of the thread reply in the parent message. Timeboxed to half a day per sprint planning discussion.

---

## DEMO-478 | DORA metrics aggregation query
**Status:** To Do
**Assignee:** Priya Patel
**Priority:** High
**Story Points:** 8

**Description:**
Build the backend aggregation for DORA metrics:
- **Deployment Frequency:** Count of successful prod deploys per service per day/week/month
- **Lead Time for Changes:** Median time from PR merge to production deploy
- **Change Failure Rate:** % of deploys that trigger a rollback within 30 minutes
- **Mean Time to Recovery:** Median time from rollback to next successful deploy

Requires denormalizing the Jira ticket number into the deployments table at write time (webhook-router writes it during GitHub push event processing). Currently the ticket correlation is a 4-hop lookup: commit → PR → branch → ticket number.

**Acceptance Criteria:**
- API endpoint: `GET /api/metrics/dora?service=all&period=30d`
- Response includes all 4 DORA metrics
- Query runs in <500ms for 90-day window
- Deployments table migration adds `jira_ticket_key` column

**Blockers:** Needs deployments table schema migration (Priya to coordinate with Marcus on migration timing)
**Notes:** Dashboard frontend (DEMO-451, carried from Sprint 13) depends on this.

---

## DEMO-482 | Teams meeting transcript ingestion
**Status:** To Do
**Assignee:** Priya Patel
**Priority:** Medium
**Story Points:** 5

**Description:**
Automated ingestion of Teams meeting transcripts via Microsoft Graph API. Poll every 15 minutes for new transcripts. Extract:
- Jira ticket mentions (DEMO-\d+ pattern)
- Speaker attribution (map Teams display names to team members)
- Action items (heuristic: lines containing "should", "need to", "will", "action item")

Drop processed transcripts into `raw/` for wiki-ingest.

**Acceptance Criteria:**
- Transcripts from sprint planning, retro, and stakeholder meetings are ingested
- Jira ticket references are linked
- Speaker names mapped to team member identifiers
- Ingestion runs within 30-day transcript retention window

**Blockers:** Teams Premium license only on 20 seats — only management/lead meetings are transcribed
**Notes:** Quarterly planning meetings need manual `/se:wiki-ingest` trigger since they happen infrequently.

---

## DEMO-485 | Slack deploy approval audit trail
**Status:** To Do
**Assignee:** James Kim
**Priority:** High
**Story Points:** 3

**Description:**
When a tech lead reacts with :rocket: to approve a production deploy, the bot should:
1. Reply in the deploy thread: "Production deploy approved by @{user}" with timestamp
2. Include a link to the CodePipeline execution
3. Log the approval in the audit table (who, when, which pipeline, which ticket)

Currently the :rocket: reaction triggers the approval but there's no visible confirmation or audit trail.

**Acceptance Criteria:**
- Bot reply posted within 5 seconds of :rocket: reaction
- Reply includes approver name, pipeline link, and ticket number
- Approval logged to audit.deploy_approvals table
- Unauthorized users (non-tech-leads) get a DM saying they can't approve

**Blockers:** None
**Notes:** Sarah specifically requested audit trail for compliance reasons.

---

## Sprint 14 Goals
1. DORA metrics backend + frontend dashboard live (DEMO-478 + DEMO-451)
2. Notification improvements shipped (DEMO-470, DEMO-471, DEMO-472, DEMO-475)
3. Deploy approval audit trail (DEMO-485)
4. Teams transcript ingestion running (DEMO-482)
5. Runbook for adding new services (DEMO-461)

## Sprint 14 Risks
- DEMO-478 schema migration could be complex if denormalization requires backfilling existing deployment records
- Teams transcript API has known issues with 30-day retention — need to validate before sprint end
- James split across notification improvements AND approval audit trail — capacity concern

## Dependencies
- DEMO-451 (dashboard frontend, carried) depends on DEMO-478 (metrics backend)
- DEMO-461 (runbook) depends on Brian having access to all integration configurations
- DEMO-493, DEMO-494 (health check fixes for notification-service, webhook-router) are quick wins, can be done anytime
