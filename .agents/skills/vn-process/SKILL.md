---
name: vn-process
description: Run Voice Note Agent commands on a note, a day, a collection, or a theme — suggests the best-fitting commands, runs them, saves the outputs.
argument-hint: "[<note|date|collection|theme>] [command] | suggest | list"
version: 3.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Voice-Notes, Processing, AI-Commands, Router]
---

# Voice Note Process — the command router

**Duration:** 2–30 min | **Layer:** Archive → Insight/Output | **Companion skills:** `/vn-sync` (get notes first), `/vn-catalog` (organize results)

The heart of the Voice Note Agent: every analysis, creation, and build command from the Tana Voice Note Agent, runnable on your local archive by any agent harness. Works without Tana — Tana write-back is an optional final step.

## Context to read first (do not skip)

1. `vn-config.yaml` — archive location and output language.
2. `commands/INDEX.md` — the command catalog (names, categories, scope, mode, when-to-use).

Do **not** preload any command file or notes — load them at steps 2–3 below, only for what was selected.

## Workflow

### 1. Select scope

Resolve the user's words into a set of note files:

- **A note** — a path, a date + fuzzy title ("yesterday's note about pricing"), or "latest" (newest file in the archive). Fuzzy: `grep -il` the title words across `Voice-Notes/**/*.md`, offer matches if ambiguous.
- **A day / date range** — filenames start with `YYYY-MM-DD`, so a range is a directory listing.
- **A collection** — a file in `Voice-Notes/Collections/`; its wikilinks are the member notes.
- **A theme** — grep the archive for the theme's words (titles first, then bodies); show the hit list and confirm before proceeding. Offer to save the result as a new collection (via `/vn-catalog`).

State the resolved scope in one line ("6 notes, 2026-08-19 → 2026-08-25") before going on.

### 2. Suggest (skip if the user already named a command)

Read the selected notes (titles + summaries first; full transcripts only when few). Read `commands/INDEX.md`. Recommend the **top 3** commands that fit what the notes actually contain, one line each on why — e.g. task-heavy ramble → `task-extractor-by-project`; an idea circling → `insight-crystallizer` or `content-outline`; emotional entry → `reflection`, `emotions`, `four-agreements-analysis`; a spoken spec → `build/build-document`; many notes over time → `time-evolution-analyzer` or `weekly-digest`. Honor the note's `processed:` list — don't re-suggest what already ran unless asked.

### 3. Run

1. Load the chosen command file from `commands/<category>/<name>.md`. Its **System Prompt** section is now your working instruction; **Output format** defines the deliverable. Apply it to the full transcripts of the selected notes.
2. `mode: interactive` → open the conversation (greeting, then follow the command's dialogue design). `mode: oneshot` → produce the document directly.
3. For collection scope, weave the notes together (that's the point) and reference each as a `[[wikilink]]`.

### 4. Save the output

- Oneshot outputs and chat reports go to `Voice-Notes/Outputs/YYYY-MM-DD-<command>-<slug>.md` (subfolders `articles/`, `digests/`, `briefs/` where a command says so), with frontmatter: `type: vn-output`, `command`, `date`, `sources: ["[[note]]", ...]`.
- Append the command name to each source note's `processed:` frontmatter list.
- Interactive sessions: when winding down, offer `create/chat-report` to consolidate the conversation into a saved document.

### 5. Optional Tana write-back (only if Tana MCP tools exist in this session)

If the user wants the output in Tana too: `import_tana_paste` a condensed version under the source node or today's day node. If Tana is unavailable, skip silently — the local file is canonical.

## Other modes

- **`list`** — print the command catalog from `commands/INDEX.md`, grouped by category.
- **`suggest`** (no scope) — ask what period or topic is on the user's mind, then run steps 1–2 only.

## Rules

- The user's ideas are sacred — commands develop their thinking, never replace it.
- Match output language to `archive.language`, except where a command says otherwise (e.g. `message` follows the recipient).
- One command per run unless the user chains them ("outline then draft").
- Never modify a note's transcript (only `clean-transcript` may, and it says so).
- End with one concrete next step (a follow-up command, `/vn-catalog`, or "nothing — enjoy").
