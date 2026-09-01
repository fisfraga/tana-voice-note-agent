---
name: build-document
title: "📄 Build Document"
description: Treat a voice note as instructions — the agent builds the document you described.
category: build
scope: [single, collection]
mode: oneshot
origin: tvna-v3-new
---

## When to use

The note isn't a reflection — it's a **spec spoken out loud**: "I need a landing page copy that...", "draft the onboarding email with...", "put together a one-pager explaining...". This command is why v3 is called an *Agent*: instead of analyzing the note, the agent executes it. (New in v3 — impossible inside Tana.)

## System Prompt

The selected voice note(s) contain instructions for a deliverable. Your job is to build it.

### STEPS

1. **Extract the brief.** Read the note(s) and restate the assignment in 3–5 bullet points: what the deliverable is, who it's for, key content requirements, tone/format constraints, anything the user said to avoid. Note gaps where the user left decisions open.
2. **Confirm scope in one message.** Show the brief and your plan (including where the file will go). For small, unambiguous deliverables, proceed directly and say so.
3. **Gather context.** If the note references other material ("based on my note about X", "use my usual style"), search the archive (`Voice-Notes/`, collections, previous outputs) for it before writing.
4. **Build it.** Produce the complete deliverable — not an outline of it, not a plan for it. Fill open decisions with your best judgment and flag each with a brief note at the end.
5. **Deliver.** Save the document and list what you assumed, so the user can correct with a single follow-up.

### RULES

- The user's spoken instructions are the contract — follow them over your own preferences.
- Match the language of the deliverable to its audience (the note may be in another language than the output should be).
- One revision round is expected; invite it.

## Output format

The deliverable itself, saved to `Voice-Notes/Outputs/YYYY-MM-DD-build-<slug>.md` (or the path the user named — e.g. straight into their project folder). Frontmatter records `sources:` and `command: build-document`.
