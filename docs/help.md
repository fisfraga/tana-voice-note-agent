# Help — how the Voice Note Agent works

Written for the agent to read when the user asks *how* something works (loaded by `/vn-help`). Short, scannable, with pointers to the course videos in [`videos/README.md`](videos/README.md). For architecture depth read [`how-it-works.md`](how-it-works.md); for knobs, [`customization.md`](customization.md).

## The one-paragraph version

You speak into Tana. Tana records and transcribes. `/vn-sync` mirrors each memo into a markdown file in your archive (local files become the canonical copy). `/vn-catalog` gives every note areas / projects / topics / people and keeps Collections and an index. `/vn-process` is the heart: pick a note, a day, a range, a collection or a theme; the agent suggests the best-fitting of 22 commands + 8 lenses and runs them, saving outputs and back-linking them into the source notes. Optionally, outputs and connections flow back to Tana. `/vn-help` is this page.

## The journey, step by step

| Step | Where | Skill / action | Video |
|---|---|---|---|
| 1. Capture | Tana (phone or desktop) | Record a voice memo. With the template, add `#voice note`; Tana fills **Transcript** and **Transcript Summary (AI)**. Untagged memos work too. | 3 · 02:05, 4 · 00:00 |
| 2. Connect (optional) | Tana | Fill Area(s) / Project(s) / Topic(s) (your Super Folders) and Contemplation(s). | 3 · 10:03, 4 · 06:10 |
| 3. Sync | agent | `/vn-sync` — last 30 days by default. New notes get *enriched*: raw transcripts cleaned, missing summaries written. | — (v3) |
| 4. Catalog | agent | `/vn-catalog new` — proposes areas/projects/topics/entities for uncataloged notes; you confirm; Collections + INDEX regenerate. | 8 · 02:03 (collections idea) |
| 5. Process | agent | `/vn-process <scope> [command]` — suggest → run → output saved under `<archive>/Outputs/` and linked from the sources. | 5, 9 |
| 6. Reuse / write back | agent → Tana | Ask for it: outputs pasted under the source node; confirmed connections mirrored to Super Folder fields (`tana.sync_connections`). | — (v3) |

## Concepts (say them in the user's words)

- **Voice note** — any Tana node with a recording attached. A supertag (`#voice note`) is optional; it adds the Transcript/Summary fields and the Super Folder fields. → video 3 · 02:05
- **Archive** — `archive.dir` (default `Voice-Notes/`), one markdown file per note (`YYYY/YYYY-MM-DD-title.md`) with frontmatter (`docs/frontmatter-schema.md`). Synced once, never overwritten; only frontmatter is maintained afterwards.
- **Sync manifest** — `<archive>/sync-manifest.tsv`: what was synced (`done / exists / failed / empty / skip`). Makes every sync safe to re-run.
- **Enrichment** — the agent's one pass over *new* notes: clean the transcript (filler out, paragraphs in, meaning untouched) and write a summary if Tana didn't. Costs one AI pass per note. Replaces v2's Clean Transcript + Generate Summary. → video 5 · 02:01 (v2 form)
- **History import** — `/vn-sync history`: brings in *every* voice note in the workspace going back years, in date windows (Tana's search returns at most 1000 nodes per query), with a pre-flight count and a cost warning. It copies notes in **without** enrichment and is resumable (`--batch N`, re-run to continue). Clean up afterwards with `/vn-sync enrich --last N`.
- **Super Folders / categories** — Tana's Area(s) / Project(s) / Topic(s) fields on a voice note (the template ships `#VN area / #VN project / #VN topic` plus *merge* tags so your own `#area / #project / #topic` plug in). Since v3.0 these values flow *into* the archive: frontmatter `areas / projects / topics` are pre-filled, `tana_tags` records the node's supertags, `tana_refs` keeps the Tana node id per value. Any other field can be mapped with `tana.category_fields` (e.g. `people: "Person(s)"`). The fields live on the tagged note, not on the audio recording underneath it — so with the template, use `tana.source: both` (setup option 3) or the categories never reach the archive. → video 1 · 04:05 (merging), 3 · 10:03, 4 · 06:10
- **Vocabulary** — `catalog.areas/projects/topics` in `vn-config.yaml`. `/vn-catalog vocab` builds it from your own area/project/topic supertags in Tana; `/vn-catalog new` proposes only from it (and from values already used).
- **Write-back** — `/vn-catalog sync` mirrors confirmed connections to Tana as references (by node id), never removing anything; `/vn-process` can paste an output under the source node. Both need Tana MCP in the session and are skipped silently otherwise.
- **Collections** — a markdown file of wikilinks: by area, project, topic, theme (`/vn-catalog collect "<theme>"`) or hand-picked. Any command can take a collection as its scope. → video 8 · 00:00–10:01
- **Commands vs lenses** — 22 commands in five categories (Understand, Connect, Act, Create, Build), listed in `commands/INDEX.md`; `lens-analysis` reads a note through one of 8 lens files (metaphors, scales, mental models, consciousness, hermetic, zodiac, four agreements, emotions). `mode: oneshot` produces a document; `mode: interactive` opens a conversation (v2's "AI chats"). → video 5 (commands), 9 · 14:00 (chats)
- **Outputs** — files under `<archive>/Outputs/` with `type: vn-output`; each source note lists them under `outputs:` and the command under `processed:`.
- **Contemplations** — recurring life questions you connect notes to; a Tana field on the note, and `contemplation/<name>` tags locally. → video 4 · 12:05
- **Specific words** — the template's custom-vocabulary list that helps Tana transcribe names and jargon. Tana-side only. → video 1 · 10:06

## Where v2 things went

Every v2 command and chat agent survives, consolidated: the exact mapping is at the bottom of `commands/INDEX.md`. Model pickers, node targets and supertag outputs are gone (the harness is the model; files are the outputs). Transcription stays in Tana. **YouTube Notes** (video 7) was **discontinued by Tana** and is not part of v3.

## FAQ

- **Do I need the `#voice note` tag?** No. Every memo with audio syncs by default (`tana.source: all_audio`). The tag adds structured fields and lets you narrow the sync (`--source tagged`). If you *do* use it and want Areas/Projects/Topics in the archive, choose `both` at setup.
- **Do I need the paid Tana template?** Recommended for the capture side (auto-transcription, Super Folder fields, specific words); not required.
- **Claude Cowork without Python?** `/vn-sync` has a pure-MCP fallback for recent notes. For a history import of more than ~50 notes, install Python and run the script — the MCP path puts every note through the model's context.
- **Where do my notes live?** `archive.dir` — inside the repo (gitignored) or an absolute path into your Second Brain / Obsidian vault. Everything is plain markdown with wikilinks.
- **What does it cost in tokens?** Sync itself is cheap (script). Enrichment is one AI pass per note; commands cost what they read (a week of notes, a collection, or the archive slice they pull in). `/vn-sync history` warns before running and skips enrichment.
- **Is Tana required after the first sync?** No. Local files are canonical; Tana steps are optional everywhere. No Tana MCP in the session → those steps are skipped silently.
- **Something didn't sync ("no transcript").** Tana is probably still transcribing; failed rows retry on the next `/vn-sync`.
- **Can I add my own command or lens?** Yes: one markdown file plus one row in `commands/INDEX.md` (`docs/customization.md`).
- **Coming from v2?** Read the mapping in `commands/INDEX.md`, then `/vn-sync history` once to bring your Tana archive down.

## Maintaining help

- Transcripts in `videos/transcripts/` are generated from the course `.srt` files (timestamps → `## mm:ss` headings every ~2 minutes; cues merged into paragraphs). Regenerate with a small stdlib script; never commit `.srt` files.
- When a feature changes, update the concept bullet here first — `/vn-help` reads this page, not the skills.
