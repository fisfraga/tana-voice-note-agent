# Frontmatter Schema (v3, canonical)

Every synced voice note is a markdown file shaped like this:

```markdown
---
title: "A fresh start for the application"
date: 2026-08-25            # Tana CAPTURE date (see caveat below)
type: voice-note
tags: [voice-note, cosmic-codex]     # free tags; seeded by catalog.tag_keywords
areas: []                   # ← /vn-catalog fills these three
projects: []                #   (mirrors the Tana template's Super Folder fields:
topics: []                  #    Area(s) / Project(s) / Topic(s)+Contemplation(s))
processed: []               # command names already run on this note (/vn-process appends)
outputs: []                 # wikilinks to the outputs generated from this note, with a value gloss
tana_id: nopW2YJqGtUp       # the source node — the bridge back to Tana
source: "Tana — My Workspace (Nd-xxxxxxxx)"
---

# A fresh start for the application

> Voice note recorded 2026-08-25. Mirrored from Tana node `nopW2YJqGtUp`.

## Transcript

One paragraph per Tana child bullet, blank-line separated.

## Summary

- **Only present** if the note had a Transcript Summary (AI) field in Tana
  (otherwise `/vn-sync` enrichment generates one right after sync).
```

## Field notes

- **`date` caveat** — it's the date Tana *captured* the node, which is the recording date for live captures but not for imported/migrated audio. When a transcript clearly describes another time, trust the transcript.
- **`tana_id`** — never change it; it's how sync stays idempotent and how write-back finds the node.
- **`processed`** — lets `/vn-process` avoid re-suggesting what already ran; clear it to make a note "fresh" again.
- **`outputs`** — the note's memory of what came from it. Each entry is a wikilink plus a one-line value gloss, e.g. `"[[2026-08-31-insight-crystallizer-fresh-start]] — named the core insight"`. `/vn-process` appends it when saving an output; Obsidian's graph picks up the link.
- **`areas`/`projects`/`topics`** — kebab-case values from your `vn-config.yaml` catalog vocabulary; `/vn-catalog` maintains them and the matching Collection files (people and contemplations land in `tags` as `person/...` / `contemplation/...`). With `tana.sync_connections: true`, confirmed values are mirrored to the note's Tana Super Folder fields.

## Output files (`Voice-Notes/Outputs/`)

```yaml
---
title: "Insight Crystallization: A fresh start for the application"
date: 2026-08-31
type: vn-output
command: insight-crystallizer
sources: ["[[2026-08-25-a-fresh-start-for-the-application]]"]
---
```

## Collection files (`Voice-Notes/Collections/`)

```yaml
---
name: Cosmic Codex
type: project        # area | project | topic | theme | manual
criteria: "notes about the Cosmic Codex product"
updated: 2026-08-31
---
```

Body: optional living prose, then a `## Notes` section of `[[wikilinks]]` (auto-regenerated for area/project/topic/theme types; append-only for manual).
