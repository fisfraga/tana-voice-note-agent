---
name: vn-catalog
description: Assign areas, projects, topics, and tags to voice notes; build and maintain dynamic Collections; regenerate the archive index.
argument-hint: "[new | all | collections | index | collect \"<theme>\"]"
version: 3.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Voice-Notes, Metadata, Collections, Organization]
---

# Voice Note Catalog — metadata & collections

**Duration:** 3–15 min | **Layer:** Archive → Structure | **Companion skills:** `/vn-sync` (upstream), `/vn-process` (consumes collections)

The v3 evolution of the Tana template's Autofill + Super Folders: instead of fields on Tana nodes, notes carry `areas/projects/topics` frontmatter, and **Collections** are living markdown files of wikilinks — dynamic, portable, Obsidian-compatible.

## Context to read first (do not skip)

1. `vn-config.yaml` — the `catalog:` vocabulary (areas, projects, topics).
2. `Voice-Notes/Collections/` — list the existing collection files (names + frontmatter only).

Do **not** read all notes up front — scan frontmatter only (step 1) and open full notes only when classifying them.

## Modes (from the user's instruction after /vn-catalog)

### `new` (default) — catalog uncataloged notes

1. Find notes whose frontmatter has empty `areas`, `projects`, AND `topics` (grep for `areas: []` across `Voice-Notes/**/*.md`, excluding `Outputs/` and `Collections/`). Report the count; if large, propose batches of ~15, newest first.
2. For each note, read title + summary (transcript only if those are thin) and propose assignments — the Autofill discipline:
   - Choose ONLY from: `catalog.*` lists in `vn-config.yaml`, existing collection names, and values already used in other notes' frontmatter.
   - Propose a NEW area/project/topic only when nothing existing fits, clearly marked as new.
   - If a note fits nothing, leave it empty — no forced classification.
3. Present the batch as a table (note → proposed areas/projects/topics/tags) and ask for one confirmation (`y` / edits / skip list). Then update each note's frontmatter in place — touch nothing else in the file.
4. Add wikilinks for the newly assigned notes to their matching collection files (create collections for any confirmed-new entity). Finish by regenerating the index (see `index`).

### `all` — re-catalog everything (asks for confirmation first; otherwise identical)

### `collections` — review & maintain collections

Each file in `Voice-Notes/Collections/` is:

```markdown
---
name: <Display Name>
type: area | project | topic | theme | manual
criteria: "<one line: what belongs here>"
updated: YYYY-MM-DD
---
# <Display Name>
<optional living notes about this thread>

## Notes
- [[2026-08-25-a-fresh-start]] — one-line gloss
- [[2026-08-21-business-structure]] — one-line gloss
```

- **Auto collections** (`area`/`project`/`topic`): regenerate the `## Notes` list from frontmatter matches — additive and re-sorting, but never delete the prose above it.
- **`theme`** collections: created from a `/vn-process` theme search; refresh by re-running their `criteria` as a grep and proposing additions.
- **`manual`** collections: only ever append what the user names.

### `collect "<theme>"` — create a collection now

Grep the archive for the theme, show the hits, confirm membership, write the collection file (`type: theme`, or `manual` if the user picked by hand).

### `index` — regenerate `Voice-Notes/INDEX.md`

Rebuild from frontmatter only: total counts by year, then sections **By Area**, **By Project**, **By Topic** (each value → its notes as wikilinks, newest first), then **Collections** (link + one-liner), then **Recent outputs** (last 10 in `Outputs/`). Overwrite the whole file — it is generated, never hand-edited.

### Optional Tana write-back (only if Tana MCP tools exist in this session)

If the user maintains the Super Folder fields in Tana too, offer to mirror confirmed assignments back with `set_field_content` on each note's node. Skip silently when Tana is unavailable.

## Rules

- Frontmatter edits only — never touch a note's body.
- Vocabulary discipline: reuse before inventing; every new entity is flagged to the user.
- `INDEX.md` is generated — regenerate, don't patch.
- Keep entity names short and reusable (2–4 words, kebab-case in frontmatter, display case in collection files).
- End with one concrete next step (usually a `/vn-process` suggestion for the freshest collection).
