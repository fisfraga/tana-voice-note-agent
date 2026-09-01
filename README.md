# 🎤 Tana Voice Note Agent v3.0

**Your voice notes, out of the outline and into the hands of a real agent.**

Record voice notes in [Tana](https://tana.inc). Sync them to your computer as clean markdown. Then let Claude Code, Claude Cowork, or any capable AI harness *actually work with them*: analyze a week of thinking, crystallize insights, extract every task, write the article you drafted out loud — even build the document or feature you described while walking.

v1 and v2 lived inside Tana. v3 finally earns the name **Agent**: your notes become local files a real agent can read, connect, and act on — with the full v2 command library (20+ AI agents, all the smart-object commands) ported and expanded with agent-native commands that were impossible inside an outliner.

> **This repo is the free companion to the [Tana Voice Note Agent template](https://pay.hotmart.com/A96283812F?checkoutMode=10)** ($90, one-time) — the Tana side that captures, transcribes, and organizes your voice notes. You need Tana and (recommended) the template for the capture flow; this repo is everything that happens after.

## What you get

- **`/vn-sync`** — pull your `#voice note` nodes out of Tana into a chronological markdown archive (`Voice-Notes/2026/2026-08-31-my-idea.md`), with frontmatter, idempotent re-runs, and a never-overwrite guarantee. Python script fast path, pure-MCP fallback.
- **`/vn-process`** — the command router. Point it at one note, a day, a date range, a collection, or a theme; it suggests the best-fitting commands and runs them. **43 commands** across six categories:
  - 🔍 **Understand** — Deep Chat, Insight Crystallizer, Main Themes, Cognitive Bias Analyzer...
  - 🎯 **Take Action** — Strategic Planner, Growth Navigator, Task Extractor...
  - 🏔️ **Explore & Connect** — Cross-Connections, Mental Models, Metaphors, Scale Shift, Time Evolution...
  - 🪬 **Higher Understanding** — Dimensions of Consciousness, Hermetic Principles, Zodiac Archetypes, Four Agreements
  - 📝 **Create** — Summary, Brainstorm, Content Outline, Final Content Piece, Mind Map, Story, Pros & Cons...
  - 🚀 **Build** *(new in v3)* — Build Document, Build Feature, Article Pipeline, Weekly Digest, Project Brief
- **`/vn-catalog`** — areas, projects, topics and tags in every note's frontmatter, plus dynamic **Collections** (markdown files of wikilinks — by area, project, topic, theme, or hand-picked) and a generated archive index.

## Two ways to use it

1. **Work inside this repo** (simplest): clone it, and your archive lives in `Voice-Notes/` right here.
2. **Point it at your Second Brain** (recommended if you have one): set `archive.dir` in `vn-config.yaml` to an absolute path inside your own vault/OS folder. The skills and commands stay here; your notes live with the rest of your knowledge. Works beautifully with Obsidian — the archive is plain markdown with wikilinks.

## Quick start

```bash
git clone https://github.com/fisfraga/tana-voice-note-agent.git
cd tana-voice-note-agent
claude   # or open the folder in Claude Cowork
```

1. Enable Tana's local API / MCP server and connect it to your harness → **[SETUP.md](SETUP.md)** (5 minutes).
2. Run `/vn-sync setup` — pick your workspace and voice-note tag.
3. Run `/vn-sync` — your notes appear in `Voice-Notes/`.
4. Run `/vn-process latest` — and meet your Voice Note Agent.

## How it fits together

```
 Tana (capture + transcribe)          This repo (the agent)
┌──────────────────────────┐   sync   ┌─────────────────────────────┐
│ 🎤 #voice note nodes     │ ───────► │ Voice-Notes/YYYY/*.md       │
│    Transcript field      │          │  ├── Collections/*.md       │
│    Summary field         │  (opt.)  │  ├── Outputs/*.md           │
│    Super Folders         │ ◄─────── │  └── INDEX.md               │
└──────────────────────────┘  write-  └─────────────────────────────┘
                               back        ▲ /vn-sync · /vn-catalog
                                           ▼ /vn-process
                                    commands/ (43 command prompts)
```

Details: [docs/how-it-works.md](docs/how-it-works.md) · [docs/frontmatter-schema.md](docs/frontmatter-schema.md) · [docs/customization.md](docs/customization.md)

## Works with

**Claude Code** and **Claude Cowork** first-class (skills auto-load from `.claude/skills/`). Any harness that reads `AGENTS.md` and `.agents/skills/` — Codex, Hermes Agent, and friends — gets the same skills; everything is plain files plus one optional Python script.

## Requirements

- [Tana](https://tana.inc) with the local API/MCP server enabled (desktop app)
- The [Tana Voice Note Agent template](https://pay.hotmart.com/A96283812F?checkoutMode=10) for the capture side (recommended — any `#voice note`-style supertag with a Transcript field also works)
- An AI agent harness (Claude Code / Cowork recommended)
- Python 3.9+ for the sync fast path (optional — there's a pure-MCP fallback)

## About

Built by [Felipe Fraga (Poggi)](https://github.com/fisfraga) — Tana Ambassador. The Voice Note Agent has 100+ users and 18+ months of development across v1 → v3.

MIT licensed. The command prompts are yours to adapt — see [docs/customization.md](docs/customization.md) for adding your own commands.
