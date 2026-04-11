# Raw Meeting Transcript — Sprint 14 Planning
# Source: Microsoft Teams recording, auto-transcribed
# Meeting: Sprint 14 Planning — Deployment Automation
# Date: 2026-04-07, 10:00 AM ET
# Duration: 47 minutes
# Participants: Sarah Chen (CTO), Marcus Rivera (Tech Lead), Priya Patel (Sr Backend), James Kim (Sr Frontend), Brian (Consultant)

---

[00:00:12] Sarah Chen: Alright let's get started. Marcus can you pull up the board?

[00:00:18] Marcus Rivera: Yeah one sec. OK so Sprint 13 we closed 34 of 38 tickets. The 4 that carried over are all in the deploy automation epic.

[00:00:31] Sarah Chen: Which ones?

[00:00:34] Marcus Rivera: DEMO-445 is the Datadog deploy markers. Priya had it but got pulled into that Redis incident on Tuesday. DEMO-451 is the DORA metrics dashboard — James has the frontend but we're blocked on the backend aggregation query. DEMO-458 is the LaunchDarkly integration and DEMO-461 is the runbook.

[00:00:58] Sarah Chen: The Redis thing — is that resolved?

[00:01:02] Priya Patel: Yeah, it was the ElastiCache failover during the maintenance window. We didn't have a circuit breaker on the Redis reads in the auth middleware so when Redis went down for like 12 seconds every API call failed. I put in a fallback that skips cache and validates the token directly with Okta. It's slower, about 200ms instead of 2ms, but at least it doesn't hard-fail.

[00:01:28] Sarah Chen: That should probably be a pattern across all our services not just the auth middleware.

[00:01:33] Brian: Agreed. I'd recommend we file that as a wiki page — it's a reusable pattern. I can run `/se:wiki-file redis-circuit-breaker` after this meeting to capture it.

[00:01:42] Sarah Chen: Do that.

[00:01:45] Marcus Rivera: OK so for Sprint 14. We have 22 tickets in the backlog for deploy automation. I'm proposing we pull in 18. The big ones are—

[00:01:56] Marcus Rivera: DEMO-470 through DEMO-475 are all the notification improvements. The Block Kit pagination thing, the thread management fix, and the private channel health check. James, these are yours right?

[00:02:09] James Kim: Yeah. DEMO-470 is mostly done, the Block Kit pagination. I'm hitting an issue with Slack's unfurl behavior — when we paginate a deploy summary into a thread, the parent message unfurl shows a preview of the thread reply which looks weird. I might need to disable unfurls on the parent.

[00:02:28] Marcus Rivera: Can you timebox that? Don't spend more than half a day on unfurl behavior.

[00:02:33] James Kim: Yeah fair.

[00:02:36] Marcus Rivera: DEMO-478 is the big one — the DORA metrics aggregation. Priya, you're picking this up?

[00:02:43] Priya Patel: Yeah. So the issue is that CodePipeline events don't have a direct correlation to Jira tickets. We correlate via the Git commit SHA — the commit references the PR which references the branch which has the DEMO-xxx ticket number. But that's a 4-hop lookup. I'm thinking we just denormalize it — when webhook-router processes a GitHub push event, we write the ticket number directly into the deployments table alongside the commit SHA. Then the DORA query is a simple join.

[00:03:15] Brian: That's the right call. Denormalize at write time, keep reads fast. The DORA dashboard is going to be hit constantly — Marcus mentioned the team checks it multiple times a day already.

[00:03:27] Sarah Chen: Multiple times a day and it doesn't even exist yet. [laughs]

[00:03:31] Marcus Rivera: I keep refreshing a Datadog dashboard that has deployment frequency but no lead time or failure rate. It's just a graph of "things happened."

[00:03:40] Brian: Once DEMO-478 lands, that dashboard becomes real. Lead time is PR-merge-to-prod-deploy timestamp delta. Failure rate is deploys that trigger a rollback within 30 minutes. Recovery time is rollback-to-next-successful-deploy.

[00:03:58] Sarah Chen: What about DEMO-461 the runbook? Who's writing that?

[00:04:03] Marcus Rivera: I was going to ask Brian actually. The runbook should cover how to add a new service to the pipeline. Right now only Priya and I know how to do it and we're the bottleneck.

[00:04:15] Brian: I'll write it. I'll use the session notes from our integration work. Actually, I should run `/se:brief demo-corp` and use that as the starting point — it'll have the current state of everything.

[00:04:28] Sarah Chen: Speaking of which, that expertise file thing you set up — it caught the Redis issue before I even heard about it. Priya logged it as an observation and it showed up in the next self-improve run.

[00:04:42] Brian: That's the self-learn loop working. `/se:self-improve demo-corp` validates observations against the current state. The Redis circuit breaker observation will get promoted to the architecture section once we verify the fix is deployed.

[00:04:58] Priya Patel: Quick question — DEMO-482 is the Teams transcript ingestion. We found out transcripts 404 after 30 days. Our sprint retros are biweekly so we should be fine but the quarterly planning meetings might get missed. Should I set up a more aggressive polling interval for those?

[00:05:16] Brian: Set the poll to every 15 minutes for all meetings. The 30-day clock is the hard constraint — as long as we ingest within that window, we're fine. For quarterly planning specifically, maybe trigger a manual ingest right after the meeting via `/se:wiki-ingest`.

[00:05:32] Marcus Rivera: OK that's DEMO-482. Last big one — DEMO-485 is the Slack approval workflow improvements. Right now the :rocket: reaction works but there's no confirmation that the approval went through. You react and then... hope?

[00:05:48] James Kim: I can add a bot reply to the thread that confirms "Production deploy approved by @marcus" with a link to the CodePipeline execution. That way there's a paper trail.

[00:05:59] Sarah Chen: Yes do that. Audit trail is important.

[00:06:04] Marcus Rivera: Alright, I think we're good on the sprint plan. 18 tickets, 4 carried over from last sprint, 14 new. Anybody have concerns about capacity?

[00:06:14] Priya Patel: I might need help on DEMO-478 if the denormalization turns out to be more complex than expected. The deployments table schema change needs a migration and I don't want to mess up the production data.

[00:06:27] Marcus Rivera: Flag it by Wednesday if you need help. I can pair with you Thursday.

[00:06:32] Sarah Chen: Good. Let's ship it. Brian — that wiki-file thing, can you also capture the DORA metrics definitions? I want everyone aligned on how we calculate lead time and failure rate.

[00:06:44] Brian: Will do. `/se:wiki-file dora-metrics-definitions` after the meeting.

[00:06:50] Sarah Chen: Perfect. Let's go.

[recording ends]

---

## Action items (extracted from transcript):
- [ ] Brian: `/se:wiki-file redis-circuit-breaker` — capture Redis failover pattern
- [ ] Brian: `/se:wiki-file dora-metrics-definitions` — capture DORA metric calculations
- [ ] Brian: Write runbook for adding new service to pipeline (DEMO-461)
- [ ] Brian: Run `/se:brief demo-corp` for runbook starting point
- [ ] James: DEMO-470 Block Kit pagination — timebox unfurl issue to half day
- [ ] Priya: DEMO-478 DORA metrics aggregation — denormalize ticket number at write time
- [ ] Priya: Flag by Wednesday if DEMO-478 needs pairing help
- [ ] James: DEMO-485 Add approval confirmation bot reply with audit trail
- [ ] Priya: DEMO-482 Teams transcript ingestion — 15-min poll interval
