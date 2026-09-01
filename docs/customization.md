# Customization

Everything adapts through `vn-config.yaml` and plain markdown files. No code changes needed for any of the below (the sync script reads the config).

## Where notes live

```yaml
archive:
  dir: "/Users/you/SecondBrain/Voice-Notes"   # absolute path → your own vault
  layout: "by-month"                          # by-year | by-month | flat
  filename: "{date}-{slug}.md"
```

Moving an existing archive: move the folder (including `sync-manifest.tsv`), update `dir`, done — the manifest keys on Tana node ids, not paths. Files already on disk are never re-written.

## Obsidian interop

The archive is a valid vault folder: wikilinks (`[[2026-08-25-a-fresh-start...]]`) resolve, frontmatter shows in Properties, Collections behave like MOCs. Point `archive.dir` inside your vault and add `Outputs/` to Obsidian's excluded files if you want raw notes only in graph view.

## Non-English Tana templates

If your Transcript/Summary fields have different labels:

```yaml
tana:
  field_labels:
    transcript: "Transcrição"
    summary: "Resumo (IA)"
```

Set `archive.language` to the language command outputs should use — notes always stay in the language you spoke.

## Your vocabulary

Seed `catalog.areas / projects / topics` with your life structure and `/vn-catalog` will classify against it instead of inventing. `catalog.tag_keywords` maps title keywords to tags at sync time:

```yaml
catalog:
  areas: [health, career, relationships, creative]
  tag_keywords:
    "gene keys": "gene-keys"
    "podcast": "podcast"
```

## Tana: capture-only, or two-way?

By default Tana is a capture device — notes flow down, nothing flows back. Two optional write-backs:

```yaml
tana:
  sync_connections: true    # /vn-catalog mirrors confirmed areas/projects/topics
                            # to the note's Super Folder fields (asked during setup)
```

- **Connections** (`sync_connections`): after each confirmed catalog batch, `/vn-catalog` sets the note's `Area(s)` / `Project(s)` / `Topic(s)` fields in Tana, so the network you build locally is also navigable in the Tana app. Field labels are configurable (`tana.field_labels`); field IDs are resolved once and cached (`tana.field_ids`).
- **Outputs**: `/vn-process` step 5 can paste a condensed output back under the source node — always offered, never automatic.

Both skip silently when Tana isn't connected. Local files stay canonical either way.

## Adding your own command

One file: `commands/<category>/<your-command>.md` with the standard frontmatter —

```yaml
---
name: your-command
title: "🔧 Your Command"
description: One line for the router.
category: create          # or any existing category
scope: [single, collection]
mode: oneshot             # or interactive
origin: custom
---
```

— then sections `## When to use`, `## System Prompt`, `## Output format`. Add a row to `commands/INDEX.md` so `/vn-process` can suggest it. That's the whole plugin system. (Prompt-writing tips: the ported v2 commands follow a PERSONA / SITUATION / ACTION / CORE FRAMEWORKS / RESPONSE FORMAT / FURTHER EXPLORATION structure that has held up across hundreds of sessions — steal it. And give every command the archive-context clause: "the selected note(s) are the starting point, not the boundary" — that's what makes a v3 command better than its v2 ancestor.)

## Adding your own lens

Even cheaper than a command: one small file in `commands/lenses/` —

```yaml
---
name: stoic
title: "🏛️ Stoic Principles"
type: lens
select: "2–4 elements"
integration_title: "Integrated Stoic Wisdom"
tone: "Grounded and practical — control vs. no-control is the razor."
---
```

— then `## Elements` (your vocabulary of perspectives, each with a guiding question) and `## Lens rules` (2–3 lines of lens-specific guidance). Add a row to the lens table in `commands/INDEX.md`, and `lens-analysis` can run it. This is how the eight built-in wisdom traditions work; a ninth costs you fifteen minutes.

## Removing what you don't use

Delete command files and lens files (and their INDEX rows) freely — e.g. the `zodiac` / `hermetic` lenses if archetypal reading isn't your thing, or `chat`'s optional "Ontological basis" section for a purely practical assistant. Nothing else references them.

## Other harnesses

The skills are plain instruction files in `.agents/skills/`; `.claude/skills/` just symlinks there. For a harness with its own skill location, symlink or copy the three folders and keep `AGENTS.md` as the entry point. The only hard dependency is file access; Tana MCP and Python are both optional (each has a documented fallback).
