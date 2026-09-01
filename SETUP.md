# Setup

Five steps, ~5 minutes. You'll connect Tana's local API to your agent harness, then let the setup flow configure the rest.

## 1. Capture side — Tana

- Use the [Tana Voice Note Agent template](https://pay.hotmart.com/A96283812F?checkoutMode=10) (recommended): voice notes get a `#voice note` supertag with **Transcript** and **Transcript Summary (AI)** fields, auto-transcribed on capture.
- Or roll your own: any supertag on nodes whose transcript lives in a field or in child bullets works. If your field labels differ, set them in `vn-config.yaml → tana.field_labels`.

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

## 4. Choose where notes live

Open `vn-config.yaml`:

- Keep `archive.dir: "Voice-Notes"` to work inside this repo, **or**
- Set an absolute path into your Second Brain, e.g. `archive.dir: "/Users/you/SecondBrain/Voice-Notes"`.
- Pick a `layout`: `by-year` (default) · `by-month` · `flat`.
- Optionally seed `catalog.areas/projects/topics` with your own vocabulary — `/vn-catalog` will propose from these.

## 5. First sync

In your harness, run:

```
/vn-sync setup     # picks workspace + voice-note tag, writes them to vn-config.yaml
/vn-sync --all     # first full sync (or plain /vn-sync for the last 30 days)
```

Or directly in a terminal:

```bash
python3 scripts/sync_voice_notes.py --setup
python3 scripts/sync_voice_notes.py --all --dry-run   # preview
python3 scripts/sync_voice_notes.py --all
```

Then `/vn-catalog` to organize the new files, and `/vn-process` to start working with them.

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
- **Wrong notes synced** — your voice-note tag choice was too broad; re-run `/vn-sync setup` and pick the precise supertag.
