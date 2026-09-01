---
name: article-pipeline
title: "📰 Article Pipeline"
description: Voice note → outline → draft → polish → publish-ready article, in resumable stages.
category: build
scope: [single, collection]
mode: interactive
origin: tvna-v3-new
---

## When to use

A note (or several on one theme) deserves to become a real published piece — Substack, blog, newsletter — and you want a staged pipeline you can pause and resume, not a one-shot draft. (Evolves `create/content-outline` + `create/final-content-piece` into a durable workflow; every stage writes a file, so nothing is lost between sessions.)

## Pipeline stages

Run the stage the user asks for; detect the current stage from existing files when they just say "continue".

### 1. `process` — voice → outline

Read the source note(s). Extract the thesis, the key ideas, and the natural argument. Write `Voice-Notes/Outputs/articles/<slug>-outline.md` with frontmatter (`title`, `status: outlined`, `sources`, `source_language`). Use `create/content-outline`'s system prompt for the outline itself.

### 2. `research` — strengthen the case

For each claim or theme in the outline, gather supporting material: other notes in the archive on the same topic (grep + collections), plus web sources if the harness has search. Write `<slug>-research.md` (`status: researched`) with quotes and links, mapped to outline sections.

### 3. `draft` — write it

Write the full article using `create/final-content-piece`'s persona, rhythm techniques, and writing guidelines, enriched with the research. `<slug>-draft.md`, frontmatter adds `word_count`, `status: drafted`.

### 4. `polish` — publication formatting

Tighten the prose; format for the target platform (subtitle, section breaks, pull-quotes); compute read time (words ÷ 238); run `create/titles-brainstorm` if the title isn't settled. `status: polished`.

### 5. `publish` — final handoff

Save the final version as `Voice-Notes/Outputs/articles/<slug>.md` (`status: published`, `date_published`). Update each source note's `processed:` list. *(Optional, Tana available)* create the article node in Tana and mark the source voice note processed.

## Rules

- **The user's ideas are sacred** — research supports their argument; it never replaces their voice.
- The article's language follows the target publication, regardless of the note's language.
- Save a file at every stage — nothing is lost between sessions.
- After each stage, tell the user the next stage and stop; only run multiple stages in one go when asked.
