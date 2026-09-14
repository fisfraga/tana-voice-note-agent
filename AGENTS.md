# Tana Voice Note Agent v3 — Agent Index

Read by any harness that honours `AGENTS.md` (Codex, Hermes Agent, ...). Claude Code/Cowork read `CLAUDE.md`, which defers here. Keep this file self-sufficient and under ~8k chars.

## What this repo is

The agent-side of the Tana Voice Note Agent: voice notes are captured and transcribed in Tana, mirrored here as markdown files, then analyzed/processed/built-upon by you, the agent. **Local files are canonical once synced; Tana is the capture device and an optional sync target.**

## Map

| Path | What it is |
|---|---|
| `vn-config.yaml` | THE config: Tana connection, archive location/layout, catalog vocabulary. Read it first. Gitignored — created from `vn-config.example.yaml` on first run. `<archive>` throughout these docs means the resolved `archive.dir`, which may point outside this repo. |
| `.agents/skills/<name>/SKILL.md` | The four skills: `vn-sync`, `vn-process`, `vn-catalog`, `vn-help`. Claude sees them via `.claude/skills/` symlinks; Hermes via `skills.external_dirs`. |
| `commands/` | The command library — 22 commands in 5 categories plus 8 lens files in `commands/lenses/`. `commands/INDEX.md` is the catalog; a command file's **System Prompt** section becomes your working instructions when it runs (`lens-analysis` also loads its lens file). |
| `scripts/sync_voice_notes.py` | Config-driven sync (pure stdlib). Flags: `--setup`, `--since N`, `--history` (alias `--all`; windowed, resumable, `--window N`, `--batch N`, `--yes`, `--retry-empty`), `--source`, `--tag` (repeatable), `--dry-run`, `--limit N`, `--refresh-categories`, `--relink`. Syncs every voice memo (`has: audio`) by default, anchored on the **day-node bullet** (`tana_id`; the hidden audio node is `tana_memo_id` and is never written to); Super Folder fields land in frontmatter (`tana_tags`, `tana_refs`). Tests: `python3 -m unittest discover -s tests -v`. |
| `Voice-Notes/` | The archive (unless `archive.dir` points elsewhere): `YYYY/` note files, `Collections/`, `Outputs/`, `INDEX.md`, `sync-manifest.tsv`. |
| `docs/` | `how-it-works.md` (architecture), `frontmatter-schema.md` (canonical note format), `customization.md` (layouts, history import, categories, adding commands), `help.md` (the in-agent manual), `videos/` (course guide + transcripts). |
| `CHANGELOG.md` / `VERSION` | Release notes and the single version string (3.0.0). |
| `SETUP.md` / `README.md` | Human onboarding. |

## The four skills

| Skill | Job | Invoke |
|---|---|---|
| `vn-sync` | Tana → archive, then enrichment of new arrivals (clean raw transcripts, fill missing summaries). `history` imports everything ever recorded (windowed past Tana's 1000-result cap, resumable, pre-flight count + cost warning, **no enrichment**); `enrich` cleans up in batches afterwards. Script fast path; MCP fallback spelled out in the SKILL. | Skill modes: `/vn-sync [setup|history|enrich --last N|status]`. Script flags passed through: `--since N`, `--source all_audio\|tagged\|both`, `--tag <id>` (repeatable), `--dry-run`, `--batch N`, `--refresh-categories`. Skill-only: `--no-enrich`. |
| `vn-process` | Select scope (note/day/range/collection/theme) → suggest top-3 commands → run → save output + back-link it into the sources → optional Tana write-back. | `/vn-process [scope] [command]` |
| `vn-catalog` | Frontmatter areas/projects/topics/entities, Collections maintenance, INDEX regeneration, `vocab` (pull the user's own areas/projects/topics from Tana), optional connection sync to Tana as references (`tana.sync_connections`). Values that came from Tana (`tana_refs`) are confirmed and never removed. | `/vn-catalog [new|all|vocab|collections|collect "<theme>"|index|sync]` |
| `vn-help` | Explain how the system works, any concept, or any step; cite the course video (with timestamp when it comes from a transcript). Loads `docs/help.md` + `docs/videos/README.md` only. | `/vn-help [question]` |

## Working rules

1. **Local files are canonical.** Tana steps are optional everywhere: no Tana MCP in this session → skip every Tana step silently; nothing is lost.
2. **Write to Tana only through a note's `tana_id`** — the day-node bullet the user sees. Never tag or set fields on a `Voice memo captured …` node (`tana_memo_id`).
3. **Never overwrite a synced note file**, and **never edit a note's body** — the one exception is `/vn-sync` enrichment (clean + summarize), which touches only notes written in the current sync. Catalog and process edit frontmatter only.
4. **Secrets:** the Tana token lives in the harness MCP config or `TANA_MCP_TOKEN`. Never write it to any file in this repo, never print it.
5. **Outputs** go under `<archive>/Outputs/` with frontmatter (`type: vn-output`, `command`, `sources`); each source note gets the command appended to `processed:` and a wikilink + value gloss appended to `outputs:`.
6. **The user's ideas are sacred** — commands develop their thinking, never replace it. Fidelity over polish.
7. **Generated files** (`<archive>/INDEX.md`, `<archive>/sync-manifest.tsv`) are regenerated, never hand-patched.
8. `build/build-feature` acts only inside folders the user explicitly names.
9. End substantive turns with one concrete next step.
10. Questions about how the system works, a concept, a step, or "what can you do" → `/vn-help`. Talking about their own notes → `/vn-process`.

## Typical flows

- First time, years of memos → `/vn-sync history` (copy in, no enrichment) → `/vn-catalog vocab` → `/vn-catalog new` → `/vn-sync enrich --last 20` when wanted.
- New notes captured this week → `/vn-sync` (sync + enrich) → `/vn-catalog` → `/vn-process` suggest.
- "What was I thinking about X?" → `/vn-process` theme scope → `time-evolution-analyzer` or `connect`.
- Spoken spec (or a free-form question about the notes) → `/vn-process <note> build-document` (or `build-feature` with a named target repo).
- Journal ramble → `/vn-process <note> journal-entry`; heavy charge → add `lens-analysis: four-agreements`.
- Friday → `/vn-process` this week → `weekly-digest`.
