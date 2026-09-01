# Tana Voice Note Agent v3 — Agent Index

Read by any harness that honours `AGENTS.md` (Codex, Hermes Agent, ...). Claude Code/Cowork read `CLAUDE.md`, which defers here. Keep this file self-sufficient and under ~8k chars.

## What this repo is

The agent-side of the Tana Voice Note Agent: voice notes are captured and transcribed in Tana, mirrored here as markdown files, then analyzed/processed/built-upon by you, the agent. **Local files are canonical once synced; Tana is the capture device and an optional sync target.**

## Map

| Path | What it is |
|---|---|
| `vn-config.yaml` | THE config: Tana connection, archive location/layout, catalog vocabulary. Read it first. |
| `.agents/skills/<name>/SKILL.md` | The three skills: `vn-sync`, `vn-process`, `vn-catalog`. Claude sees them via `.claude/skills/` symlinks; Hermes via `skills.external_dirs`. |
| `commands/` | The command library — 43 prompt files in 6 categories. `commands/INDEX.md` is the catalog; a command file's **System Prompt** section becomes your working instructions when it runs. |
| `scripts/sync_voice_notes.py` | Config-driven sync (pure stdlib). `--setup`, `--since N`, `--all`, `--dry-run`, `--limit N`. |
| `Voice-Notes/` | The archive (unless `archive.dir` points elsewhere): `YYYY/` note files, `Collections/`, `Outputs/`, `INDEX.md`, `sync-manifest.tsv`. |
| `docs/` | `how-it-works.md` (architecture), `frontmatter-schema.md` (canonical note format), `customization.md` (layouts, adding commands). |
| `SETUP.md` / `README.md` | Human onboarding. |

## The three skills

| Skill | Job | Invoke |
|---|---|---|
| `vn-sync` | Tana → archive. Script fast path; MCP fallback spelled out in the SKILL. | `/vn-sync [setup|--since N|--all|status]` |
| `vn-process` | Select scope (note/day/range/collection/theme) → suggest top-3 commands → run → save output → optional Tana write-back. | `/vn-process [scope] [command]` |
| `vn-catalog` | Frontmatter areas/projects/topics, Collections maintenance, INDEX regeneration. | `/vn-catalog [new|all|collections|collect "<theme>"|index]` |

## Working rules

1. **Local files are canonical.** Tana steps are optional everywhere: no Tana MCP in this session → skip every Tana step silently; nothing is lost.
2. **Never overwrite a synced note file** (sync) and **never edit a note's body** (catalog — frontmatter only; only the `clean-transcript` command may touch a transcript, explicitly).
3. **Secrets:** the Tana token lives in the harness MCP config or `TANA_MCP_TOKEN`. Never write it to any file in this repo, never print it.
4. **Outputs** go under `Voice-Notes/Outputs/` with frontmatter (`type: vn-output`, `command`, `sources`); source notes get the command appended to their `processed:` list.
5. **The user's ideas are sacred** — commands develop their thinking, never replace it. Fidelity over polish.
6. **Generated files** (`Voice-Notes/INDEX.md`, `sync-manifest.tsv`) are regenerated, never hand-patched.
7. `build/build-feature` acts only inside folders the user explicitly names.
8. End substantive turns with one concrete next step.

## Typical flows

- New notes captured this week → `/vn-sync` → `/vn-catalog` → `/vn-process` suggest.
- "What was I thinking about X?" → `/vn-process` theme scope → `time-evolution-analyzer` or `cross-connections`.
- Spoken spec → `/vn-process <note> build-document` (or `build-feature` with a named target repo).
- Friday → `/vn-process` this week → `weekly-digest`.
