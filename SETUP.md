# Setup

Five steps, ~5 minutes. You'll connect Tana's local API to your agent harness, then let the setup flow configure the rest.

## 1. Capture side — Tana

- **Nothing special required:** any Tana voice memo syncs — record one and it has an audio recording attached, which is all `/vn-sync` looks for by default. Everything in this repo works without the template; setup asks once whether you have it and never mentions supertags if you don't.
- With the [Tana Voice Note Agent template](https://fisfraga.com/tana-voice-note-agent) (recommended): voice notes get a `#voice note` supertag with **Transcript**, **Transcript Summary (AI)** and Area(s)/Project(s)/Topic(s) fields, auto-transcribed on capture. Answer *yes* at setup and choose `both`, so those fields come into the archive.
- Or roll your own: transcripts are read from a Transcript field *or* from the node's child bullets, so plain memos and custom supertags both work. If your field labels differ, set them in `vn-config.yaml → tana.field_labels`.

## 2. Enable Tana's local MCP server

In the Tana **desktop** app: **Settings → API / Labs → Local API (MCP)** — enable it and copy the **API token**. The server listens at `http://127.0.0.1:8262/mcp` while Tana is running.

> Tana must be open for sync to work — the server is local to the app.

## 3. Connect your harness

**Claude Code** (also used by the sync script to find the token):

```bash
claude mcp add tana-local --transport http http://127.0.0.1:8262/mcp \
  --header "Authorization: Bearer YOUR_TANA_API_TOKEN"
```

**Claude Cowork / other harnesses:** add an HTTP MCP server with that URL and header wherever your harness configures MCP. If your harness stores MCP config somewhere the script can't read, also export the token for the script:

```bash
export TANA_MCP_TOKEN="YOUR_TANA_API_TOKEN"   # add to your shell profile
```

The token is only ever read from your harness config or that env var — never stored in this repo.

## 4. Create your config and choose where notes live

Run setup once — it creates `vn-config.yaml` from `vn-config.example.yaml`, lists your workspaces, counts the voice memos in the one you pick, and asks what should sync:

```
/vn-sync setup                            # in your harness
python3 scripts/sync_voice_notes.py --setup   # or in a terminal
```

`vn-config.yaml` is **gitignored**, so your workspace id, archive path and catalog vocabulary never end up in a commit (only the example is tracked). Then open it and decide:

- Keep `archive.dir: "Voice-Notes"` to work inside this repo, **or**
- Set an absolute path into your Second Brain, e.g. `archive.dir: "/Users/you/SecondBrain/Voice-Notes"`.
- Pick a `layout`: `by-year` (default) · `by-month` · `flat`.
- Optionally seed `catalog.areas/projects/topics` with your own vocabulary — `/vn-catalog` will propose from these.
- `archive.enrich` (default `true`) cleans raw transcripts and fills missing summaries right after each sync.
- `tana.sync_connections` decides whether confirmed areas/projects/topics mirror back to your Tana Super Folder fields (`/vn-sync setup` asks; default `false` = Tana is capture-only).
- `tana.category_fields` maps your Super Folder fields (`Area(s)` / `Project(s)` / `Topic(s)` in the template) to frontmatter — notes that already carry them in Tana arrive categorized. Add any other superfolder you use. With the template, pick **[3] both** at setup: the fields sit on the tagged note, and `both` syncs that note instead of only the recording underneath it.

> **Your notes stay yours.** `Voice-Notes/` is gitignored — synced notes, generated outputs, collections, the index and the manifest are never committed, even though the default archive lives inside this repo. Only the folder scaffold (the READMEs) is tracked. If you point `archive.dir` somewhere else, that folder is outside git entirely. `vn-config.yaml` is gitignored too; `vn-config.example.yaml` is the tracked template.

## 5. First sync

In your harness, run:

```
/vn-sync            # the last 30 days
/vn-sync history    # or: everything you ever recorded (shows a count and asks first)
```

Or directly in a terminal:

```bash
python3 scripts/sync_voice_notes.py                       # last 30 days
python3 scripts/sync_voice_notes.py --history --dry-run   # count the whole workspace
python3 scripts/sync_voice_notes.py --history             # import it all (resumable)
```

The history import copies notes in without the per-note AI cleanup — do that later in batches with `/vn-sync enrich --last 20`. Then `/vn-catalog vocab` to pull your areas/projects/topics from Tana, `/vn-catalog` to organize the new files, and `/vn-process` to start working with them. Lost? `/vn-help` explains every step and links the course videos.

## Per-harness notes

| Harness | Skills load from | Notes |
|---|---|---|
| **Claude Code** | `.claude/skills/` (symlinks to `.agents/skills/`) | Everything works out of the box. |
| **Claude Cowork** | same | If the sandbox can't run Python, the skills' MCP fallback covers sync. |
| **Codex / others** | `AGENTS.md` + `.agents/skills/` | Invoke skills by asking for them by name; `TANA_MCP_TOKEN` env recommended. |
| **Hermes Agent** | `skills.external_dirs` → `.agents/skills/` | No Tana MCP? Run the script for sync; every Tana write-back step skips cleanly. |

## Troubleshooting

- **`No Tana token found`** — redo step 3; check `claude mcp list` shows `tana-local`.
- **Connection refused** — Tana desktop isn't running, or the local API is disabled.
- **`no transcript` failures on sync** — the note hasn't been transcribed in Tana yet (open it in Tana; the template's automation fills the Transcript field). Re-run `/vn-sync` later; failed rows retry automatically.
- **More notes than you expected** — the default syncs *every* voice memo in the workspace. To take only the ones carrying a supertag, re-run `/vn-sync setup` and choose option [2], or run one sync with `--source tagged --tag <id>`.
- **Connection sync-back fails** — `tana.category_fields` must name your template's Super Folder fields (`Area` / `Areas` / `Area(s)` all match; rename them in `vn-config.yaml` for non-English templates); delete `tana.field_ids` to force re-resolution. Sync-back needs Tana MCP in the session — the script alone can't do it.
- **`search returned 1000`** — Tana caps a search at 1000 results. Use `/vn-sync history`, which pages through the whole workspace.
- **Categories missing on old notes** — they were synced before Tana had the fields, or before this version. Run `python3 scripts/sync_voice_notes.py --refresh-categories --history --dry-run`, then without `--dry-run`.
