---
name: tag-and-connect-entities
title: "🕸️ Tag and Connect Entities"
description: Extract the people, topics, and contemplations mentioned in a note and connect them to your knowledge structure.
category: create
scope: [single, collection]
mode: oneshot
origin: tvna-v2
---

## When to use

A note mentions people, topics, or ongoing themes you track — you want those entities extracted and wired into your system instead of buried in the transcript. This is the entity-extraction heart of the v2 Autofill/Tag-and-Connect flow, and the per-note engine behind `/vn-catalog`.

## System Prompt

Analyze the voice note transcript and extract the entities it mentions, using these definitions:

- **People** — individuals named or clearly referenced in the note.
- **Topics** — areas of interest or fields of study; a specific theme or concept.
- **Contemplations** — topics, situations, or subjects of contemplation; ongoing ideas the person wants to keep reflecting upon.
- **Areas / Projects** — if the note clearly belongs to one of the user's life areas or active projects (check `vn-config.yaml` `catalog:` vocabulary and existing `Voice-Notes/Collections/`), name it.

Rules:

- Extract only entities genuinely present in the note — no padding.
- Prefer the user's existing vocabulary (config lists, existing collection names, entities already used in other notes' frontmatter) over inventing new names; propose a new entity only when nothing existing fits.
- Keep entity names short and reusable (2–4 words).

## Output format

1. Present the proposed entities grouped by type, marking which are existing vs new.
2. On confirmation, update the note's frontmatter: `areas`, `projects`, `topics` lists (people and contemplations go into `topics` or `tags` per the user's preference in `vn-config.yaml`).
3. If a matching collection file exists in `Voice-Notes/Collections/`, add a wikilink to this note there; offer to create a collection for any new recurring entity.
4. *(Optional, Tana available)* mirror the same assignments to the Tana node's fields.
