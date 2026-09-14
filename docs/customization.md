# Customization

Everything adapts through `vn-config.yaml` and plain markdown files. No code changes needed for any of the below (the sync script reads the config).

## What syncs

By default **every voice memo in the workspace** — any Tana node with an audio recording attached. You do not need a supertag, and you do not need the Tana template; record a memo and it syncs.

```yaml
tana:
  source: "all_audio"        # all_audio (default) | tagged | both
  voice_note_tag_id: ""      # only read by tagged / both
```

| `source` | Syncs | Use when |
|---|---|---|
| `all_audio` | every node with audio attached | you just talk into Tana (most people) |
| `tagged` | only nodes carrying `voice_note_tag_id` | your memos are deliberately marked, and you want *only* those |
| `both` | the union | you have both loose memos and a tagged history — including notes whose audio was stripped after transcription |

Narrow a single run without touching the config:

```bash
python3 scripts/sync_voice_notes.py --source tagged --tag <tagId>
python3 scripts/sync_voice_notes.py --source both --tag <tagId>
```

`--tag <id>` on its own implies `--source tagged`, and it may be repeated. In a harness, just say it — *"/vn-sync, only my #voice note ones"* — and the skill applies it for that run only. `/vn-sync setup` asks the same question and counts your memos first, so you can see what each choice would pull in.

Old memos marked with other supertags (a legacy `#voice memo`, a `#conversation voice note`…) join the `tagged` / `both` sets through `tana.extra_tag_ids: ["<id>", "<id>"]` — an inline list, because the no-PyYAML fallback parser doesn't read block lists.

## Bringing in your whole history

The default sync looks at the last 30 days. To import everything you ever recorded — years of memos in every format — run the history sweep:

```bash
python3 scripts/sync_voice_notes.py --history --dry-run   # count only
python3 scripts/sync_voice_notes.py --history             # pre-flight, then asks
python3 scripts/sync_voice_notes.py --history --yes --batch 300   # go, 300 notes at a time
```

or, in a harness, `/vn-sync history`. What it does differently:

- **Pages past Tana's 1000-result cap.** Search has no cursor, so the sweep walks backwards in date windows (`tana.history.window_days`, default 90) and halves a window that fills up. Nothing is silently truncated; a day with 1000+ memos is flagged.
- **Shows a pre-flight and asks.** Nodes found, how many are new, a breakdown by supertag, a time estimate — then an explicit go (`--yes` skips the prompt; outside a terminal the script prints the pre-flight and exits so the agent can relay it).
- **Copies notes in; does not enrich.** Cleaning a transcript and writing a missing summary is one AI pass per note. A sweep of a thousand notes would cost hours of tokens, so the sweep never does it. Afterwards, clean up in batches whenever you like: `/vn-sync enrich --last 20`.
- **Is resumable.** The manifest is written every 25 notes and on Ctrl-C; re-run the same command to continue. `--batch N` stops after N notes on purpose.
- **Keeps empty nodes out of the archive.** A node with no transcript is recorded as `empty` in the manifest (not written); `--retry-empty` re-tries them once Tana has transcribed them.

`--all` still works as a synonym. Fallback without Python: the skill spells out the same windowed walk with MCP calls, but every node then lands in the conversation — above ~50 notes, install Python.

## Categories from Tana (Super Folders)

If your voice notes carry the template's Super Folder fields — **Area(s) / Project(s) / Topic(s)** — or any field of your own, their values arrive in the note's frontmatter:

```yaml
tana:
  category_fields:
    areas: "Area(s)"        # Tana field label -> frontmatter key
    projects: "Project(s)"  # loose match: "Project", "Projects", "Project(s)" all work
    topics: "Topic(s)"
    people: "Person(s)"     # any other superfolder you use becomes its own list
```

Each value becomes a kebab-case entry (`4. Home & Family` → `home-family`) and its Tana node id is remembered in `tana_refs`, so `/vn-catalog` knows the value is confirmed and can write references back. The bullet's own supertags land in `tana_tags`. Untagged captures have no fields, so they arrive uncategorized — `/vn-catalog new` handles those.

## Two nodes per capture: the day node is the anchor

Every voice capture in Tana creates two nodes. The one you see is the **bullet under your day node** (*Daily notes → year → week → day*), with a title Tana derives from what you said — and, tagged or not, the Transcript, Summary and Super Folder fields. Behind it Tana keeps a hidden **`Voice memo captured …`** node that holds the audio. The audio search that discovers your memos only ever finds the hidden one, and anything written to it (a tag, an Area) never shows up in your outline.

So the sync anchors every note on the **day-node bullet**: it opens the capture's day node, matches the capture by timestamp, and uses that bullet as `tana_id`; the hidden node is remembered as `tana_memo_id`. Every write-back — tags, Super Folder fields, pasted outputs — goes to `tana_id`. Costs one calendar lookup and one children listing per day that has captures.

Archives synced by an older version point at the hidden nodes. Fix them once:

```bash
python3 scripts/sync_voice_notes.py --relink --history --dry-run   # what would change
python3 scripts/sync_voice_notes.py --relink --history             # remap tana_id, frontmatter only
```

If you moved a note out of its day node, the sync can't find its bullet and keeps the hidden node as `tana_id` (the note still syncs); `--relink` picks it up later if it ever finds the twin.

Two small things to know: the day lookup uses Tana's *get-or-create* calendar call, so a sweep may create an empty Day node for a day that had none (harmless, and only when a capture's timestamp sits near midnight); and a bullet you renamed after capture still anchors by timestamp, but not by title.

Two companions:

- `/vn-catalog vocab` pulls the *values* of your areas / projects / topics out of Tana (every node carrying your `#area` / `#project` / `#topic` supertags) into `catalog.*`, so the catalog proposes from your own structure. It caches the tag ids in `tana.category_tag_ids` and the node ids in `catalog.tana_ids`.
- `python3 scripts/sync_voice_notes.py --refresh-categories --since 60` re-reads the fields of notes already archived and union-merges them into frontmatter (frontmatter only, nothing removed). `--history` instead of `--since` covers the whole archive; `--dry-run` shows the changes first.

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

- **Connections** (`sync_connections`): after each confirmed catalog batch, `/vn-catalog` sets the note's `Area(s)` / `Project(s)` / `Topic(s)` fields in Tana — as references to your actual area/project/topic nodes (`[[Name^id]]`), never plain text — so the network you build locally is also navigable in the Tana app. Field labels come from `tana.category_fields`; field IDs are resolved once and cached (`tana.field_ids`); node ids come from `tana_refs` and `catalog.tana_ids` (run `/vn-catalog vocab` first). Values that came from Tana are never removed by the catalog, in either direction.
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
