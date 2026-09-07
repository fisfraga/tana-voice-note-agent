---
name: vn-sync
description: Sync voice notes from Tana into the local markdown archive — idempotent, config-driven, with enrichment (clean + summarize) and an MCP fallback when the script can't run.
argument-hint: "[setup | --since N | --all | --dry-run | --no-enrich | status]"
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

1. `vn-config.yaml` — the configuration (archive location, layout, workspace, tag, `archive.enrich`).
2. `Voice-Notes/sync-manifest.tsv` — current sync state (skim the last ~20 lines).

Do **not** read the whole archive or the command library for a sync.

## Modes (from the user's instruction after /vn-sync)

### `setup` — first-time configuration

1. Check `vn-config.yaml`: if `tana.workspace_id` and `tana.voice_note_tag_id` are filled, say so and stop.
2. Fast path — run from the repo root with the shell tool:
   `python3 scripts/sync_voice_notes.py --setup`
   (interactive: it lists workspaces and voice-looking tags, then writes the choices into `vn-config.yaml`).
3. Fallback (no Python, or the user prefers chat): call the Tana MCP tools yourself — `list_workspaces`, then `list_tags` on the chosen workspace; show candidates whose name contains "voice"; on the user's choice, edit `vn-config.yaml` yourself (`tana.workspace_id`, `tana.workspace_name`, `tana.voice_note_tag_id`).
4. Ask one more setup question: *"Should confirmed areas/projects/topics also sync back to your Tana Super Folder fields, or is Tana capture-only?"* — record the answer as `tana.sync_connections: true|false` (used by `/vn-catalog`).
5. If neither Python nor Tana MCP is available, point the user to `SETUP.md` and stop.

### default — sync recent notes

1. Fast path: `python3 scripts/sync_voice_notes.py --since 30` (pass through the user's `--since N`, `--all`, `--limit N`, `--dry-run`).
2. Report the script's tally: written / skipped / failed. For each `failed` row, tell the user why (usually an empty Transcript field — the note may still be transcribing in Tana).
3. **Enrich** the newly written notes (see below), unless `archive.enrich: false` or the user said `--no-enrich`.
4. Suggest `/vn-catalog` to assign areas/projects/topics to the new notes.

### Enrichment — clean + summarize new arrivals

Runs only on notes written *in this sync* (never on the existing archive). This is the one moment the agent may touch a note's body — before the note is "yours". *(Absorbs the v2 Clean Transcript and Generate Summary commands.)* For each new note:

1. **Clean, if raw.** If the transcript is run-on speech-to-text (no paragraphs, heavy filler), clean it in place, preserving the author's voice and meaning exactly: remove filler words and false starts ("um", "uh", "like, you know", repeated words) unless they carry meaning; fix punctuation, capitalization, and obvious speech-to-text errors (use context; when unsure, keep the original); break into paragraphs at natural topic shifts — one idea per paragraph. Keep the original language; never translate, summarize, shorten, or embellish; never add content or remove content that carries meaning; mark unintelligible passages `[unclear]`. Transcripts that arrive already cleaned by the Tana template are left untouched.
2. **Summarize, if missing.** If the note has no `## Summary` (Tana's summary field usually provides one), generate it: a bulleted list, each bullet a **short bold title** followed by an expanded description on the same line; first person, as if the note's author wrote it; the note's own language; cover ALL the important parts — do not omit for brevity.
3. Report which notes were cleaned and which were summarized.

On request, enrichment can also run standalone on notes the user names ("enrich my last three notes").

### MCP fallback — when the script can't run

Only if Python is unavailable or the script errors on transport. Replicate its algorithm with Tana MCP tools, sequentially:

1. `search_nodes` with `{ "and": [ { "hasType": "<voice_note_tag_id>" }, { "created": { "last": N } } ] }` (drop the `created` clause for `--all`).
2. Load `Voice-Notes/sync-manifest.tsv`; skip node ids already `done`/`exists`/`skip`.
3. For each remaining node: `read_node` (maxDepth 6); extract the title (strip trailing `#tags`, unwrap `![alt](url)` names, strip checkbox prefixes and trailing timestamps) and the children of the `**Transcript**:` and `**Transcript Summary (AI)**:` fields (labels per `vn-config.yaml`). If there's no Transcript field, the direct child bullets are the transcript; if there are none and the title is very long, the title IS the content.
4. Write the file per the schema in `docs/frontmatter-schema.md`, at the path dictated by `archive.dir` + `archive.layout` + `archive.filename`. **Never overwrite an existing file** — mark the row `exists` instead.
5. Append/update the manifest row (`date · node_id · mirrored · title`), run enrichment on the new files, and report the same tally the script would.

### `status` — where things stand

Count manifest rows by `mirrored` value, report the newest synced note's date, and how many files the archive holds (`ls` by year folder). No Tana calls.

## Rules

- **Never commit or print the Tana token.** It lives in the harness MCP config or `TANA_MCP_TOKEN` — nowhere else.
- Never overwrite an existing note file — hand-curated edits are sacred. Enrichment touches only notes written in the current sync (or explicitly named by the user).
- Never delete manifest rows; `skip` (hand-set) means never sync that node.
- Transcription happens in Tana (the audio lives there). A note failing with "no transcript" is usually still processing — retry on the next sync.
- Everything here is safe to re-run; say so when the user hesitates.
- End with one concrete next step (usually `/vn-catalog` for new files).
