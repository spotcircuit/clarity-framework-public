---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, Task, Skill
description: Understand, document, and establish expertise for an existing app — produces expertise.yaml and prime context
argument-hint: <app-name>
---

# App: Takeover

Understand an existing app in `apps/APP_NAME/`, build or update its expertise domain, and produce a prime context file. After this command, the app is fully integrated into the forge framework and ready for `/feature`.

## Variables

APP_NAME: $ARGUMENTS
APP_DIR: apps/APP_NAME
EXPERTISE_DIR: .claude/commands/apps/APP_NAME
APP_DOCS_DIR: app_docs/
MAX_EXPERTISE_LINES: 1000

## Instructions

- IMPORTANT: If APP_NAME is empty, list `ls apps/` and ask which app to take over.
- Verify `apps/APP_NAME/` exists before proceeding.
- If `apps/APP_NAME/.forge/client.yaml` exists, execute the **Client Config Preamble** from `client_config_protocol.md` before any other steps — creates the feature branch + worktree, enforces readonly tenant mode if configured.
- This command is NON-DESTRUCTIVE — it reads and documents, never modifies app code.
- If an expertise file already exists, run a full validation pass (not from scratch).
- The output expertise.yaml should be written as a principal engineer: clear, concise, actionable.
- Prioritize: file locations, function signatures, key patterns, data models, known issues.
- The prime_APP_NAME.md should list ONLY the files an agent needs to read to be productive — not everything.

## Workflow

### Step 1: Verify App Exists
```bash
ls apps/APP_NAME/ 2>/dev/null || echo "NOT FOUND"
```
If NOT FOUND: stop, list `ls apps/` for available apps.

### Step 2: Discover Architecture
Run a comprehensive codebase scan:

```bash
find apps/APP_NAME -type f | grep -v node_modules | grep -v __pycache__ | grep -v .git | sort
```

Read (in this order):
1. `apps/APP_NAME/README.md` — if exists
2. `apps/APP_NAME/backend/main.py` or `apps/APP_NAME/backend/index.ts` — entry point
3. Any `requirements.txt` or `package.json` — detect stack and dependencies
4. Key module files (websocket_manager, database, services) — scan for patterns

Identify:
- Stack (Python/FastAPI, Node, Vue, React, etc.)
- Domains used (database, websocket, both, neither)
- Key architectural patterns
- Port numbers
- Environment variables required

### Step 3: Detailed File Scan
Run `/find_and_summarize APP_NAME *.py apps/APP_NAME` for Python apps.
Run `/find_and_summarize APP_NAME *.ts apps/APP_NAME` for TS apps.
(Output saved to `app_docs/find_and_summarize_APP_NAME.yaml`)

Read the output and identify:
- Core files (always read in prime)
- Backend-specific files
- Frontend-specific files
- Test files
- Configuration files

### Step 4: Create or Update Expertise

**If EXPERTISE_DIR/expertise.yaml does NOT exist:**
- Create `EXPERTISE_DIR/` directory
- Copy `_template` command files with APP_NAME substituted
- Build expertise.yaml from scratch using the discovery in Steps 2-3
- Structure: overview, key_files, architecture_patterns, key_operations, best_practices, known_issues
- Cap at MAX_EXPERTISE_LINES (1000)

**If EXPERTISE_DIR/expertise.yaml EXISTS:**
- Read the existing expertise
- Compare against current codebase (validate every claim)
- Update stale line counts, file paths, function signatures
- Add newly discovered files/patterns
- Remove obsolete sections
- Enforce MAX_EXPERTISE_LINES cap

Validate YAML after writing:
```bash
python3 -c "import yaml; yaml.safe_load(open('EXPERTISE_DIR/expertise.yaml'))"
```

### Step 5: Create Prime Context File
Create `.claude/commands/prime_APP_NAME.md`:

```markdown
# Prime: APP_NAME

Execute the `Run`, `Read` and `Report` sections to understand APP_NAME then summarize your understanding.

## Focus
- Primary focus: `apps/APP_NAME/*`

## Run
git ls-files apps/APP_NAME/

## Read

### Core (always read these):
- @apps/APP_NAME/README.md
- @apps/APP_NAME/backend/main.py
- [other core files from discovery]

### Backend (if working on backend):
- [backend key files]

### Frontend (if working on frontend):
- [frontend key files]

## Report
Summarize your understanding of APP_NAME.
```

### Step 6: Register Expert Commands
Ensure the following commands exist in `EXPERTISE_DIR/`:
- `question.md` (from _template if missing)
- `self-improve.md` (from _template if missing)
- `plan.md` (from _template if missing)

### Step 7: Finalize Client Workflow
If `apps/APP_NAME/.forge/client.yaml` exists and `git.workflow: feature_branch`, execute the **Client Config Postamble** from `client_config_protocol.md`: commit documentation changes, push branch, create PR to configured reviewer, clean up worktree.

### Step 8: Identify Gaps and Risks
Analyze the codebase for:
- Missing tests (endpoints with no test coverage)
- Missing documentation (undocumented modules)
- Security concerns (exposed secrets, missing auth)
- Technical debt (TODO comments, deprecated patterns)
- Missing error handling

## Report

```
✅ Takeover Complete: APP_NAME

Architecture:
- Stack: [backend + frontend]
- Domains: [database | websocket | none]
- Ports: backend:[N] frontend:[N]
- Entry: apps/APP_NAME/backend/main.py

Expert Domain: .claude/commands/apps/APP_NAME/
  - expertise.yaml: [N lines / 1000]
  - Commands: question, self-improve, plan

Prime Context: .claude/commands/prime_APP_NAME.md
  - Core files: [N]
  - Backend files: [N]
  - Frontend files: [N]

Codebase Summary: app_docs/find_and_summarize_APP_NAME.yaml

Gaps Identified:
- [gap 1]
- [gap 2]

Risks:
- [risk 1]

Ready for:
  /feature APP_NAME "<feature-request>"
  /experts:APP_NAME:question "<question>"
```
