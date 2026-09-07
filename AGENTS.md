# Tana Voice Note Agent v3 — Agent Index

Read by any harness that honours `AGENTS.md` (Codex, Hermes Agent, ...). Claude Code/Cowork read `CLAUDE.md`, which defers here. Keep this file self-sufficient and under ~8k chars.

## What this repo is

The agent-side of the Tana Voice Note Agent: voice notes are captured and transcribed in Tana, mirrored here as markdown files, then analyzed/processed/built-upon by you, the agent. **Local files are canonical once synced; Tana is the capture device and an optional sync target.**

## Map

| Path | What it is |
|---|---|
| `vn-config.yaml` | THE config: Tana connection, archive location/layout, catalog vocabulary. Read it first. Gitignored — created from `vn-config.example.yaml` on first run. `<archive>` throughout these docs means the resolved `archive.dir`, which may point outside this repo. |
| `.agents/skills/<name>/SKILL.md` | The three skills: `vn-sync`, `vn-process`, `vn-catalog`. Claude sees them via `.claude/skills/` symlinks; Hermes via `skills.external_dirs`. |
| `commands/` | The command library — 22 commands in 5 categories plus 8 lens files in `commands/lenses/`. `commands/INDEX.md` is the catalog; a command file's **System Prompt** section becomes your working instructions when it runs (`lens-analysis` also loads its lens file). |
| `scripts/sync_voice_notes.py` | Config-driven sync (pure stdlib). `--setup`, `--since N`, `--all`, `--dry-run`, `--limit N`. |
| `Voice-Notes/` | The archive (unless `archive.dir` points elsewhere): `YYYY/` note files, `Collections/`, `Outputs/`, `INDEX.md`, `sync-manifest.tsv`. |
| `docs/` | `how-it-works.md` (architecture), `frontmatter-schema.md` (canonical note format), `customization.md` (layouts, adding commands). |
| `SETUP.md` / `README.md` | Human onboarding. |

## The three skills

| Skill | Job | Invoke |
|---|---|---|
| `vn-sync` | Tana → archive, then enrichment of new arrivals (clean raw transcripts, fill missing summaries). Script fast path; MCP fallback spelled out in the SKILL. | `/vn-sync [setup|--since N|--all|--no-enrich|status]` |
| `vn-process` | Select scope (note/day/range/collection/theme) → suggest top-3 commands → run → save output + back-link it into the sources → optional Tana write-back. | `/vn-process [scope] [command]` |
| `vn-catalog` | Frontmatter areas/projects/topics/entities, Collections maintenance, INDEX regeneration, optional connection sync to Tana (`tana.sync_connections`). | `/vn-catalog [new|all|collections|collect "<theme>"|index|sync]` |

## Working rules

1. **Local files are canonical.** Tana steps are optional everywhere: no Tana MCP in this session → skip every Tana step silently; nothing is lost.
2. **Never overwrite a synced note file**, and **never edit a note's body** — the one exception is `/vn-sync` enrichment (clean + summarize), which touches only notes written in the current sync. Catalog and process edit frontmatter only.
3. **Secrets:** the Tana token lives in the harness MCP config or `TANA_MCP_TOKEN`. Never write it to any file in this repo, never print it.
4. **Outputs** go under `<archive>/Outputs/` with frontmatter (`type: vn-output`, `command`, `sources`); each source note gets the command appended to `processed:` and a wikilink + value gloss appended to `outputs:`.
5. **The user's ideas are sacred** — commands develop their thinking, never replace it. Fidelity over polish.
6. **Generated files** (`<archive>/INDEX.md`, `<archive>/sync-manifest.tsv`) are regenerated, never hand-patched.
7. `build/build-feature` acts only inside folders the user explicitly names.
8. End substantive turns with one concrete next step.

## Typical flows

- New notes captured this week → `/vn-sync` (sync + enrich) → `/vn-catalog` → `/vn-process` suggest.
- "What was I thinking about X?" → `/vn-process` theme scope → `time-evolution-analyzer` or `connect`.
- Spoken spec (or a free-form question about the notes) → `/vn-process <note> build-document` (or `build-feature` with a named target repo).
- Journal ramble → `/vn-process <note> journal-entry`; heavy charge → add `lens-analysis: four-agreements`.
- Friday → `/vn-process` this week → `weekly-digest`.
