# Clarity Framework Onboarding Session -- Meeting Transcript

Date: 2026-04-08
Attendees: YOUR_NAME (framework author), Alex (new team member)
Duration: 30 minutes

---

**YOUR_NAME:** Welcome aboard. Before we dive into the codebase, let me walk you through how we manage project knowledge. We use a framework called Clarity that keeps all the context an engineer needs persistent across sessions.

**Alex:** I've heard it's based on the Karpathy wiki pattern?

**YOUR_NAME:** Right. Karpathy published his LLM Wiki architecture in April -- the idea that instead of RAG, you maintain a wiki that the LLM reads and writes. We extended that with two additional systems. So Clarity has three knowledge layers.

**Alex:** What are they?

**YOUR_NAME:** First is `expertise.yaml` -- structured YAML with operational data. API endpoints, known gotchas, deployment states, results from recent runs. The `/se:*` commands update it automatically. Second is `.claude/memory/` -- behavioral rules. How you like to work, guardrails, process preferences. The LLM creates those on its own when it notices patterns. Third is the wiki -- synthesized knowledge. Patterns, architectural decisions, cross-cutting concepts. That's what you're looking at in Obsidian.

**Alex:** Why not just put everything in the wiki?

**YOUR_NAME:** Different access patterns. The YAML is machine-readable -- commands parse it programmatically to check project state. Behavioral memory needs to be injected silently into every session. The wiki needs cross-linking and human readability. Mixing them creates something that's hard to query and hard to maintain.

**Alex:** Got it. So how do I actually use this day-to-day?

**YOUR_NAME:** When you start on a new client, copy the template from `clients/_templates/client.yaml`, fill it in, then run `/se:discover`. That generates a Phase 0 discovery document and seeds the expertise.yaml with initial observations.

**Alex:** What's Phase 0?

**YOUR_NAME:** It's auto-generated analysis of the client's tech stack, architecture, potential gotchas -- everything you'd normally spend a week figuring out. The LLM reads the client config and produces a structured assessment.

**Alex:** And then?

**YOUR_NAME:** Day to day, you use `/se:brief` for standup summaries, `/se:check` for design compliance, and `/se:self-improve` after any significant investigation. That last one is the key -- it validates observations that commands have been collecting and promotes confirmed facts into the expertise sections.

**Alex:** What about the wiki side?

**YOUR_NAME:** Two main workflows. First, drop files into the `raw/` folder -- meeting notes, web clips, transcripts like this one -- and run `/se:wiki-ingest`. The LLM reads the source, creates or updates wiki pages in the right categories, adds cross-links, updates the index, and moves the source to `raw/processed/`.

**Alex:** And the second workflow?

**YOUR_NAME:** The compounding loop. When you ask the LLM a question and get a good synthesized answer, run `/se:wiki-file <topic>` to capture it as a permanent wiki page. That way the system gets smarter every time you use it. Questions that produce good answers become knowledge.

**Alex:** What about maintenance?

**YOUR_NAME:** Run `/se:wiki-lint` periodically -- it checks for orphan pages with no inbound links, broken wiki links, stale pages, missing index entries. Pass `fix` to auto-repair what it can.

**Alex:** This is really different from our old setup where everything was in Confluence and nobody could find anything.

**YOUR_NAME:** That's the point. The LLM reads `index.md` first to navigate, follows the wiki links, and synthesizes answers with full context. No searching, no stale docs that nobody updates. The system maintains itself as a side effect of doing work.

**Alex:** One more thing -- how does the self-learn loop actually work?

**YOUR_NAME:** Every `/se:*` command appends raw observations to `unvalidated_observations:` in expertise.yaml. These are things the LLM noticed during execution -- an API that returned unexpected data, a config that was missing, a pattern it recognized. When you run `/se:self-improve`, it validates each observation against the current live state. Confirmed facts get promoted into the relevant section. Stale or duplicate observations get discarded. The expertise file stays clean and accurate.

**Alex:** And the wiki grows from the ingest and wiki-file commands, the YAML grows from the self-learn loop, and memory grows from the LLM noticing patterns. Three systems, each growing in its own way.

**YOUR_NAME:** Exactly. That's Clarity.

---

*End of transcript. To process this into wiki pages, run `/se:wiki-ingest`.*
