---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
description: Health check on wiki/ -- orphans, broken links, stale pages, contradictions, index gaps
argument-hint: [fix]
---

# SE: Wiki Lint

Runs a full health check on the `wiki/` folder. Finds orphan pages, broken links, stale pages,
contradictions with expertise.yaml, missing index entries, missing tags, and missing Related sections.

Pass `fix` as argument to auto-repair what it can.

## Variables

FIX_MODE: $ARGUMENTS (true if "fix", false otherwise)
WIKI_DIR: wiki

## Instructions

---

## Step 1: Inventory

Collect all wiki pages and their links.

```bash
find wiki/ -name "*.md" -type f | sort
```

For each page, extract all `[[wiki links]]` using grep.
Build: PAGE_LIST (all pages) and LINK_MAP (page -> outgoing links).

---

## Step 2: Orphan Check

Find pages with no incoming links from other pages.
- For every page, check if its filename (without .md) appears as a link target in any other page.
- Exceptions: index.md and log.md are never orphans.

---

## Step 3: Broken Link Check

Find `[[link-target]]` references that don't match any existing page filename.
- Search case-insensitive across all wiki subdirectories.

---

## Step 4: Stale Check

Find pages not modified in 14+ days.
- Use `git log --format="%ci" -- path` or file mtime.
- Exclude index.md and log.md.

---

## Step 5: Contradiction Check

Compare wiki pages against `clients/*/expertise.yaml` and `apps/*/expertise.yaml` for conflicts.
- Check version numbers, status claims, record counts, named owners.
- If no expertise.yaml files exist, skip.

---

## Step 6: Index Completeness

Verify every wiki page (except index.md, log.md) has an entry in wiki/index.md.

---

## Step 7: Tag + Related Audit

- Missing tags: pages without `#tag` patterns (not headings).
- Missing Related: pages without `## Related` section.

---

## Step 8: Apply Fixes (if FIX_MODE)

Only if user passed "fix":
1. Add missing pages to index.md in correct category section
2. Add empty `## Related` sections to pages that lack them
3. Create stub pages for missing link targets

---

## Step 9: Report

```
Wiki Lint Report
================

Orphans: N
Broken Links: N
Stale: N
Contradictions: N
Missing Pages: N
Index Gaps: N
Missing Tags: N
Missing Related: N

Total issues: N
```

If FIX_MODE, append fixes summary.
If zero issues: "Wiki is healthy. No issues found."
