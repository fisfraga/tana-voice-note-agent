---
name: vn-help
description: Explain how the Voice Note Agent works — concepts, the workflow, what a skill or command does — citing the course videos with timestamps.
argument-hint: "[<question> | <concept> | video <n> | videos]"
version: 3.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Voice-Notes, Help, Onboarding, Videos]
---

# Voice Note Help — how the system works

**Duration:** under a minute | **Layer:** any | **Companion skills:** `/vn-sync`, `/vn-catalog`, `/vn-process`

Answers questions *about the system*: "how does sync work?", "what is a collection?", "what can you do with my notes?", "which video explains Super Folders?". Questions *about the user's own notes* ("what was I thinking about X?") are not help — route them to `/vn-process`.

## Context to read first

1. `docs/help.md` — the concepts, the six-step journey, FAQ, and where v2 things went.
2. `docs/videos/README.md` — the course videos, what each covers, and the concept → timestamp table.

Read a transcript in `docs/videos/transcripts/` **only** when the question is about that video's topic and you want to quote or cite a precise moment. Never load all transcripts (the AI Chats one alone is ~90 KB). Do not read the archive, the command library, or the other SKILL.md files for a help question — if the answer needs a command's details, open just that one command file.

## Modes

- **`<question>` / `<concept>`** (default) — explain in the user's own terms; one short paragraph, then at most three bullets of specifics; link the best video (`title — URL`) and, when the point comes from a transcript, cite the `mm:ss` heading so they can jump there. If the concept changed between v2 and v3, say what moved where (the "v3 today" column).
- **`video <n>`** — what that video covers, its length, and what still applies in v3; offer the two or three most relevant timestamps.
- **`videos`** — the numbered list from `docs/videos/README.md` with one line each.
- **No argument** — a five-line tour: capture → sync → catalog → process → write-back, and "ask me about any of these".

## Rules

- Be accurate about what exists **now**: videos 1–9 show v1/v2 mechanics inside Tana; the concepts hold, the buttons don't. Say so when it matters. YouTube Notes (video 7) is discontinued — never present it as available.
- Cite, don't dump: link and timestamp rather than pasting transcript passages (a sentence or two of quotation is fine).
- Costs are real: when the question touches enrichment, history import, or the MCP fallback, mention the token/time implications from `docs/help.md`.
- If the answer is "run a skill", give the exact invocation.
- Don't invent features; if `docs/help.md` doesn't cover it, say so and point to `docs/customization.md` or the repo.
- End with one concrete next step (usually the skill or command to try).
