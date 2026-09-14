---
name: vn-catalog
description: Assign areas, projects, topics, tags, and entities to voice notes; pull your own Super Folder vocabulary from Tana; build and maintain dynamic Collections; regenerate the archive index; optionally sync connections back to Tana as references.
argument-hint: "[new | all | vocab | collections | index | collect \"<theme>\" | sync]"
version: 3.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Voice-Notes, Metadata, Collections, Organization]
---

# Voice Note Catalog — metadata & collections

**Duration:** 3–15 min | **Layer:** Archive → Structure | **Companion skills:** `/vn-sync` (upstream), `/vn-process` (consumes collections)

The v3 evolution of the Tana template's Autofill + Tag-and-Connect + Super Folders: instead of fields on Tana nodes, notes carry `areas/projects/topics` frontmatter, and **Collections** are living markdown files of wikilinks — dynamic, portable, Obsidian-compatible. Tana can stay in the loop (`tana.sync_connections`) or stay capture-only.

## Context to read first (do not skip)

`<archive>` below means the archive root — `archive.dir` from `vn-config.yaml`, resolved absolute (it may point outside this repo, e.g. into your Second Brain). It is **not** literally `Voice-Notes/` unless the config says so.

1. `vn-config.yaml` — the `catalog:` vocabulary (areas, projects, topics, `tana_ids`), `tana.category_fields`, `tana.category_tag_ids`, and `tana.sync_connections`.
2. `<archive>/Collections/` — list the existing collection files (names + frontmatter only).

Two frontmatter keys are written by `/vn-sync` and are **read-only for the catalog**: `tana_tags` (the node's own supertags) and `tana_refs` (`<key>/<value>: <tana node id>` — a value that exists in Tana as a reference). A value listed in `tana_refs` is *confirmed by Tana*: never remove it, never re-propose it.

Do **not** read all notes up front — scan frontmatter only (step 1) and open full notes only when classifying them.

## Modes (from the user's instruction after /vn-catalog)

### `new` (default) — catalog uncataloged notes

1. Find notes whose frontmatter has empty `areas`, `projects`, AND `topics` and no `tana_refs` (grep for `areas: []` across `<archive>/**/*.md`, excluding `Outputs/` and `Collections/`, then drop any hit that has a `tana_refs:` line). Notes that arrived with values from Tana are already cataloged; only propose *additions* to them when the user explicitly asks (`/vn-catalog new --include-tana`). Report the count; if large, propose batches of ~15, newest first.
2. For each note, read title + summary (transcript only if those are thin) and propose assignments — the Autofill discipline:
   - Choose ONLY from: `catalog.*` lists in `vn-config.yaml` (run `vocab` first if they are empty and Tana is connected), existing collection names, and values already used in other notes' frontmatter or `tana_refs`.
   - Propose a NEW area/project/topic only when nothing existing fits, clearly marked as new.
   - If a note fits nothing, leave it empty — no forced classification.
3. **Entities** *(absorbs the v2 Tag-and-Connect flow)* — alongside areas/projects/topics, extract the entities genuinely present:
   - **People** — individuals named or clearly referenced → `person/<name>` in `tags`.
   - **Contemplations** — ongoing ideas the person wants to keep reflecting upon → `contemplation/<name>` in `tags` (or `topics`, per the user's preference).
   - Plus plain `tags` for recurring vocabulary (`emotion/<state>` tags may arrive from `create/journal-entry`).
   - Same discipline: reuse before inventing; short, reusable names (2–4 words); no padding.
4. Present the batch as a table (note → proposed areas/projects/topics/tags) and ask for one confirmation (`y` / edits / skip list). Then update each note's frontmatter in place — touch nothing else in the file; never edit `tana_tags`; never remove a value that has a `tana_refs` entry.
5. Add wikilinks for the newly assigned notes to their matching collection files (create collections for any confirmed-new entity). If `tana.sync_connections: true`, mirror the batch to Tana (see `sync`). Finish by regenerating the index (see `index`).

### `all` — re-catalog everything (asks for confirmation first; otherwise identical)

### `vocab` — pull your Super Folder vocabulary from Tana (only if Tana MCP tools exist in this session)

Your areas, projects and topics already live in Tana as supertagged nodes (the template's `#VN area` / `#VN project` / `#VN topic`, or whatever you merged into the `Area(s)` / `Project(s)` / `Topic(s)` fields). This mode makes them the local vocabulary so `new` proposes from *your* structure instead of inventing one. Run it once after setup, after a history sweep, and whenever you reorganize Tana.

1. Resolve the category tags once: `get_tag_schema` on `tana.voice_note_tag_id` (`includeInheritedFields: true`) and read the target tag of each field named in `tana.category_fields` (an "Instance of #tag" field exposes it). If the target is a `*-merge` tag, the user's own tags extend it and `hasType` includes extensions, so it is fine as-is. If there is no voice-note tag or the field isn't instance-typed, `list_tags` and ask the user which supertags hold their areas / projects / topics. Cache the answers in `vn-config.yaml` under `tana.category_tag_ids` (`{areas: "<id>", projects: "<id>", topics: "<id>"}`).
2. For each category: `search_nodes {"and":[{"hasType":"<id>"}]}` with `limit: 1000` on the workspace (page by date windows exactly as `/vn-sync` does if it returns 1000). Kebab-case each node name, dropping leading numbering (`4. Home & Family` → `home-family`).
3. Show the user what would change in `catalog.areas/projects/topics` (additions, and local-only values that no longer exist in Tana — those are kept unless the user says otherwise). On confirmation, write the sorted inline lists and `catalog.tana_ids.<key>.<kebab>: <node id>` for every value. Inline YAML only — the fallback config parser doesn't read block lists.
4. Report counts per category and suggest `/vn-catalog new`.

### `collections` — review & maintain collections

Each file in `<archive>/Collections/` is:

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

### `index` — regenerate `<archive>/INDEX.md`

Rebuild from frontmatter only: total counts by year, then sections **By Area**, **By Project**, **By Topic** (each value → its notes as wikilinks, newest first), then **Collections** (link + one-liner), then **Recent outputs** (last 10 in `Outputs/`). Overwrite the whole file — it is generated, never hand-edited.

### `sync` — mirror connections to Tana (only if Tana MCP tools exist in this session)

Governed by `tana.sync_connections` in `vn-config.yaml` (set during `/vn-sync setup`; ask and record it if unset):

- **`true`** — after each confirmed batch in `new`/`all`, mirror the assignments to the notes' Tana nodes automatically. The explicit `/vn-catalog sync` mode pushes ALL current frontmatter connections on demand (confirm the count first).
- **`false`** — Tana is capture-only; never mirror. The user can still run `/vn-catalog sync` as a one-off, which offers to flip the config.

How to mirror:

0. **Write only to the day-node bullet.** A note's `tana_id` is the bullet the user sees in their daily notes; `tana_memo_id` (when present) is the hidden audio node — never tag it, never set a field on it, the user would never see the change. If a note has no `tana_memo_id` and `read_node` on its `tana_id` (maxDepth 0) shows a name starting `Voice memo captured`, stop and ask the user to run `python3 scripts/sync_voice_notes.py --relink` first.
1. Resolve field IDs once: `get_tag_schema` on `tana.voice_note_tag_id`, match the field names in `tana.category_fields` (loose match — `Area`, `Areas`, `Area(s)` are the same; `tana.field_labels.area/project/topic` are honoured as a fallback), and cache the resulting IDs in `vn-config.yaml` under `tana.field_ids`. **This step needs a supertag.** With no `voice_note_tag_id` set there are no Super Folder fields to write into — say so, leave `sync_connections` off, and keep the catalog local-only. A bullet with `tana_tags: []` has no fields yet: offer to apply the voice-note supertag to it (`tag` tool on `tana_id`, never on the memo node) — with the user's yes — and then write; otherwise skip it and report the count.
2. Resolve each value to a Tana node: first the note's own `tana_refs`, then `catalog.tana_ids`, then `search_nodes {"and":[{"hasType":"<category tag>"},{"textContains":"<name>"}]}`. A value with no node is new to Tana — ask before creating it (`import_tana_paste` `- <Display Name> #<tag>` under the category's home, or let the user create it in Tana), then cache its id in `catalog.tana_ids`.
3. For each note in the batch (its node is `tana_id` in the frontmatter): `set_field_content` per field with **references**, one per value, in Tana paste form `[[Display Name^nodeId]]` — never plain text. Send the full set for that field (existing `tana_refs` values plus the confirmed additions): check once on a scratch node whether `set_field_content` replaces or appends, and send only the delta if it appends.
4. After a successful write, add the matching `tana_refs` lines to the note's frontmatter. That is what makes the next `sync` idempotent and what stops `/vn-sync --refresh-categories` from re-importing them as new.
5. **Only confirmed assignments are ever mirrored** — never proposals. Skip silently when Tana is unavailable; local files stay canonical. Report how many notes were mirrored.

Conflict rule, both directions: values coming from Tana are confirmed; local additions win for additions; **nothing is ever removed on either side by the catalog.** If the user wants a value gone, they remove it in Tana or in the frontmatter by hand, and say so.

## Rules

- Frontmatter edits only — never touch a note's body.
- Vocabulary discipline: reuse before inventing; every new entity is flagged to the user.
- `INDEX.md` is generated — regenerate, don't patch.
- Keep entity names short and reusable (2–4 words, kebab-case in frontmatter, display case in collection files).
- Tana mirroring follows `tana.sync_connections`; confirmed values only; references (`[[Name^id]]`), never plain text; local files canonical.
- `tana_tags` and `tana_refs` are `/vn-sync`'s: the catalog reads them, adds `tana_refs` lines only after a successful write-back, and never removes either.
- End with one concrete next step (usually a `/vn-process` suggestion for the freshest collection).
