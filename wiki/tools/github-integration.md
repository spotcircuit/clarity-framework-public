# GitHub Integration

#tools #github #mcp #code-context

Clarity works with GitHub through the MCP GitHub server in Claude Desktop and native git access in Claude Code. This gives `/discover`, `/review`, and `/test` direct access to repo structure, PR history, and CI results.

## Setup

### Claude Code (Built-in)

Claude Code has native git and GitHub CLI (`gh`) access. No additional setup needed if you have `gh` authenticated:

```bash
gh auth status
# Logged in to github.com as spotcircuit
```

Clarity commands automatically use `gh` for:
- Reading repo structure and recent commits
- Creating and reviewing pull requests
- Checking CI status
- Reading issue and PR comments

### Claude Desktop (MCP Server)

Add the GitHub MCP server to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

Required token scopes: `repo`, `read:org`, `read:discussion`.

## What /discover Reads from GitHub

When you run `/discover {app}`, Clarity examines the repo to seed expertise.yaml:

| Data | Source | Where It Goes |
|---|---|---|
| Directory structure | `git ls-tree` | `architecture.structure` |
| Language breakdown | GitHub API | `architecture.languages` |
| Recent commits (30 days) | `git log` | `project_health.commit_frequency` |
| Open PRs | `gh pr list` | `project_health.open_prs` |
| CI workflow status | `gh run list` | `project_health.ci_status` |
| Branch protection rules | GitHub API | `project_health.branch_protection` |
| Issue patterns | `gh issue list` | `project_health.issue_patterns` |
| CODEOWNERS | File read | `team.ownership` |
| README + docs | File read | `documentation.overview` |

### Example expertise.yaml section

After `/discover` with GitHub access:

```yaml
project_health:
  repo: spotcircuit/demo-api
  default_branch: main
  commit_frequency:
    last_30_days: 47
    contributors: 3
    most_active: "@brian (28 commits)"
  open_prs:
    count: 2
    oldest_days: 3
    review_requested: 1
  ci_status:
    last_10_runs:
      passed: 8
      failed: 2
      failure_pattern: "test_metrics flaky on Postgres connection timeout"
  branch_protection:
    main:
      require_pr: true
      required_reviews: 1
      require_ci: true
      enforce_admins: false
```

## What /review Does

`/review` integrates with the PR workflow:

```
/review

Reviewing PR #42: "Add deployment rollback endpoint"

Files changed: 6 (+312, -14)
  app/routes/deployments.py        +45  (new rollback route)
  app/services/rollback_service.py +128 (new file)
  app/models/deployment.py         +8   (added rolled_back status)
  tests/test_rollback_api.py       +117 (new file, 8 tests)
  app/core/database.py             +6   (transaction helper)
  alembic/versions/003_add_...py   +8   (migration)

Review:
  [OK] No secrets or credentials in diff
  [OK] New route follows existing patterns (auth, error handling)
  [OK] Tests cover happy path + error cases
  [OK] Migration is reversible (has downgrade)
  [WARN] rollback_service.py line 42: bare except clause -- should catch specific exception
  [WARN] No test for concurrent rollback attempts on same deployment

Suggestions:
  1. Replace bare except with except (asyncpg.PostgresError, ValueError)
  2. Add test: two simultaneous rollback requests should not create duplicate records
```

The warnings and suggestions get appended to `unvalidated_observations` for the next `/improve` cycle.

## CI Integration for /test

When `/test` generates or runs tests, it checks CI results:

```
/test demo-api

Running pytest locally... 47 passed, 0 failed (12.3s)

Checking CI status for last 5 runs on main:
  Run #89: passed (2m 14s)
  Run #88: passed (2m 08s)
  Run #87: FAILED -- test_metrics_lead_time timeout
  Run #86: passed (2m 11s)
  Run #85: passed (2m 09s)

CI failure analysis:
  Run #87 failure: test_metrics_lead_time
  Error: asyncpg.exceptions.ConnectionDoesNotExistError
  Pattern: This test has failed 3 times in last 20 runs (15% flake rate)
  Likely cause: Test database connection pool exhaustion in CI (shared runner)

Appending to unvalidated_observations:
  "test_metrics_lead_time flaky in CI -- 15% failure rate, connection pool issue in shared runner"
```

## GitHub Actions Workflow

Example CI workflow that Clarity-managed projects typically use:

```yaml
# .github/workflows/ci.yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint
        run: ruff check . && ruff format --check .

      - name: Test
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

## Tips

- `/discover` reads repo structure on first run, then only checks for changes on subsequent runs
- PR review comments from `/review` can be posted directly via `gh pr review`
- CI flake detection accumulates in expertise.yaml -- patterns emerge over multiple `/improve` cycles
- CODEOWNERS file + Jira component owners give Clarity a complete team ownership map
- For monorepos, `/discover` scopes to the app's subdirectory (reads path from app.yaml)

Source: GitHub MCP server, GitHub CLI (`gh`), tested with GitHub.com and GitHub Enterprise

## Related

- [Jira Integration](jira-integration.md) -- ticket and sprint context
- [Slack Integration](slack-integration.md) -- team communication
- [Claude Desktop](claude-desktop.md) -- MCP server configuration
