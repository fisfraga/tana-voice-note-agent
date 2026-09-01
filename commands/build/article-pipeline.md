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

A note (or several on one theme) deserves to become a real published piece — Substack, blog, newsletter. This is the front door for all content work: a staged pipeline you can pause and resume, with every stage writing a file so nothing is lost between sessions. *(Absorbs v2's Content Outline, Final Content Piece, and Titles Brainstorm as stages — each stage also runs standalone: "article-pipeline draft", "article-pipeline titles".)*

## Pipeline stages

Run the stage the user asks for; detect the current stage from existing files when they just say "continue". Any stage can run standalone on a suitable input (e.g. `titles` on an existing draft).

### 1. `outline` — voice → outline

Read the source note(s). Extract the thesis, the key ideas, and the natural argument. Use `create/structure-ideas` (outline format) for the structuring itself. Write `Voice-Notes/Outputs/articles/<slug>-outline.md` with frontmatter (`title`, `status: outlined`, `sources`, `source_language`).

### 2. `research` — strengthen the case

For each claim or theme in the outline, gather supporting material: other notes in the archive on the same topic (grep + collections), plus web sources if the harness has search. Write `<slug>-research.md` (`status: researched`) with quotes and links, mapped to outline sections.

### 3. `draft` — write it

Write the full article, enriched with the research, using this embedded persona and craft:

> You are a professional writer who knows the user very well and writes in a similar way as they do. You know human psychology very well. You are an artist — an expert in capturing the reader's attention and writing compelling, vivid pieces — and a transmutation specialist in transforming spoken thoughts into world-class written articles that represent what was said.

- An engaging introduction, a well-developed core, a powerful conclusion and CTA.
- High fidelity to the user's content and style; the article roughly matches the scale of the source material — improve clarity, word selection, and formatting, don't inflate.
- Write toward the reader ("you"); detailed and thorough — do not omit for brevity.
- **Rhythm**: alternate sentence and section length — ideally open and close each section with a single sentence. Patterns like 1/3/1, 1/3/1 + 1/3/1, 1/3/2/1, or 1/3/1 + bullets; adapt freely, the rule of thumb is varied paragraph length for a smoother rhythm.
- Simple structure: introduction, main points, conclusion; section headers only for main points.
- Conclusion pattern: one strong declarative statement → three sentences to round out the argument → one strong concluding sentence as a subhead → five bullets proving the conclusion.

`<slug>-draft.md`, frontmatter adds `word_count`, `status: drafted`.

### 4. `polish` + `titles` — publication formatting

Tighten the prose; format for the target platform (subtitle, section breaks, pull-quotes); compute read time (words ÷ 238). If the title isn't settled, run the embedded titles round:

> Brainstorm **20 titles** that clearly represent the piece and give readers a reason to click. Mix these levers: a counterintuitive idea that goes against conventional wisdom; the outcome the piece helps the reader achieve or avoid; authority backing the premise; enticement — enough information to pull the reader in; the keywords the audience actually searches for. Then pick your **top 3** with reasoning, and refine the user's choice through rounds until it earns the click. *(Remember: readers see the title before anything else — in a feed, an inbox, a search result. The title also determines how the intro gets written.)*

Update the piece's `title:` frontmatter with the winner. `status: polished`.

### 5. `publish` — final handoff

Save the final version as `Voice-Notes/Outputs/articles/<slug>.md` (`status: published`, `date_published`). Update each source note's `processed:` and `outputs:` frontmatter. *(Optional, Tana available)* create the article node in Tana and mark the source voice note processed.

## Rules

- **The user's ideas are sacred** — research supports their argument; it never replaces their voice.
- The article's language follows the target publication, regardless of the note's language.
- Save a file at every stage — nothing is lost between sessions.
- After each stage, tell the user the next stage and stop; only run multiple stages in one go when asked.
