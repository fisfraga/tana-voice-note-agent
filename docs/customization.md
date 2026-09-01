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

— then sections `## When to use`, `## System Prompt`, `## Output format`. Add a row to `commands/INDEX.md` so `/vn-process` can suggest it. That's the whole plugin system. (Prompt-writing tip: the ported v2 commands follow a PERSONA / SITUATION / ACTION / CORE FRAMEWORKS / RESPONSE FORMAT / FURTHER EXPLORATION structure that has held up across hundreds of sessions — steal it.)

## Removing what you don't use

Delete command files (and their INDEX rows) freely — e.g. the 🪬 Higher Understanding category if archetypal lenses aren't your thing, or `deep-chat`'s optional "Ontological basis" section for a purely practical assistant. Nothing else references them.

## Other harnesses

The skills are plain instruction files in `.agents/skills/`; `.claude/skills/` just symlinks there. For a harness with its own skill location, symlink or copy the three folders and keep `AGENTS.md` as the entry point. The only hard dependency is file access; Tana MCP and Python are both optional (each has a documented fallback).
