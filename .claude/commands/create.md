---
allowed-tools: Read, Write, Edit, Bash
description: Create a new client — prompts progressively for what the SE knows, creates config files, then hands off to /discover
argument-hint: <client-name>
---

# SE: Create

Sets up a brand new client directory. Only the client name is required to start —
everything else is prompted progressively and anything unknown is marked TODO.
Creates `client.yaml` and `.env`, then hands off to `/discover`.

## Variables

CLIENT: $ARGUMENTS
CLIENT_DIR: clients/CLIENT

## Instructions

### Step 1 — Check if client already exists

```bash
ls clients/CLIENT/ 2>/dev/null && echo "EXISTS" || echo "NEW"
```

If EXISTS: stop and tell the user:
> `clients/CLIENT/` already exists. Use `/discover CLIENT` to refresh it, or `/brief CLIENT` to get a summary.

If CLIENT is empty: ask for the client name and stop.

If NEW: continue.

---

### Step 2 — Ask only what's needed, progressively

Ask these questions **one group at a time**, in order. Stop asking if the SE says they don't know yet — create the files with what's available and mark the rest TODO.

**Group A — always ask first:**
```
Setting up: CLIENT

1. Display name — full client/project name (e.g. "Acme Corp") — or skip
2. Is the tenant created yet? (yes / no)
3. Jira project key — if the space exists (e.g. "BH") — or skip
4. Slack channel — if created (e.g. "client_example") — or skip
```

**If tenant = yes, ask Group B:**
```
5. Tenant ID — the subdomain (e.g. "bp-hokies" for bp-hokies.my.platform.io)
6. Do you have API credentials yet? (yes / no)
```

**If credentials = yes, ask Group C:**
```
7. client_id — from tenant Settings > API Keys
8. client_secret
```

That's it. Don't ask about prod tenant, industry, or anything else unless the SE volunteers it.

---

### Step 3 — Create files immediately with what's known

```bash
mkdir -p clients/CLIENT
```

**Create `clients/CLIENT/client.yaml`:**

Fill in everything provided. Use `~` and a `# TODO` comment for everything not provided yet.

```yaml
# clients/CLIENT/client.yaml
# ⚠️  GITIGNORED — never commit this file.

client:
  name: CLIENT
  display_name: {answer 1 or ~}          # TODO: fill in if skipped

jira:
  project_keys: [{answer 3 or []}]       # TODO: add when Jira project is created

slack:
  channel: {answer 4 or ~}              # TODO: add when Slack channel is created
  channels: []

tenant:
  dev:
    id: {answer 5 or ~}                  # TODO: fill in when tenant is provisioned
    native_object_url: {derived from id or ~}
    auth_token_url: {derived from id or ~}
    client_id: ${ENVPREFIX_CLIENT_ID}
    client_secret: ${ENVPREFIX_CLIENT_SECRET}
    bearer_token: ${ENVPREFIX_DEV_TOKEN}
    management_token: ${ENVPREFIX_MGT_TOKEN}
    access: readonly

  prod:
    id: ~                                # TODO: add when prod tenant is ready
    native_object_url: ~
    access: readonly
```

Where ENVPREFIX = CLIENT uppercased with underscores (e.g. `bp-hokies` → `BP_HOKIES`).

**Create `clients/CLIENT/.env`:**

```bash
# clients/CLIENT/.env
# ⚠️  GITIGNORED — never commit this file.
# Source before running commands: source clients/CLIENT/.env

ENVPREFIX_CLIENT_ID={answer 7 or blank}
ENVPREFIX_CLIENT_SECRET={answer 8 or blank}

# Bearer token — generated automatically once credentials are set
# Run: source clients/CLIENT/.env && curl -s -X POST https://auth.{tenant-id}.my.platform.io/oauth/token \
#   -H "Content-Type: application/json" \
#   -d '{"grant_type":"client_credentials","client_id":"...","client_secret":"...","audience":"https://platform/no-api"}'
ENVPREFIX_DEV_TOKEN=

# Management token — copy Authorization header from browser dev tools (~24h expiry)
ENVPREFIX_MGT_TOKEN=
```

---

### Step 4 — Verify .gitignore

```bash
git check-ignore -v clients/CLIENT/.env clients/CLIENT/client.yaml 2>/dev/null
```

If either is NOT gitignored, warn the user before continuing.

---

### Step 5 — Generate bearer token if credentials were provided

If client_id and client_secret were provided AND tenant ID is known, generate the bearer token now:

```bash
curl -s -X POST https://auth.{tenant-id}.my.platform.io/oauth/token \
  -H "Content-Type: application/json" \
  -d '{"grant_type":"client_credentials","client_id":"{client_id}","client_secret":"{client_secret}","audience":"https://platform/no-api"}'
```

Write the `access_token` value to `ENVPREFIX_DEV_TOKEN` in `.env`.

If credentials or tenant ID are missing, tell the SE what they'll need to do when they have them:
```
When you have credentials:
  1. Add to clients/CLIENT/.env: ENVPREFIX_CLIENT_ID and ENVPREFIX_CLIENT_SECRET
  2. Run /create CLIENT again — it will generate the bearer token and run discovery
```

---

### Step 6 — Run discovery if tenant + credentials are ready

If tenant ID and bearer token are set, run `/discover CLIENT` automatically.

If not: stop and report what's missing so the SE knows what to come back with.

---

### Step 7 — Report

```
✅ Client created: CLIENT

Files created:
  clients/CLIENT/client.yaml   ← gitignored
  clients/CLIENT/.env          ← gitignored

Status:
  Tenant:      {configured / TODO — not provisioned yet}
  Credentials: {set + bearer token generated / TODO — not provided yet}
  Jira:        {BH / TODO — not created yet}
  Slack:       {#channel / TODO — not created yet}

{If ready:}   Running /discover CLIENT now...
{If not:}     Come back with the missing pieces and re-run /create CLIENT.
              It will pick up where you left off.
```
