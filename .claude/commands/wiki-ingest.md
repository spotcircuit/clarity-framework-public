---
allowed-tools: Read, Write, Edit, Bash, Glob
description: Scan raw/ folder for unprocessed files and ingest them into the wiki as structured pages
argument-hint: [client-name]
---

# SE: Wiki Ingest

Scans `raw/` for unprocessed files (markdown, PDF, text, HTML), extracts key concepts,
and creates or updates structured wiki pages. Maintains `wiki/index.md` and `wiki/log.md`.
Moves processed files to `raw/processed/` when done.

## Variables

CLIENT: $ARGUMENTS
RAW_DIR: raw
WIKI_DIR: wiki
PROCESSED_DIR: raw/processed

## Instructions

- If CLIENT is provided: scope the wiki to `clients/CLIENT/wiki/` and `clients/CLIENT/raw/`
- If CLIENT is empty: use the project-level `wiki/` and `raw/` directories at repo root
- Never delete raw files — move to `raw/processed/` after ingestion
- One concept per wiki page — split multi-concept documents into multiple pages
- Check if a page already exists before creating — update instead of duplicate
- Cross-reference expertise.yaml when CLIENT is set
- SECRETS FILTER: NEVER include secrets in wiki pages. Scan every raw file for: eyJ (JWT), Bearer, client_secret, password=, api_key, _TOKEN=, _SECRET=, Authorization:. Redact matches with [REDACTED]. If a raw file is primarily secrets (like a .env), skip it entirely.

---

## Step 1: Scan raw/ for Unprocessed Files

```bash
ls -1 RAW_DIR/ 2>/dev/null | grep -v "^processed$"
```

Collect all files with extensions: `.md`, `.txt`, `.html`, `.htm`, `.pdf`

If no files found: report "No files to process in RAW_DIR/" and exit.

For each file, note:
- Filename and extension
- File size (skip empty files)
- Last modified date

---

## Step 2: Ensure Wiki Structure Exists

Check that these directories exist, create if missing:

```bash
mkdir -p WIKI_DIR/platform WIKI_DIR/clients WIKI_DIR/patterns WIKI_DIR/decisions WIKI_DIR/people PROCESSED_DIR
```

Check if `WIKI_DIR/index.md` exists. If not, create it with this skeleton:

```markdown
# Wiki Index

| Page | Category | Summary |
|------|----------|---------|
```

Check if `WIKI_DIR/log.md` exists. If not, create it with this skeleton:

```markdown
# Ingest Log

| Date | Source File | Pages Created | Pages Updated |
|------|-------------|---------------|---------------|
```

---

## Step 3: Process Each File

For each unprocessed file in `raw/`:

### 3a. Read the Content

Read the file fully. For HTML files, mentally strip tags and focus on text content.
For PDF files, read as text. If the file is unreadable, skip it and note in the log.

### 3b. Extract Key Information

Identify from the content:

**Concepts** — what platform features, patterns, or behaviors does this document describe?
**People** — names, roles, contact info, team assignments
**Clients** — any client or tenant references
**Decisions** — architectural or design decisions with stated rationale
**Patterns** — reusable flow structures, error handling approaches, API usage patterns
**Issues/Bugs** — known problems, workarounds, gotchas

### 3c. Determine Category and Target Pages

Map each concept to a wiki category:

| Concept Type | Wiki Category | Directory |
|---|---|---|
| Platform API behavior, node behavior, env var gotchas | platform | `wiki/platform/` |
| Client-specific knowledge, tenant state, project notes | clients | `wiki/clients/` (or `clients/CLIENT/wiki/clients/`) |
| Reusable flow/architecture patterns | patterns | `wiki/patterns/` |
| Architectural or design decisions with rationale | decisions | `wiki/decisions/` |
| Team members, roles, contacts | people | `wiki/people/` |

If a source file contains multiple distinct concepts, create a separate page for each.

### 3d. Check for Existing Pages

Before creating a page, glob for existing pages with similar names:

```bash
ls WIKI_DIR/CATEGORY/ 2>/dev/null
```

If a page covering the same concept exists: update it (merge new information, do not duplicate).
If no page exists: create a new one.

### 3e. Write or Update Each Wiki Page

**Page filename:** kebab-case of the concept name, `.md` extension.
Example: `native-object-reserved-names.md`, `cbp-status-mapping.md`

**Page format:**

```markdown
# Page Title

#tag1 #tag2 #category

One-sentence summary of this page.

## Content

[Concise wiki content — facts, patterns, gotchas. Not documentation. Keep it dense.]

## Related

- [[related-page-name]]
- [[another-related-page]]

---
Source: raw/source-filename.ext | Ingested: YYYY-MM-DD
```

**Tagging rules:**
- Always include the category as a tag: `#platform`, `#clients`, `#patterns`, `#decisions`, `#people`
- Add topic tags: `#api`, `#flow`, `#agent`, `#error-handling`, `#auth`, `#deployment`, etc.
- If CLIENT is set and the content is client-specific, add `#CLIENT`
- Tags go on line 2, space-separated

**Wiki link rules:**
- Link to related pages using `[[page-name]]` (filename without `.md`)
- Link to people pages when names appear: `[[john-doe]]`
- Link to platform pages when platform concepts are referenced
- Add links in the Related section and inline in the content where natural

**Platform-level content:**
- If the content would be useful to an SE on any engagement (not just this client), tag `#platform`
- Examples: API endpoint quirks, node behavior, auth patterns, deployment gotchas

**Cross-reference expertise.yaml (when CLIENT is set):**
- Read `clients/CLIENT/expertise.yaml` to check: does this knowledge already exist there?
- If the wiki page contains something missing from expertise.yaml's `implementation_patterns:` or `known_issues:`, note it (do not auto-edit expertise.yaml — that is `/improve`'s job)

---

## Step 4: Update wiki/index.md

After processing all files, update `WIKI_DIR/index.md`.

For each new page created, add one row to the index table:

```
| [[page-name]] | category | One-line summary of what this page covers |
```

For updated pages, check if they already have a row — if so, update the summary if it changed.

Keep the table sorted by category, then page name.

---

## Step 5: Append to wiki/log.md

Append one row per source file processed:

```
| YYYY-MM-DD | source-filename.ext | N created | N updated |
```

Use today's date. If a file was skipped (unreadable or empty), log it with `0 created | 0 updated | SKIPPED`.

---

## Step 6: Move Processed Files

For each successfully processed file, move it to `raw/processed/`:

```bash
mv RAW_DIR/filename PROCESSED_DIR/filename
```

If the move fails, warn but do not retry — leave the file in place.

---

## Step 7: Report

```
Wiki Ingest Complete

Source files processed: {N}
  Pages created: {N}
  Pages updated: {N}
  Files skipped: {N}

Pages created:
  - wiki/platform/page-name.md
  - wiki/patterns/page-name.md

Pages updated:
  - wiki/decisions/page-name.md

expertise.yaml gaps noted (run /improve to integrate):
  - {observation if any}

Files moved to raw/processed/:
  - filename.ext
```

If CLIENT was set and expertise.yaml gaps were found, suggest running `/improve CLIENT`.
