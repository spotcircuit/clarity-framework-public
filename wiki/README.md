# Clarity Framework Wiki

This wiki shows what the Clarity Framework does, how it works, and what it produces. It is the reference for anyone evaluating the framework or trying to understand it quickly.

Clarity is an agentic intelligence framework for technical engagements. It gives any engineer (human or AI) full project context on day one and grows smarter throughout the engagement through a self-learn loop. Based on Andrej Karpathy's LLM Wiki pattern, extended with structured operational data and behavioral memory.

## Getting Started

New to Clarity? Start here.

- [Getting Started](getting-started.md) -- 15-minute tutorial from clone to working framework

## Tools

Integrations and supporting infrastructure.

- [Paperclip](tools/paperclip.md) -- Agent orchestration: 7 autonomous agents, heartbeats, issue routing
- [Obsidian](tools/obsidian.md) -- Use the wiki as an Obsidian vault with bidirectional sync
- [Quartz](tools/quartz.md) -- Render the wiki as a searchable website via GitHub Pages
- [Claude Desktop](tools/claude-desktop.md) -- Access framework knowledge from Claude Desktop via MCP

## Diagrams

Visual architecture and workflow references.

- [Architecture](diagrams/architecture.md) -- System overview, self-learn loop, three knowledge systems, agent orchestration
- [Command Flow](diagrams/command-flow.md) -- Client onboarding, development cycle, knowledge capture workflows

## Examples

Real output from real projects managed by the framework.

- [Site Builder](examples/site-builder.md) -- A web app built across four Claude Code sessions. Shows how expertise.yaml grows from 5 lines to a complete operational reference.
- [Acme Integration](examples/acme-integration.md) -- An enterprise client engagement (Node-RED trade compliance). Shows how the framework handles external engagements with live APIs and multi-tenant deployment.

## How It Works

The mechanics behind the framework.

- [The Self-Learn Loop](how-it-works/self-learn-loop.md) -- How observations get validated, promoted, or discarded. The core feedback mechanism.
- [Three Knowledge Systems](how-it-works/three-systems.md) -- Why the framework uses YAML + memory + wiki instead of one system. What each stores and why they stay separate.
- [Commands](how-it-works/commands.md) -- All 19 slash commands with descriptions and example output.

## Patterns

Reusable engineering patterns captured through the wiki. These show the kind of knowledge the framework accumulates.

- [Correlation ID](patterns/correlation-id.md) -- Track execution across services.
- [Idempotency Guard](patterns/idempotency-guard.md) -- Prevent duplicate processing.
- [Config-Driven Routing](patterns/config-driven-routing.md) -- Routing logic in config, not code.
