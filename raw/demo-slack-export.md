# Slack Export — #deployment-automation
# Exported: 2026-04-04
# Channel: #deployment-automation (public)

---

**Marcus Rivera** — Apr 3, 2026, 2:14 PM
heads up — `user-service` deploy to prod just failed. CodePipeline shows the ECS task health check is failing. rolling back.

**Priya Patel** — Apr 3, 2026, 2:16 PM
which version? I pushed a change to the health endpoint this morning

**Marcus Rivera** — Apr 3, 2026, 2:17 PM
commit `a3f7bc2`. PR #247 "Add Redis connection check to health endpoint" — that's yours right?

**Priya Patel** — Apr 3, 2026, 2:18 PM
yeah that's mine. oh no. the health endpoint now checks Redis connectivity and if Redis is unreachable it returns 503. but the ECS task starts before ElastiCache security group rules propagate. so the health check fails during the first 10-15 seconds.

**Marcus Rivera** — Apr 3, 2026, 2:19 PM
so the deployment health check hits the health endpoint, gets 503 because Redis isn't reachable yet, and rolls back?

**Priya Patel** — Apr 3, 2026, 2:20 PM
exactly. the ECS health check grace period is only 10 seconds. we need to either increase the grace period or make the Redis check in the health endpoint non-fatal during startup.

**James Kim** — Apr 3, 2026, 2:22 PM
can confirm — I see the same pattern in the notification-service logs from last week. the health endpoint was returning 200 because it didn't check Redis. now it checks Redis and fails during cold start. DEMO-489 ?

**Marcus Rivera** — Apr 3, 2026, 2:23 PM
yeah create a ticket. this is blocking the user-service deploy.

**Priya Patel** — Apr 3, 2026, 2:25 PM
created DEMO-489: "Health endpoint Redis check fails during ECS cold start"
fix options:
1. increase ECS health check grace period to 30s (quick fix)
2. make health endpoint return 200 with degraded status during startup (better fix)
3. add a readiness probe separate from the liveness probe (proper fix but more work)

**Sarah Chen** — Apr 3, 2026, 2:28 PM
go with option 2 for now, file a follow-up for option 3. we need user-service deployed today — there's a customer demo at 4.

**Priya Patel** — Apr 3, 2026, 2:29 PM
on it

**Marcus Rivera** — Apr 3, 2026, 2:31 PM
@brian FYI this is a good one for the expertise file. Redis health check + ECS startup timing is going to bite us on every service.

**Brian** — Apr 3, 2026, 2:33 PM
noted. I'll run `/se:self-improve demo-corp` after the fix lands — this should get captured as an architecture gotcha.

**Priya Patel** — Apr 3, 2026, 2:47 PM
PR up: #251 "Make Redis health check non-fatal during startup grace period"
health endpoint returns `{"status": "starting", "redis": "connecting"}` for first 30s, then switches to normal behavior. if Redis is still unreachable after 30s, it returns 503.

**Marcus Rivera** — Apr 3, 2026, 2:48 PM
approved. merging.

**James Kim** — Apr 3, 2026, 2:52 PM
CI passed. deploying to staging now.

**Marcus Rivera** — Apr 3, 2026, 3:01 PM
staging looks good. health endpoint returns "starting" for about 8 seconds then switches to "healthy". deploying to prod.

**Priya Patel** — Apr 3, 2026, 3:14 PM
prod deploy successful. user-service is live. DEMO-489 done.

**Marcus Rivera** — Apr 3, 2026, 3:15 PM
:rocket: nice. 47 minutes from incident to fix in prod. that's way better than last month's 4-hour deploy incident.

**Sarah Chen** — Apr 3, 2026, 3:17 PM
that's exactly the kind of improvement I want to see in the DORA metrics dashboard when it's ready.

**James Kim** — Apr 3, 2026, 3:19 PM
created DEMO-492: "Add readiness probe separate from liveness probe on all services" — the proper fix Priya mentioned. putting it in the backlog for next sprint.

**Marcus Rivera** — Apr 3, 2026, 3:20 PM
good. also @priya can you add the same startup grace period logic to notification-service and webhook-router? don't want the same issue there.

**Priya Patel** — Apr 3, 2026, 3:22 PM
DEMO-493 and DEMO-494 created. I'll batch those together.
