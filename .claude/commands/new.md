---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, Task, Skill
description: Scaffold a new application in apps/ with expertise.yaml initialized and expertise bootstrapped
argument-hint: <app-name> <description>
---

# App: New

Scaffold a new application under `apps/APP_NAME`, initialize its expertise.yaml, plan and build the scaffold, then establish baseline expertise. Follow `Instructions` and work through the `Workflow`.

## Variables

ARGUMENTS: $ARGUMENTS
APP_NAME: first word of ARGUMENTS
APP_DESCRIPTION: everything after the first word of ARGUMENTS
APP_DIR: apps/APP_NAME
EXPERTISE_DIR: .claude/commands/apps/APP_NAME
SPECS_DIR: specs/

## Instructions

- IMPORTANT: Parse ARGUMENTS immediately: APP_NAME = first whitespace-delimited token; APP_DESCRIPTION = remainder of the string after that token. If either is empty after parsing, stop and ask for both.
- APP_NAME should be lowercase kebab-case (e.g. `listing-launch`, `site-builder`)
- **Never assume a stack silently.** If APP_DESCRIPTION doesn't make the stack obvious, stop and present options (see Step 1). The user's time is wasted scaffolding the wrong stack.
- The scaffold plan should be minimal — directory structure, entry points, env config, health check
- Do NOT over-engineer the scaffold — the user will add features via `/feature`

## Stack Decision Guide

Present these options when not explicitly specified. Show name, one-line pitch, and key tradeoffs.

### Backend Framework
| Option | Pitch | Strengths | Weaknesses |
|---|---|---|---|
| **Hono** (TypeScript) | FastAPI for TypeScript — minimal, fast, edge-ready | Tiny bundle, great DX, first-class Zod/Prisma/Drizzle, runs on Bun/Node/edge | Smaller ecosystem than Express, newer |
| **FastAPI** (Python) | Industry standard for Python APIs | Mature, async-first, excellent for AI/ML-heavy workloads, asyncpg native | Python-only, no Prisma, heavier than Hono for pure API work |
| **Express** (TypeScript) | The safe choice — most popular Node framework | Massive ecosystem, tons of examples, well-understood | Verbose, no built-in validation, requires more boilerplate |
| **Fastify** (TypeScript) | Express with speed and schema baked in | Fast, JSON schema validation built-in, good plugin system | Steeper learning curve, smaller ecosystem than Express |

**Default recommendation**: Hono (TypeScript) — unless the app is AI/ML heavy (prefer FastAPI) or the user says otherwise.

### ORM / Database Access (only when database domain detected)
| Option | Pitch | Strengths | Weaknesses |
|---|---|---|---|
| **Prisma** | Best DX ORM — schema-first, auto-generated types | Type-safe queries, excellent migrations, great Neon integration, readable schema | Slightly slower than raw, abstraction can hide complex queries |
| **Drizzle** | SQL-first TypeScript ORM | Lightest weight, SQL-like syntax, great for Neon serverless driver, no magic | Less hand-holding than Prisma, smaller community |
| **Raw SQL** (postgres.js / asyncpg) | Full control, no abstractions | Fastest, no overhead, best for complex queries | No type safety, manual migration management, more boilerplate |

**Default recommendation**: Prisma — unless performance is critical (Drizzle) or the app is Python-only (raw asyncpg).

### Frontend Framework
| Option | Pitch | Strengths | Weaknesses |
|---|---|---|---|
| **Vue 3** | Progressive framework — easy to add, easy to reason about | Composition API, great DX, smaller bundle than React, Pinia for state | Smaller ecosystem and job market than React |
| **React** | The industry default | Largest ecosystem, most libraries, most hiring | Verbose JSX, needs more setup (state, routing), heavier |
| **Svelte** | Write less, ship less | Simplest syntax, smallest bundle, no virtual DOM | Smallest ecosystem, fewer integrations |

**Default recommendation**: Vue 3 — unless the user prefers React or the project needs a specific React library.

---

## Workflow

### Step 1: Validate and Detect

1. Confirm APP_NAME is provided and lowercase kebab-case (`^[a-z0-9-]+$`); stop if not
2. Confirm APP_DESCRIPTION has at least 3 words; if truncated, ask user to re-run with quotes
3. **Idempotency check**: if `apps/APP_NAME/` already exists, stop and warn: "App 'APP_NAME' already exists. Use /feature to add features, or delete the directory to re-scaffold."
4. Detect domains from APP_DESCRIPTION:
   - Mentions "database", "postgres", "store", "persist", "neon", "sql" → database domain
   - Mentions "realtime", "websocket", "live", "stream", "push" → websocket domain

5. **Stack resolution** — for each dimension below, check if it's explicit in APP_DESCRIPTION or the user's message. If NOT explicit, stop and present the options table for that dimension, then wait for a choice:
   - **Backend**: Is a specific framework/language mentioned? If not, present Backend options and ask.
   - **ORM** (only if database domain): Is Prisma/Drizzle/raw mentioned? If not, present ORM options and ask.
   - **Frontend**: Is a framework mentioned? If not, present Frontend options and ask. If the app is API-only (no UI implied), ask if a frontend is needed at all.

   Once all choices are confirmed, report the full detected configuration and ask for a final go-ahead before scaffolding.

### Step 2: Scaffold Directory Structure

Scaffold based on confirmed stack choices.

#### TypeScript Backend (Hono)
```
apps/APP_NAME/
├── backend/
│   ├── src/
│   │   └── index.ts          (Hono entry point, /health endpoint)
│   ├── package.json          (hono, @hono/node-server, typescript, tsx)
│   ├── tsconfig.json
│   └── .env.sample
├── frontend/                 (if frontend requested)
│   ├── src/
│   │   ├── App.vue / App.tsx
│   │   ├── main.ts
│   │   └── stores/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

**If database + Prisma**: add to backend:
```
backend/
└── prisma/
    └── schema.prisma         (datasource + generator + empty models scaffold)
```
Wire Prisma client into `src/index.ts` and add `prisma generate` + `prisma db push` to README.

**If database + Drizzle**: add `drizzle/schema.ts` + `drizzle.config.ts`.

**If database + raw SQL**: add `src/db.ts` with postgres.js pool, no schema file.

#### Python Backend (FastAPI)
```
apps/APP_NAME/
├── backend/
│   ├── main.py               (FastAPI entry point, /health endpoint)
│   ├── modules/
│   ├── tests/
│   │   └── conftest.py
│   ├── requirements.txt
│   └── .env.sample
└── ...
```

**If database**: add `migrations/schema.sql` and wire auto-apply into lifespan:
```python
schema = Path(__file__).parent / "migrations" / "schema.sql"
if schema.exists() and schema.read_text().strip():
    async with app.state.db.acquire() as conn:
        await conn.execute(schema.read_text())
```

#### Frontend (Vue 3)
```
frontend/
├── src/
│   ├── App.vue
│   ├── main.ts
│   └── stores/
├── package.json              (vue, vue-router, pinia)
└── vite.config.ts            (proxy /api → backend port)
```

#### Frontend (React)
```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── components/
├── package.json              (react, react-dom, react-router-dom)
└── vite.config.ts
```

### Step 3: Initialize Expert Domain
- Create `EXPERTISE_DIR/` directory
- Copy `.claude/commands/apps/_template/improve.md` → `EXPERTISE_DIR/improve.md`
  - Replace all `{{APP_NAME}}` placeholders with APP_NAME
- Copy `.claude/commands/apps/_template/question.md` → `EXPERTISE_DIR/question.md`
  - Replace all `{{APP_NAME}}` placeholders with APP_NAME
- Copy `.claude/commands/apps/_template/plan.md` → `EXPERTISE_DIR/plan.md`
  - Replace all `{{APP_NAME}}` placeholders with APP_NAME
- Create `EXPERTISE_DIR/expertise.yaml` from `.claude/commands/apps/_template/expertise.yaml.template`
  - Replace: `{{APP_NAME}}` → APP_NAME
  - Replace: `{{APP_DESCRIPTION}}` → APP_DESCRIPTION
  - Replace: `{{DATE}}` → today's date
  - Fill in confirmed stack values (backend, frontend, orm, domains)
- **Verify substitution**:
  ```bash
  grep -n '{{' EXPERTISE_DIR/expertise.yaml EXPERTISE_DIR/improve.md EXPERTISE_DIR/question.md EXPERTISE_DIR/plan.md
  ```
  If any `{{...}}` patterns remain, fix before continuing.

### Step 4: Plan the Scaffold
Run `/plan "Scaffold APP_NAME: APP_DESCRIPTION. Stack: [confirmed stack]. Create minimal working app with health endpoint, env config, and app-specific README."` and note the plan file path.

### Step 5: Build the Scaffold
Run `/build <plan-path>` from Step 4.

### Step 6: Baseline Self-Improve
Run `/improve APP_NAME false` to establish the initial expertise baseline.

### Step 7: Initialize Git Tracking
```bash
git add apps/APP_NAME/ .claude/commands/apps/APP_NAME/ specs/
```
(Do not commit — leave staging to the user.)

## Report

```
✅ App Created: APP_NAME

Description: APP_DESCRIPTION
Location: apps/APP_NAME/
Expert Domain: .claude/commands/apps/APP_NAME/

Confirmed Stack:
- Backend: [framework + language]
- ORM/DB: [prisma | drizzle | raw sql | none]
- Frontend: [vue3 | react | svelte | none]
- Domains: [database | websocket | none]

Files Created:
- [list key scaffold files]

Expert Commands Available:
- /experts:APP_NAME:question <question>
- /experts:APP_NAME:self-improve [check_git_diff]
- /experts:APP_NAME:plan <request>

Next Step:
  /feature APP_NAME "<your first feature>"
```
