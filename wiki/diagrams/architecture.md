# Architecture Diagrams

Visual overview of how the Clarity Framework components connect.

## Overall Architecture

```mermaid
graph TB
    subgraph "Interfaces"
        CC[Claude Code CLI]
        CD[Claude Desktop]
        OB[Obsidian]
        QZ[Quartz Site]
    end

    subgraph "Clarity Framework"
        CMD[Slash Commands<br>/create /discover /plan /build]
        EXP[expertise.yaml<br>Operational Data]
        MEM[.claude/memory/<br>Behavioral Rules]
        WIKI[wiki/<br>Durable Knowledge]
    end

    subgraph "Agent Layer"
        PC[Paperclip Orchestrator]
        CS[Clarity Steward]
        WC[Wiki Curator]
        SB[Site Builder]
        SM[Social Media]
        OR[Outreach]
        GTM[GTM Agent]
        TR[Triage]
    end

    CC --> CMD
    CD -->|MCP filesystem| EXP
    CD -->|MCP filesystem| WIKI
    OB -->|direct vault| WIKI
    QZ -->|wiki-sync.sh| WIKI

    CMD --> EXP
    CMD --> WIKI
    CMD --> MEM

    PC --> CS
    PC --> WC
    PC --> SB
    PC --> SM
    PC --> OR
    PC --> GTM
    PC --> TR

    CS -->|/improve| EXP
    WC -->|/wiki-ingest| WIKI
    TR -->|routes issues| PC
```

## Self-Learn Loop

```mermaid
graph LR
    A[Run any /command] -->|appends| B[unvalidated_observations]
    B --> C{/improve}
    C -->|confirmed| D[Promoted to<br>expertise section]
    C -->|stale| E[Discarded]
    C -->|unverifiable| F[Deferred]
    D --> G[expertise.yaml<br>grows more accurate]
    G -->|informs| A
```

Every slash command appends raw observations. The `/improve` command validates each one against current state and either promotes it into the relevant section, discards it, or defers it for later verification.

## Three Knowledge Systems

```mermaid
graph TB
    subgraph "expertise.yaml"
        E1[Project state]
        E2[API gotchas]
        E3[Build results]
        E4[Known limitations]
    end

    subgraph ".claude/memory/"
        M1[User preferences]
        M2[Process rules]
        M3[Guardrails]
        M4[Behavioral patterns]
    end

    subgraph "wiki/"
        W1[Reusable patterns]
        W2[Architectural decisions]
        W3[Platform knowledge]
        W4[People and roles]
    end

    CMD2[Slash Commands] -->|structured YAML| E1
    AUTO[Claude automatically] -->|markdown + frontmatter| M1
    WCMD[Wiki Commands] -->|Obsidian markdown| W1

    E1 -.->|runtime data| SESSION[Current Session]
    M1 -.->|behavioral rules| SESSION
    W1 -.->|durable knowledge| SESSION
```

Each system serves a different purpose. They stay separate by design:
- **expertise.yaml** -- operational data that changes frequently (updated by `slash commands` commands)
- **.claude/memory/** -- behavioral rules and preferences (updated by Claude automatically)
- **wiki/** -- synthesized knowledge that compounds over time (updated by `/wiki-*` commands)

## Command Workflow

```mermaid
graph LR
    CREATE[/create] --> DISCOVER[/discover]
    DISCOVER --> CHECK[/check]
    CHECK --> BRIEF[/brief]
    BRIEF --> PLAN[/plan]
    PLAN --> BUILD[/build]
    BUILD --> TEST[/test]
    TEST --> REVIEW[/review]
    REVIEW --> IMPROVE[/improve]
    IMPROVE -->|next session| BRIEF
```

A typical engagement flows from left to right. Each session starts with `/brief` and ends with `/improve`. The cycle repeats, and expertise.yaml gets more accurate with each pass.

## Agent Orchestration

```mermaid
graph TB
    PC[Paperclip API<br>localhost:3100]

    subgraph "Every 5 min"
        TR[Triage Agent]
    end

    subgraph "Every 30 min"
        WC[Wiki Curator]
        OR[Outreach Agent]
    end

    subgraph "Every 4-6 hours"
        CS[Clarity Steward<br>every 4h]
        SB[Site Builder<br>every 6h]
    end

    subgraph "Weekday Mornings"
        GTM[GTM Agent<br>8am]
        SM[Social Media<br>9am]
    end

    PC -->|heartbeat| TR
    PC -->|heartbeat| WC
    PC -->|heartbeat| OR
    PC -->|heartbeat| CS
    PC -->|heartbeat| SB
    PC -->|heartbeat| GTM
    PC -->|heartbeat| SM

    TR -->|assigns issues| WC
    TR -->|assigns issues| CS
    TR -->|assigns issues| SB
    GTM -->|coordinates| SM
    GTM -->|coordinates| OR

    CS -->|expertise.yaml| EXP[(expertise.yaml)]
    WC -->|wiki pages| WIKI[(wiki/)]
    SM -->|drafts| DRAFTS[(system/drafts/)]
```

Paperclip triggers each agent on its cron schedule. The Triage Agent runs most frequently (every 5 minutes) to route new issues. The GTM Agent runs at 8am to set the day's strategy before the Social Media Agent posts at 9am.

## Related

- [Command Flow](command-flow.md) -- detailed command chaining diagrams
- [Paperclip](../tools/paperclip.md) -- agent setup and management
- [Three Knowledge Systems](../how-it-works/three-systems.md) -- detailed explanation
