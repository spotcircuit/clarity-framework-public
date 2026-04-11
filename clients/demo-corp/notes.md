# Demo Corp — Session Notes

---

## Session 1 — Jira API Exploration (2026-03-20, ~3 hours)

### What happened

Ran `/se:create demo-corp` and `/se:discover demo-corp`. Phase 0 generated. Then dove into the Jira integration.

Set up a Jira OAuth 2.0 (3LO) app in Atlassian Developer Console. The 3LO flow is more complex than expected — requires an initial user authorization redirect even for server-to-server use. Ended up using a long-lived refresh token stored in Secrets Manager.

Explored the webhook payload for `jira:issue_updated`. The payload includes a `changelog` object showing which fields changed, but it does NOT include the full issue. If you need custom field values (like "Deploy Target Environment"), you have to make a separate `GET /rest/api/3/issue/{key}` call. This is documented but easy to miss.

### Webhook payload quirks discovered

1. **Duplicate webhooks.** Jira retries on 5xx responses. If webhook-router takes >10s to respond (e.g., downstream Slack call is slow), Jira assumes failure and retries. Got duplicate events 3 times during testing. Fix: dedup by `webhookEvent` + `timestamp` within a 60-second window.

2. **Transition IDs are instance-specific.** The transition ID for "In Progress → In Review" is `31` in Demo Corp's Jira. Hardcoding this is fragile — if they modify the workflow, it breaks. Correct approach: call `GET /rest/api/3/issue/{key}/transitions` to get available transitions by name, then use the ID from the response.

3. **Custom fields are opaque.** "Deploy Target Environment" is `customfield_10089`. No way to discover this from the API without listing all fields via `GET /rest/api/3/field`. Built a field-mapping config in webhook-router so we don't hardcode field IDs.

4. **Sprint data is in the Agile API.** Sprint details (start date, end date, goal) are not in the core REST API. Need to use `/rest/agile/1.0/sprint/{sprintId}`. Different base path, different auth scope.

### Observations logged

- "Jira webhook payload excludes full issue data — must GET issue separately for custom fields"
- "Jira webhooks retry on 5xx and slow responses — need dedup layer"
- "Transition IDs are not portable across Jira instances — always look up by name"
- "Custom field IDs are instance-specific — customfield_10089 = Deploy Target Environment in Demo Corp"

---

## Session 2 — Slack Bot & Notification Service (2026-03-24, ~2.5 hours)

### What happened

Built the notification-service Slack integration. Created a Slack app with bot token (xoxb-*), installed to workspace with scopes: `chat:write`, `channels:read`, `users:read`, `reactions:write`.

First deploy notification worked immediately — `chat.postMessage` to #deploys. Clean.

Then the problems started.

### Rate limiting

Slack's rate limit for `chat.postMessage` is 1 message per second per channel. During a burst deploy (3 services deploying simultaneously from the same PR), we tried to post 3 messages to #deploys within 200ms. Got rate-limited on the second call.

Fix: notification-service queues messages per channel with 1.1s spacing between sends. The extra 100ms buffer prevents edge cases.

### Thread management

Deploy notifications follow a pattern:
1. Initial message: "DEMO-456: Deploying `user-service` to staging"
2. Thread reply: CI status, test results
3. Thread reply: "Deployed to staging successfully"
4. Thread reply: "Deployed to prod — live"

The gotcha: **thread replies do not notify channel members** by default. If someone isn't watching the thread, they miss the "deployed to prod" update. You have to set `reply_broadcast=true` on the final message to post it to the channel AND the thread.

Decision: thread replies for intermediate updates (CI, staging), broadcast reply for the final prod deploy confirmation.

### The private channel incident

Notification-service was configured to also post to #incidents (private channel). Messages silently failed for 2 hours. The error from Slack was `channel_not_found` — NOT `not_in_channel`. Extremely misleading. The bot token was valid, the channel existed, but the bot had not been invited to the private channel.

Fix: added a startup health check that verifies the bot can access all configured channels via `conversations.info`. Logs a clear error if any channel is inaccessible.

### Block Kit limits

Built a rich deploy summary using Slack Block Kit (sections, fields, context blocks). Worked great for single-service deploys. Then tested a "release train" deploy (8 services from one epic). The message had 62 blocks. Slack's limit is 50 blocks per message.

Fix: if deploy summary exceeds 40 blocks, paginate into summary (first message) and details (thread reply).

### Observations logged

- "Slack chat.postMessage rate limit is 1/sec per channel — queue with 1.1s spacing"
- "Thread replies require reply_broadcast=true for channel visibility on final status"
- "Private channel access fails with misleading channel_not_found — add startup channel verification"
- "Block Kit limit is 50 blocks — paginate deploy summaries over 40 blocks"

---

## Session 3 — Teams Meeting Integration (2026-03-28, ~2 hours)

### What happened

Demo Corp uses Teams for sprint planning, retro, and stakeholder meetings. CTO wants meeting transcripts ingested into the wiki so that decisions and action items don't get lost.

Set up an Azure AD app registration with Microsoft Graph permissions: `OnlineMeetings.Read`, `CallRecords.Read.All`, `OnlineMeetingTranscript.Read.All`.

### Transcript access

Graph API endpoint: `GET /me/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content`

The response is a `.vtt` (WebVTT) file. Looks like this:

```
WEBVTT

00:00:05.000 --> 00:00:08.500
<v Sarah Chen>Let's look at the sprint board. Marcus, where are we on DEMO-312?

00:00:09.200 --> 00:00:15.800
<v Marcus Rivera>DEMO-312 is in review. PR is up, waiting on Priya's review. Should merge today.

00:00:16.500 --> 00:00:22.000
<v Sarah Chen>Good. What about the deploy tracking? DEMO-345 was supposed to be done last sprint.
```

### Parsing issues

1. **Speaker attribution is by display name.** "Sarah Chen" in Teams doesn't map to "@sarah.chen" in Slack or "schen" in Jira. Built a name-mapping table in the notification-service config. Fragile — breaks when someone changes their Teams display name.

2. **Transcript availability delay.** Transcripts are not available immediately after the meeting ends. In testing, there was a 5-15 minute delay. The ingestion job needs to poll or use a webhook (Graph API supports change notifications for transcripts, but setup is complex).

3. **30-day retention.** Discovered that transcripts older than 30 days return 404 from the Graph API. This is not documented prominently. If we want to keep transcript data, we must ingest within the retention window.

4. **Teams Premium requirement.** Transcript API requires Teams Premium licenses. Demo Corp has 20 Premium seats (management + leads). Regular engineers' meetings are NOT transcribed. This limits coverage to sprint planning, retro, and stakeholder meetings.

### What we built

A transcript ingestion job that:
1. Polls for new transcripts every 15 minutes
2. Downloads VTT content
3. Extracts Jira ticket mentions (DEMO-\d+ pattern)
4. Maps speaker names to team members
5. Drops the processed transcript into `raw/` for `/se:wiki-ingest`

### Observations logged

- "Teams transcript API requires Premium license — only 20 seats at Demo Corp"
- "Transcripts available 5-15 min after meeting ends — poll, don't assume immediate availability"
- "VTT speaker names don't match Slack/Jira usernames — need mapping table"
- "Transcript 404 after 30 days — must ingest within retention window"

---

## Session 4 — CI/CD Pipeline Wiring (2026-04-02, ~3 hours)

### What happened

Wired up the full pipeline: Jira → GitHub → CodePipeline → Slack. This is the core integration — everything connects here.

### GitHub webhook setup

Created a GitHub App for the `democorp-eng` org. Subscribed to: `push`, `pull_request`, `check_run`, `deployment_status`.

The correlation logic: extract Jira ticket key from branch name (`feature/DEMO-456-add-redis-cache`) or PR title (`[DEMO-456] Add Redis session cache`). Regex: `DEMO-\d+`.

**Gotcha:** `check_run` events fire 3 times per CI run: `queued`, `in_progress`, `completed`. Only care about `completed`. Without filtering, notification-service was posting "CI running..." messages that added noise.

### CodePipeline EventBridge integration

CodePipeline sends state change events to EventBridge. We set up a rule to forward `CodePipeline Pipeline Execution State Change` and `CodePipeline Action Execution State Change` events to the webhook-router's SQS queue.

**Event delay.** EventBridge events arrive 30-90 seconds after the actual state change. This means the "deployed to staging" notification arrives about a minute after the deploy is live. Acceptable for tracking, but confusing during demos when someone deploys and then stares at Slack waiting.

**Action name truncation.** CodePipeline truncates action names to 100 characters. The service `notification-service-staging-deploy` becomes `notification-service-staging-dep` in events. Need to handle partial matching.

### The full loop working

Tested the complete flow end-to-end:

1. Created Jira ticket DEMO-467: "Add health check endpoint to deploy-service"
2. Created branch `feature/DEMO-467-health-check`
3. Opened PR — webhook-router received `pull_request.opened` event
   - Correlated to DEMO-467 via branch name
   - Jira auto-transitioned to "In Progress"
   - Slack posted to #deploys: "DEMO-467: PR opened for deploy-service"
4. PR merged — webhook-router received `pull_request.closed` (merged=true)
   - Jira transitioned to "In Review"
   - Slack thread reply: "PR merged, CI running"
5. CI passed — `check_run.completed` (conclusion=success)
   - Slack thread reply: "CI passed ✓"
6. CodePipeline deployed to staging — EventBridge event (~45s delay)
   - Slack thread reply: "Deployed to staging"
   - E2E smoke tests triggered
7. Manual approval (Slack reaction :rocket: on deploy message)
8. CodePipeline deployed to prod — EventBridge event (~60s delay)
   - Jira transitioned to "Done"
   - Slack broadcast reply: "DEMO-467 live in production ✓"
   - DORA metrics updated

Total time from PR merge to production: 18 minutes (previously ~2 days with manual tracking).

### Deployment approval via Slack

Built a Slack interaction where the deploy message to #deploys includes a :rocket: reaction prompt. When a tech lead reacts with :rocket:, the notification-service calls CodePipeline's `put-approval-result` API to approve the production deploy.

This replaces the previous process: log into AWS Console → find the pipeline → click Approve → paste a comment.

Marcus (tech lead) tested it: "I just approved a production deploy from my phone while walking to get coffee. This is going to change everything."

### Observations logged

- "Full pipeline loop working: PR → CI → staging → prod → Slack notification in 18 minutes"
- "CodePipeline events delayed 30-90s via EventBridge — acceptable for tracking"
- "check_run fires 3x per CI run — filter on completed status only"
- "Slack reaction-based deploy approval replaces AWS Console workflow"
- "CodePipeline action names truncated to 100 chars — need partial matching"
