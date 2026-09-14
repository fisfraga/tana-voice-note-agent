# Frontmatter Schema (v3, canonical)

Every synced voice note is a markdown file shaped like this:

```markdown
---
title: "A fresh start for the application"
date: 2026-08-25            # Tana CAPTURE date (see caveat below)
type: voice-note
tags: [voice-note, cosmic-codex]     # free tags; seeded by catalog.tag_keywords
areas: [home-family]        # ← pre-filled from the node's Super Folder fields when Tana has them
projects: []                #   (Area(s) / Project(s) / Topic(s), or whatever tana.category_fields maps);
topics: [ai]                #   /vn-catalog fills the rest
processed: []               # command names already run on this note (/vn-process appends)
outputs: []                 # wikilinks to the outputs generated from this note, with a value gloss
tana_id: nopW2YJqGtUp       # the day-node bullet the user sees — the bridge back to Tana
tana_memo_id: 2u_AzEW1d37l  # the hidden audio node behind it (only when one was resolved)
tana_tags: [voice-note]     # the bullet's own supertags at sync time ([] when untagged)
tana_refs:                  # values that exist in Tana as references (only present when non-empty)
  areas/home-family: hg6UQLfpqB4G
  topics/ai: Kd8sLmQ1xAbc
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
- **`tana_id`** — the **day-node bullet**: the node under *Daily notes → day* that the user actually sees and that carries the Transcript, Summary and Super Folder fields, tagged or not. Every write-back targets it. Never change it by hand; it's how sync stays idempotent.
- **`tana_memo_id`** — the hidden `Voice memo captured …` node that holds the audio (Tana creates it alongside the bullet; `has: audio` finds only this one). Kept for dedupe and provenance; nothing is ever written to it. Absent when the sync could not resolve a bullet (the user moved the note) — then `tana_id` is the memo node itself, and `--relink` can fix it later.
- **`processed`** — lets `/vn-process` avoid re-suggesting what already ran; clear it to make a note "fresh" again.
- **`outputs`** — the note's memory of what came from it. Each entry is a wikilink plus a one-line value gloss, e.g. `"[[2026-08-31-insight-crystallizer-fresh-start]] — named the core insight"`. `/vn-process` appends it when saving an output; Obsidian's graph picks up the link.
- **`areas`/`projects`/`topics`** — kebab-case values from your `vn-config.yaml` catalog vocabulary; `/vn-catalog` maintains them and the matching Collection files (people and contemplations land in `tags` as `person/...` / `contemplation/...`). With `tana.sync_connections: true`, confirmed values are mirrored to the note's Tana Super Folder fields as references. When the Tana node already carries those fields, `/vn-sync` pre-fills them: the display name is kebab-cased with any leading numbering dropped (`4. Home & Family` → `home-family`). Extra keys declared in `tana.category_fields` (e.g. `people: "Person(s)"`) appear as their own top-level lists.
- **`tana_tags`** — the supertags the bullet carried when it was synced (kebab-case). Written by `/vn-sync`, read-only for everything else; `[]` means an untagged capture — no Super Folder fields exist on it until a supertag is applied.
- **`tana_refs`** — provenance for categories. Each line is `<frontmatter key>/<kebab value>: <Tana node id>` and means "this value exists in Tana as a reference on this note". The catalog treats such values as confirmed (never removes or re-proposes them) and `/vn-catalog sync` uses the id to write a reference rather than text. Absent when nothing is linked. Written by `/vn-sync` on arrival and by `/vn-sync --refresh-categories` (the one sync path that edits existing files — frontmatter only), and appended by `/vn-catalog sync` after a successful write-back.

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
