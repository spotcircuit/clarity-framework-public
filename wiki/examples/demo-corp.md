# Demo Corp — Deployment Automation Knowledge

#demo-corp #deployment #integrations #dora

Synthesized knowledge from sprint planning, Slack discussions, and Jira tickets for the Demo Corp deployment automation engagement. This page captures patterns and decisions that emerged across multiple sources.

Source: raw/demo-meeting-transcript.md, raw/demo-slack-export.md, raw/demo-jira-notes.md
Ingested: 2026-04-08 via `/se:wiki-ingest`

---

## Architecture Pattern: Webhook Event Correlation

All deployment tracking depends on correlating events from Jira, GitHub, and CodePipeline back to a single Jira ticket key. The correlation chain:

1. Branch name: `feature/DEMO-XXX-description` (regex: `DEMO-\d+`)
2. PR title: `[DEMO-XXX] Description` (fallback)
3. Commit message (last resort)

Key decision from Session 4: **denormalize the ticket number at write time** in the deployments table. The 4-hop lookup (commit → PR → branch → ticket) is too expensive for the DORA metrics dashboard. Webhook-router now writes `jira_ticket_key` directly when processing GitHub push events.

## Integration Gotcha: ECS Health Check + Redis Cold Start

Discovered during a production incident on 2026-04-03 (DEMO-489). When a service health endpoint checks Redis connectivity, the check fails during ECS cold start because ElastiCache security group rules take 10-15 seconds to propagate. The ECS health check grace period (10s default) expires before Redis is reachable, causing a rollback.

**Pattern applied:** Health endpoint returns `{"status": "starting", "redis": "connecting"}` during a 30-second startup grace period. After grace period, normal health check behavior (503 if Redis unreachable). This pattern needs to be applied to all three services: deploy-service, notification-service, webhook-router.

Follow-up: DEMO-492 to implement proper readiness probes separate from liveness probes.

## DORA Metrics Definitions (Agreed in Sprint 14 Planning)

Definitions confirmed by CTO (Sarah Chen) in sprint planning meeting:

- **Deployment Frequency:** Count of successful production deploys per service per time period
- **Lead Time for Changes:** Median time from PR merge to production deploy (not from ticket creation)
- **Change Failure Rate:** Percentage of production deploys that trigger a rollback within 30 minutes
- **Mean Time to Recovery:** Median time from rollback event to next successful production deploy

API endpoint: `GET /api/metrics/dora?service=all&period=30d`

## Slack Notification Patterns

Learned from Sessions 2 and 4, validated in production:

| Event | Channel | Format |
|-------|---------|--------|
| PR opened | #deploys (thread) | "DEMO-XXX: PR opened for {service}" |
| CI passed | #deploys (thread reply) | "CI passed" (no broadcast) |
| Staging deploy | #deploys (thread reply) | "Deployed to staging" (no broadcast) |
| Prod deploy | #deploys (broadcast reply) | "DEMO-XXX live in production" (reply_broadcast=true) |
| Deploy failure | #incidents | Full Block Kit summary with rollback status |
| Approval | #deploys (thread reply) | "Production deploy approved by @{user}" + pipeline link |

Rate limit handling: 1.1s spacing between messages per channel. Block Kit messages paginated at 40 blocks (Slack limit is 50).

## Open Items

- CodePipeline execution history API returns max 100 results with no pagination cursor. Need local storage for history beyond 100 deploys.
- Slack bot token refresh fails silently when Okta session expires. Need health check endpoint.
- Teams transcript retention is 30 days. Quarterly planning meetings need manual ingestion trigger.

## Related

- [[redis-circuit-breaker]] -- the failover pattern from the Apr 3 incident
- [[dora-metrics-definitions]] -- detailed metric calculation methodology
- [[acme-integration]] -- different client, similar webhook dedup patterns in the Jira integration
