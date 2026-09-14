# Changelog

All notable changes to the Tana Voice Note Agent (agent side). The Tana template has its own release notes at [fisfraga.com/tana-voice-note-agent](https://fisfraga.com/tana-voice-note-agent). Version lives in `VERSION`.

## 3.0.0 — 2026-09

The version that earns the name *Agent*. v1 and v2 ran inside Tana, one note at a time. v3 mirrors your voice notes into a local markdown archive and hands them to a real agent — Claude Code, Claude Cowork, Codex, Hermes, anything that reads files — so every command can draw on your whole history.

### Added

- **Local archive, canonical.** `Voice-Notes/YYYY/<date>-<slug>.md` with frontmatter, transcript and summary; `sync-manifest.tsv` makes every sync idempotent and never overwrites a file. Point `archive.dir` into your own Second Brain / Obsidian vault if you have one.
- **Every voice memo syncs by default** — any Tana node with audio attached, tagged or not. A supertag is optional (`tana.source: tagged | both`).
- **`/vn-sync history`** — import everything you ever recorded, in every format: audio memos, `#voice note`, legacy tags (`tana.extra_tag_ids`, repeatable `--tag`), empty nodes tracked as `empty`. Pages past Tana's 1000-result search cap by walking date windows, writes the manifest as it goes (Ctrl-C safe, `--batch N`), shows a pre-flight count with a tag breakdown and a cost warning, and **never enriches** — that is `/vn-sync enrich --last N`, in batches, whenever you want.
- **Super Folder categories from Tana.** Area(s) / Project(s) / Topic(s) — or any field you map in `tana.category_fields` — arrive in `areas/projects/topics` frontmatter, with `tana_tags` (the node's supertags) and `tana_refs` (which values Tana already holds, by node id). `--refresh-categories` back-fills notes synced earlier, frontmatter only.
- **`/vn-catalog vocab`** — pull your own areas / projects / topics out of Tana so the catalog proposes from your structure. Write-back (`tana.sync_connections`) now writes references (`[[Name^id]]`), never plain text, and never removes a value on either side.
- **Enrichment on arrival** — clean run-on transcripts and fill missing summaries for notes written in the current sync (recent syncs only).
- **22 commands + 8 wisdom lenses** in five categories (Understand, Connect, Act, Create, Build), consolidated from the 43 v2 commands — see the mapping at the bottom of `commands/INDEX.md`. New agent-native `build/` category: Build Document, Build Feature, Article Pipeline, Weekly Digest, Project Brief.
- **`/vn-process`** — scope (note / day / range / collection / theme) → top-3 suggestions → run → output saved under `Outputs/` and back-linked into every source note (`processed`, `outputs`).
- **`/vn-catalog`** — areas/projects/topics/entities in frontmatter, living Collections of wikilinks, generated `INDEX.md`.
- **`/vn-help`** — the manual inside the agent: `docs/help.md` plus the nine-video course guide and transcripts in `docs/videos/`, cited with timestamps.
- Harness-agnostic: `AGENTS.md` + `.agents/skills/` for Codex/Hermes; `.claude/skills/` symlinks for Claude Code/Cowork; pure-MCP fallback when Python can't run.
- `tests/test_sync.py` — stdlib unit tests for the parser, query builder, window walker, manifest and frontmatter writer.

### Changed from v2

- Commands no longer live as Tana AI commands; they are markdown prompt files (`commands/<category>/<name>.md`) any agent can run.
- Model pickers, node targets and supertag outputs became file-native equivalents (see `docs/how-it-works.md`, *The v2 lineage*).
- YouTube Notes are not part of v3 — Tana discontinued the feature the v2 command depended on.

### Privacy

- `vn-config.yaml` and the whole archive are gitignored; the Tana token is read from the harness MCP config or `TANA_MCP_TOKEN` and never written to the repo.
