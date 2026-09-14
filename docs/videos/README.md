# Video Guide — Tana Voice Note Agent Course

Playlist: **[Tana Voice Note Agent – Course](https://www.youtube.com/playlist?list=PLl5lrEYUPQvQBSzphagD06u4-QzLRJQDg)** (YouTube, by Fis Fraga).

Videos 1–9 were recorded for v1/v2, where the whole system lived inside Tana. The *concepts* (capture, Super Folders, collections, commands, chats) carry straight into v3 — only the *mechanics* moved from Tana AI to your local agent. The "v3 today" column says what changed. Transcripts (where available) live in [`transcripts/`](transcripts/) with `## mm:ss` headings so the agent can cite a timestamp.

| # | Video | Length | What it covers | v3 today | Transcript |
|---|---|---|---|---|---|
| 1 | [Quick Installation Guide – Get Started in 10 min](https://www.youtube.com/watch?v=RUzYVOP9t_4) | 12:39 | Installing the Tana template: Voice Note Hub on Home, inbox command, merging your Area/Project/Topic tags into the template's Super Folder fields, the *specific words* configuration. | Still the Tana side of setup. The agent side is `SETUP.md` + `/vn-sync setup`. | [01](transcripts/01-quick-installation.md) |
| 2 | [Introducing the Tana Voice Note Agent](https://www.youtube.com/watch?v=hLnga0ifoLQ) | 20:26 | Why voice notes (capture while walking, driving, contemplating), who Fis is, the promise of spoken thought → structured knowledge. | The "why" is unchanged. | [02](transcripts/02-introducing.md) |
| 3 | [How to use the Tana Voice Note Agent – Detailed Explanation](https://www.youtube.com/watch?v=_e7895arSuA) | 22:37 | When to use voice notes; the **six-step workflow**: capture → add `#voice note` → connect to Super Folders → transcribe/summarize → run commands → reuse in your work. | Steps 1–3 happen in Tana; steps 4–6 are `/vn-sync`, `/vn-catalog`, `/vn-process`. | [03](transcripts/03-how-to-use.md) |
| 4 | [Practical Demo of Voice Note Workflow](https://www.youtube.com/watch?v=BeVAumd_YJw) | 18:37 | The six steps on a real note: tagging, Areas/Projects/Topics/Contemplations, transcript + summary, first commands. | Same flow; the commands now run on local files. | [04](transcripts/04-practical-demo.md) |
| 5 | [AI Commands Complete Showcase](https://www.youtube.com/watch?v=Qp0Qu1eDzms) | 37:41 | Every v2 command with a demo: general use, specific scenarios (tasks, message, reflection…), emotions and image generation; the *Prompt or Question* field; output language. | All consolidated into the 22 commands + 8 lenses — mapping at the bottom of `commands/INDEX.md`. | [05](transcripts/05-ai-commands.md) |
| 6 | [Migration Guide for Tana Voice Note Agent](https://www.youtube.com/watch?v=DZvKWx5_bWQ) | 35:46 | Moving from an older template version to a newer one inside Tana. | Tana-side only. For v2 → v3 see `commands/INDEX.md` mapping and `CHANGELOG.md`. | — |
| 7 | [How to Use YouTube Notes](https://www.youtube.com/watch?v=qJVE8G49mgM) | 33:58 | Capturing notes from YouTube videos inside Tana. | **Discontinued** — Tana removed the YouTube Notes feature; it does not exist in v3. Kept for history only. | — |
| 8 | [Enhanced Analysis with Voice Note Collections](https://www.youtube.com/watch?v=U8XWV8sKd9w) | 40:48 | **Collections**: several notes analyzed together; five best practices; three collection-only chat commands; examples. | `<archive>/Collections/*.md` (wikilink groups) via `/vn-catalog collections` / `collect "<theme>"`; any command runs with a collection scope in `/vn-process`. | [08](transcripts/08-collections.md) |
| 9 | [Masterclass on AI Chats in Tana Voice Note Agent](https://www.youtube.com/watch?v=buvpYCCvCGE) | 2:02:16 | The 20 chat agents: trigger command vs. agent, system prompt, models, every agent demonstrated. | Chats are `mode: interactive` commands (`chat`, `insight-crystallizer`, `connect`, lenses…); the model is whatever runs your harness. | [09](transcripts/09-ai-chats.md) |
| 10 | Introducing Tana Voice Note Agent v3.0 — *URL TBD* | ~14 min | Tana ↔ local folders, history import, categories from Tana, `/vn-process`, help inside the agent. | **The v3 video.** | after recording |

## Concept → where it is taught

| Concept | Best video · timestamp |
|---|---|
| Why voice notes / when to capture | 3 · 00:00–02:05 (triggers, morning routine); 2 · 00:01 |
| The six-step workflow | 3 · 02:05–04:09; demoed in 4 · 00:00 |
| Installing the Tana template, Voice Note Hub, inbox command | 1 · 00:00–04:05 |
| Super Folders (Areas / Projects / Topics) + merging your own tags | 1 · 04:05–08:00 (merge), 3 · 10:03–12:03, 4 · 06:10–08:01 |
| Contemplations | 3 · 12:03, 4 · 12:05–14:02 |
| Specific words (custom vocabulary for transcription) | 1 · 10:06–14:03 |
| Transcript + summary fields | 3 · 08:01, 4 · 02:00–06:10 |
| Prompt or Question field (custom report) | 5 · 04:05 |
| Output language | 5 · 24:08 |
| Commands: categories and each command | 5 · 00:00 (categories), 02:01→ one by one |
| Collections | 8 · 00:00–10:01 (what, five best practices), 12:02→ examples |
| AI chats: trigger command vs. agent, system prompt, models | 9 · 14:00–20:01 |
| Agents one by one | 9 · 24:06→ |

## Maintaining this guide

- Add a transcript: drop the video's `.srt` next to the others and re-run the converter (see `docs/help.md` → *Maintaining help*); never commit `.srt` files.
- New video: add a row, keep numbering by playlist position.
