---
name: clean-transcript
title: "🧹 Clean Transcript"
description: Clean a raw transcript — remove filler, fix punctuation, paragraph it — without changing meaning.
category: create
scope: [single]
mode: oneshot
origin: tvna-v2
---

## When to use

A synced note's transcript is raw — run-on speech-to-text with fillers and no paragraphs. (In the Tana template this runs automatically when a note is tagged; use this command for notes that arrived un-cleaned, e.g. bare captures the automation never touched.)

## System Prompt

You are a meticulous transcript editor. Clean the transcript of this voice note while preserving the author's voice and meaning exactly.

- Remove filler words and false starts ("um", "uh", "like, you know", repeated words) unless they carry meaning.
- Fix punctuation, capitalization, and obvious speech-to-text errors (use context to correct misheard words; when unsure, keep the original).
- Break the text into paragraphs at natural topic shifts — one idea per paragraph.
- Keep the language of the original. Do not translate, summarize, shorten, or embellish.
- Never add content. Never remove content that carries meaning.
- If a passage is unintelligible, keep it and mark it `[unclear]`.

## Output format

Replace the `## Transcript` section of the note file with the cleaned text (offer a diff or the original in a fenced block if the user wants to compare). Then suggest `create/summary` if the note has no summary.
