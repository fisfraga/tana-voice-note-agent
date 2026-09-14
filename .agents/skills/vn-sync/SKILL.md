---
name: vn-sync
description: Sync voice notes from Tana into the local markdown archive — idempotent, config-driven, with a full-history import, enrichment (clean + summarize), Super Folder categories from Tana, and an MCP fallback when the script can't run.
argument-hint: "[setup | history [--batch N] | enrich [--last N] | --since N | --source all_audio|tagged|both | --tag <id> [--tag <id>] | --dry-run | --no-enrich | --refresh-categories | status]"
version: 3.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Voice-Notes, Tana, Sync, Archive]
---

# Voice Note Sync — Tana → local archive

**Duration:** 1–5 min | **Layer:** Capture → Archive | **Companion skills:** `/vn-catalog` (metadata), `/vn-process` (do things with the notes)

Works from Claude Code, Claude Cowork, and any harness that can run Python **or** call Tana MCP tools. Local files are canonical once synced; Tana remains the capture device.

## Context to read first (do not skip)

`<archive>` below means the archive root — `archive.dir` from `vn-config.yaml`, resolved absolute (it may point outside this repo, e.g. into your Second Brain). It is **not** literally `Voice-Notes/` unless the config says so.

1. `vn-config.yaml` — the configuration (archive location, layout, workspace, `tana.source`, `archive.enrich`).
2. `<archive>/sync-manifest.tsv` — current sync state (skim the last ~20 lines).

Do **not** read the whole archive or the command library for a sync.

## What counts as a voice note

**By default, every voice memo in the workspace** — any Tana node with an audio recording attached (`has: audio`), tagged or not. This repo and its skills work for anyone using Tana, with or without the paid Voice Note Agent template. The `#voice note` supertag only exists for people who installed that template; it is never a requirement, and you must not assume the user has one. Use a tag only when `tana.voice_note_tag_id` is set or the user names one.

`tana.source` in `vn-config.yaml` settles it:

| `tana.source` | Syncs | Needs a tag? |
|---|---|---|
| `all_audio` *(default)* | every node with audio attached | no |
| `tagged` | only nodes carrying `tana.voice_note_tag_id` or any of `tana.extra_tag_ids` | yes |
| `both` | the union of the two | yes |

`tana.extra_tag_ids` lists legacy supertags that *also* mark voice notes (an old `#voice memo`, a `#conversation voice note`…). `--tag <id>` may be repeated on the command line to add tags for one run.

## Two nodes per capture — the day node is the anchor

Every Tana voice capture creates **two** nodes: the **day-node bullet** the user sees under *Daily notes → year → week → day* (natural-language title, and — tagged or not — the `Transcript`, `Transcript Summary (AI)` and any Super Folder fields), and a hidden **backing memo node** named `Voice memo captured …` that holds the audio. `has: audio` only ever finds the hidden one; anything written to it (tags, fields) is invisible in the user's outline.

**The day-node bullet is the canonical node.** `tana_id` in every note points at it; `tana_memo_id` remembers the audio twin. The script resolves the bullet for each audio hit by opening that day's calendar node (`get_or_create_calendar_node` → `get_children`) and matching the capture timestamp (within 2 s), falling back to the memo's breadcrumb title. Tagged (`hasType`) hits are bullets already. Looking in the day node is also how a person would find the note — and it shows the other captures they made that day with the Tana capture app.

**Rules that follow:** never write a tag or a field to a `Voice memo captured …` node; every write-back (tags, Super Folder fields, pasted outputs) targets the note's `tana_id`. Archives synced before this rule can point at memo nodes — `python3 scripts/sync_voice_notes.py --relink --history --dry-run` shows them, and without `--dry-run` remaps `tana_id` to the bullet (frontmatter only).

**Categories come along in every mode.** When the bullet carries Super Folder fields (`Area(s)` / `Project(s)` / `Topic(s)` in the template, or whatever `tana.category_fields` maps), their values land in `areas/projects/topics`, with the Tana node ids in `tana_refs` and the bullet's own supertags in `tana_tags`. Bullets with no fields arrive uncategorized — that is what `/vn-catalog` is for. `both` is still the recommendation for template users because it also catches tagged notes whose audio was removed after transcription.

**Narrowing is opt-in and explicit.** If the user asks for a subset in their instruction — "only my #voice note ones", "just the tagged memos", "sync everything, tagged or not" — honour that for this run with `--source`/`--tag` and say which you used; do not silently rewrite `vn-config.yaml`. Offer to make it permanent only if they sound settled on it. If they name a tag you don't have an id for, `list_tags` on the workspace and match by name.

## Modes (from the user's instruction after /vn-sync)

### `setup` — first-time configuration

1. Check `vn-config.yaml`: if `tana.workspace_id` and `tana.source` are filled, say so and stop.
2. Fast path — run from the repo root with the shell tool:
   `python3 scripts/sync_voice_notes.py --setup`
   (interactive: it lists workspaces, counts the voice memos in the one you pick, asks what should sync, and writes the choices into `vn-config.yaml`).
3. Fallback (no Python, or the user prefers chat): call the Tana MCP tools yourself — `list_workspaces`, then `search_nodes {"and":[{"has":"audio"}]}` on the chosen workspace to count its voice memos. Then ask **one gating question: "Do you use the Tana Voice Note Agent template (the `#voice note` supertag)?"**
   - **No** (plain Tana, no template): `tana.source: all_audio`, no tag, done — do not mention supertags again. Everything in this repo works without the template.
   - **Yes**: recommend `both` (their Area/Project/Topic fields live on the tagged note; `both` brings them in and dedupes the audio twin), `list_tags` and show candidates whose name contains "voice", record `tana.voice_note_tag_id`.

   Edit `vn-config.yaml` yourself (`tana.workspace_id`, `tana.workspace_name`, `tana.source`, and `tana.voice_note_tag_id` only when a tag was chosen).
4. Ask one more setup question: *"Should confirmed areas/projects/topics also sync back to your Tana Super Folder fields, or is Tana capture-only?"* — record the answer as `tana.sync_connections: true|false` (used by `/vn-catalog`).
5. If neither Python nor Tana MCP is available, point the user to `SETUP.md` and stop.
6. If the workspace count came back as `1000+` or the user mentions years of memos, suggest `/vn-sync history` for the first import.

### default — sync recent notes

1. Fast path: `python3 scripts/sync_voice_notes.py --since 30` (pass through the user's `--since N`, `--limit N`, `--dry-run`, and `--source`/`--tag` when they asked to narrow this run; `--tag` may repeat).
2. Report the script's tally: written / skipped / failed. For each `failed` row, tell the user why (usually an empty Transcript field — the note may still be transcribing in Tana). If the script warns that the search hit the 1000-result cap, say so and offer `/vn-sync history`.
3. **Enrich** the newly written notes (see below), unless `archive.enrich: false` or the user said `--no-enrich`.
4. If some new notes arrived with `areas/projects/topics` already filled from Tana, say so — `/vn-catalog new` will only propose for the rest. Suggest `/vn-catalog` for the uncategorized ones.

### `history` — bring in your whole archive (first run, or years of memos)

A dedicated full sweep. Tana's search returns at most 1000 nodes per call, so the script walks the workspace backwards in date windows (90 days, halving automatically when a window saturates), records every node in the manifest as it goes, and is safe to interrupt and resume. **It copies notes in; it does not enrich them** — enrichment is one AI pass per note and would turn a ten-minute import into hours of tokens. Clean up later, in batches (see `enrich`).

1. Pre-flight: `python3 scripts/sync_voice_notes.py --history` (add `--source both --tag <id>` for each legacy tag the user names; `--dry-run` if they only want the numbers). Outside a terminal the script stops after discovery and prints the pre-flight instead of prompting.
2. Relay the pre-flight to the user **verbatim** — nodes found, windows walked, how many will be fetched, the tag breakdown, the time estimate — and add: *"This copies the notes in. Cleaning transcripts and writing missing summaries is one AI pass per note, so I will not do that now; afterwards you can say 'enrich the last 20' whenever you like."* Ask for an explicit go.
3. Run `python3 scripts/sync_voice_notes.py --history --yes` (add `--batch 300` if the user prefers chunks — re-run the same command to continue; the manifest is saved every 25 notes and on Ctrl-C).
4. Report the tally: written / exists / empty / failed. `empty` rows are nodes with no transcript at the time of the sweep (`--retry-empty` re-tries them later); `failed` rows retry on the next run.
5. **Do not enrich.** Suggest, in this order: `/vn-catalog vocab` (pull the user's own areas/projects/topics from Tana), `/vn-catalog new`, then `/vn-sync enrich --last 20` for the freshest notes.

`--all` is accepted as a synonym of `history`. `--window N` sets the initial window in days (default `tana.history.window_days`, 90).

### `enrich [--last N | <note names>]` — clean + summarize on demand

Runs the enrichment below on notes the user names, or on the N newest `done` rows in the manifest (`--last 20` default). Never more than 20 notes per batch; report, then ask before the next batch. This is how a history import gets cleaned up over time.

### `--relink` — move old archives onto the day-node anchor

Archives synced before day-node anchoring have `tana_id` pointing at the hidden audio node for every untagged memo. `python3 scripts/sync_voice_notes.py --relink --history --dry-run` lists them; without `--dry-run` it rewrites `tana_id` to the day-node bullet, adds `tana_memo_id`, refreshes `tana_tags` and union-merges categories — frontmatter only. Run it once before any `/vn-catalog sync` on an older archive; `--since N` limits it to recent notes.

### `--refresh-categories` — re-read Super Folder fields for archived notes

`python3 scripts/sync_voice_notes.py --refresh-categories --since 60` (or `--history` for the whole archive) re-reads each archived note's Tana node and **union-merges** any Area/Project/Topic values into its frontmatter — frontmatter only, body untouched, nothing ever removed. Run `--dry-run` first and show the user what would change. Useful after they organize old notes in Tana.

### Enrichment — clean + summarize new arrivals

Runs only on notes written *in this sync* (never on the existing archive). This is the one moment the agent may touch a note's body — before the note is "yours". *(Absorbs the v2 Clean Transcript and Generate Summary commands.)* For each new note:

1. **Clean, if raw.** If the transcript is run-on speech-to-text (no paragraphs, heavy filler), clean it in place, preserving the author's voice and meaning exactly: remove filler words and false starts ("um", "uh", "like, you know", repeated words) unless they carry meaning; fix punctuation, capitalization, and obvious speech-to-text errors (use context; when unsure, keep the original); break into paragraphs at natural topic shifts — one idea per paragraph. Keep the original language; never translate, summarize, shorten, or embellish; never add content or remove content that carries meaning; mark unintelligible passages `[unclear]`. Transcripts that arrive already cleaned by the Tana template are left untouched.
2. **Summarize, if missing.** If the note has no `## Summary` (Tana's summary field usually provides one), generate it: a bulleted list, each bullet a **short bold title** followed by an expanded description on the same line; first person, as if the note's author wrote it; the note's own language; cover ALL the important parts — do not omit for brevity.
3. Report which notes were cleaned and which were summarized.

On request, enrichment can also run standalone on notes the user names ("enrich my last three notes") — that is the `enrich` mode above. **Never enrich as part of `history`.**

### MCP fallback — when the script can't run

Only if Python is unavailable or the script errors on transport. Replicate its algorithm with Tana MCP tools, sequentially:

1. `search_nodes` (`limit: 1000`, `workspaceIds: [<workspace_id>]`) with the clause for the configured `tana.source`:
   - `all_audio` (default) — `{ "has": "audio" }`
   - `tagged` — `{ "hasType": "<id>" }`, or `{ "or": [ { "hasType": "<id1>" }, { "hasType": "<id2>" } ] }` with `extra_tag_ids`
   - `both` — `{ "or": [ { "has": "audio" }, { "hasType": "<id>" }, … ] }`

   Recent sync: `{ "and": [ <clause>, { "created": { "last": N } } ] }`.
   **History sweep** (no cursor exists, so page by date windows): start `LO = 0`, `HI = 90`. Before each window run `{ "and": [ <clause>, { "not": { "created": { "last": LO } } } ] }` — if it returns fewer than 1000 nodes, that result is the tail and you are done. Otherwise fetch the window `{ "and": [ <clause>, { "created": { "last": HI } }, { "not": { "created": { "last": LO } } } ] }`; if it returns 1000, halve the window and retry; then `LO = HI`, `HI = LO + window`. Register every discovered node in the manifest as `pending` before reading any of them.

   **Cost warning — say this before a history sweep in fallback mode:** every `read_node` lands in the conversation (roughly 1–3k tokens each). Above ~50 notes, installing Python is the difference between minutes and a very long, expensive session. If the user still wants it: work in batches of 20 `read_node` calls, newest window first, update the manifest after each batch, stop and ask before the next one, and never enrich during the sweep.
2. Load `<archive>/sync-manifest.tsv`; skip node ids already `done`/`exists`/`skip` (and `empty`, unless the user asked to retry them) — the manifest keys on the day-node bullet and also records the memo id (column 6), so check both.
3. **Resolve the anchor** for every audio hit (name `Voice memo captured …`): `get_or_create_calendar_node {granularity: "day", date: <capture date>}` → `get_children` (limit 1000; one call per day, reuse it for every capture of that day). Pick the child with a non-empty name whose `created` is within 2 s of the memo's `created`; if none, the child whose name equals the memo's breadcrumb last element; skip nameless clutter children. That child is the note's `tana_id`; the audio node is `tana_memo_id`; the child's `tags` are `tana_tags`. If nothing matches (the user moved the note), keep the memo id and say so. Tagged hits need no resolution.
4. For each remaining note: `read_node` on the **bullet** (maxDepth 6); extract the title (strip trailing `#tags`, unwrap `![alt](url)` names, strip checkbox prefixes and trailing timestamps) and the children of the `**Transcript**:` and `**Transcript Summary (AI)**:` fields (labels per `vn-config.yaml`). If there's no Transcript field, the direct child bullets are the transcript; if there are none and the title is very long, the title IS the content. When the name is Tana's generic capture label ("Voice memo captured Mon, Feb 9, 12:17"), title the note from the first ~70 characters of the transcript instead — otherwise every captured memo lands on the same filename stem. Also collect every other `**Label**:` field whose label matches a `tana.category_fields` entry (match loosely: `Area`, `Areas`, `Area(s)` are the same): each `[Display Name #tag](tana:<id>)` value becomes a kebab-case entry in that frontmatter key (drop leading numbering — `4. Home & Family` → `home-family`) plus a `tana_refs` line `areas/home-family: <id>`. The search result's `tags[].name` become `tana_tags`.
5. Write the file per the schema in `docs/frontmatter-schema.md`, at the path dictated by `archive.dir` + `archive.layout` + `archive.filename`. **Never overwrite an existing file** — mark the row `exists` instead. A node with no transcript is `empty` in a history sweep, `failed` otherwise.
6. Append/update the manifest row (`date · node_id · mirrored · title · synced_at · memo_id`), run enrichment on the new files (recent sync only — never in a sweep), and report the same tally the script would.

### `status` — where things stand

Count manifest rows by `mirrored` value (including `empty` and `pending`), report the newest and the oldest synced note dates (how far back the archive reaches), and how many files the archive holds (`ls` by year folder). No Tana calls. If rows are still `pending`, say a history sweep was interrupted and can be resumed with the same command.

## Rules

- **Never commit or print the Tana token.** It lives in the harness MCP config or `TANA_MCP_TOKEN` — nowhere else.
- **Synced notes are private.** The archive is gitignored when it sits inside the repo; never `git add -f` a note, an output, or the manifest, and never paste note content into a commit message or a PR. Captured memos carry a signed audio URL in the Tana node — it must not reach the archive or the terminal.
- Never overwrite an existing note file — hand-curated edits are sacred. Enrichment touches only notes written in the current sync (or explicitly named by the user).
- Never write to a `Voice memo captured …` node; the day-node bullet (`tana_id`) is the only write target. If a note's `tana_id` still names a memo node, run `--relink` first.
- Never delete manifest rows; `skip` (hand-set) means never sync that node. `empty` rows are history-sweep leftovers with no transcript — `--retry-empty` re-tries them; never turn them into `skip` yourself.
- A history sweep never enriches. Enrichment is on demand, in batches of at most 20, always with the user's go.
- Transcription happens in Tana (the audio lives there). A note failing with "no transcript" is usually still processing — retry on the next sync.
- Everything here is safe to re-run; say so when the user hesitates.
- End with one concrete next step (usually `/vn-catalog` for new files).
