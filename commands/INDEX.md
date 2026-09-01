# Command Library Index

The complete catalog of Voice Note Agent commands — **22 commands · 8 wisdom lenses**, in 5 categories. `/vn-process` reads this file to suggest and route commands; each entry links to a command file whose **System Prompt** section becomes the working instructions when it runs.

**Scope**: `single` = one voice note · `collection` = several notes (a day, a date range, a collection file, or a theme). Either way, the selection is a starting point, not a wall — every command may pull broader context from the archive.
**Mode**: `oneshot` = produces a document · `interactive` = opens a conversation (any interactive session offers a saved consolidation on wind-down — `vn-process` skill, step 4).
**Choices**: when a command has a real decision to make (tone, style, format, lens), the agent uses the harness's ask-user mechanism if present; otherwise it infers, *states the inferred parameters*, and offers one revision round.

## 🔍 Understand

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [chat](understand/chat.md) 💬 | single, collection | interactive | Talk it through — light thinking partner or deep contemplative exploration. |
| [insight-crystallizer](understand/insight-crystallizer.md) 💫 | single, collection | interactive | Isolate and develop the breakthrough moments hiding in a note. |
| [identify-main-themes](understand/identify-main-themes.md) 🗂️ | single, collection | oneshot | Fast inventory of topics — the natural first pass, feeds `/vn-catalog`. |
| [cognitive-bias-analyzer](understand/cognitive-bias-analyzer.md) 🤔 | single, collection | interactive | Honest check of thinking patterns and blind spots before a decision. |
| [knowledge-gap-explorer](understand/knowledge-gap-explorer.md) 🔍 | single, collection | interactive | Find blindspots and the questions you're not asking. |

## 🕸️ Connect

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [connect](connect/connect.md) 🕸️ | collection | interactive | Non-obvious links between notes; apply one note's methods to another's problems. |
| [time-evolution-analyzer](connect/time-evolution-analyzer.md) ⏳ | collection | interactive | Track how your thinking on a topic evolved across months of notes. |
| [perspectives](connect/perspectives.md) 🎭 | single, collection | interactive | Every relevant viewpoint — stakeholders (to act) or audiences (to publish). |
| [lens-analysis](connect/lens-analysis.md) 🔭 | single, collection | interactive | Read the note through a chosen wisdom lens (table below). |

### 🔭 Lenses *(for `lens-analysis` — invoke as "lens-analysis: hermetic"; each is one file in `commands/lenses/`)*

| Lens | Reads the note through |
|---|---|
| [metaphors](lenses/metaphors.md) 🦎 | 10 metaphorical frameworks — translate the abstract into vivid images. |
| [scales](lenses/scales.md) 🌎 | 10 scales, individual → quantum — find where the leverage lives. |
| [mental-models](lenses/mental-models.md) 🧠 | 7 mental models from 7 disciplines, applied in tandem. |
| [consciousness](lenses/consciousness.md) 🪷 | 11 layers of awareness — emotional, intuitive, spiritual, universal. |
| [hermetic](lenses/hermetic.md) 🔮 | The seven Hermetic principles — the law beneath the surface story. |
| [zodiac](lenses/zodiac.md) 🪐 | The 12 zodiacal archetypes — which energies the moment calls for (not predictive). |
| [four-agreements](lenses/four-agreements.md) 🍀 | Don Miguel Ruiz's Four Agreements — a compassionate self-check. |
| [emotions](lenses/emotions.md) 🫀 | David Hawkins's Map of Consciousness — gentle emotional naming. |

## 🎯 Act

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [plan](act/plan.md) 🎯 | single, collection | interactive | Strategy from a note — execution pathways, or a growth/learning path. |
| [task-extractor](act/task-extractor.md) 🤾 | single, collection | oneshot | Pull every task out of a ramble, grouped by project, dates preserved. |
| [pros-and-cons](act/pros-and-cons.md) 📉📈 | single | oneshot | Sort a decision into For / Against / Neutral, with AI additions marked. |

## 📝 Create

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [structure-ideas](create/structure-ideas.md) 🧠 | single, collection | oneshot | Brainstorm → structure: flat list, article outline, or deep mind map. |
| [journal-entry](create/journal-entry.md) 📔 | single, collection | oneshot | Journal note → topics, classified moments, and a gentle emotional read. |
| [message](create/message.md) 💬 | single | oneshot | Turn a dictation into a ready-to-send message to a person. |
| [tell-a-story](create/tell-a-story.md) 🏰 | single | oneshot | Reframe the situation as an inspiring short story. |
| [visual](create/visual.md) 🖼️ | single | oneshot | Image or infographic prompt (and the image, when generation is available). |

## 🚀 Build *(agent-native)*

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [build-document](build/build-document.md) 📄 | single, collection | oneshot | The note is a spoken spec — build the deliverable. Also the free-form "answer this / make me a report" command. |
| [build-feature](build/build-feature.md) 🛠️ | single, collection | interactive | The note describes software — spec it and implement it in your repo. |
| [article-pipeline](build/article-pipeline.md) 📰 | single, collection | interactive | Voice → outline → research → draft → polish → publish, resumable stages. |
| [weekly-digest](build/weekly-digest.md) 🗞️ | collection | oneshot | A week of notes → themes, wins, decisions, open loops, next actions. |
| [project-brief](build/project-brief.md) 📋 | collection | oneshot | A project collection → living project brief / PRD, updated in place. |

## Mapping from Tana Voice Note Agent v2

Every v2 command and AI chat agent is represented — v3 consolidates where v2 had duplicates, Tana-only mechanics, or several names for one job:

**Platform consolidations (v3.0):**

- **[GPT] / [Claude] variants** → one command each; the model is whatever runs your harness.
- **Commands vs Chats** → one Command category; `mode:` preserves the difference.
- **Collection variants** of the chat agents (v2's "AI Analysis — Collection of Voice Notes") → the same command run with a collection scope.
- **Move to Today / Set AI Model** → obsolete in an agent harness.
- **Transcribe** → stays in Tana (the audio lives there); sync brings the transcript down.

**Semantic consolidations (v3.1) — where to find each v2 command:**

- **Basic Chat + Deep Chat** → [chat](understand/chat.md) (light/deep register).
- **Cross-Connections + Synthesis of Knowledge** → [connect](connect/connect.md).
- **Stakeholder Perspective + Multi-Perspective Creator** → [perspectives](connect/perspectives.md) (stakeholders/audiences lens).
- **Suggest Mental Models, Generate Metaphors, Scale Shift, Dimensions of Consciousness, Hermetic Principles, Zodiac Archetypes, Four Agreements, Emotions** → [lens-analysis](connect/lens-analysis.md) + one lens file each.
- **Action Strategic Planner + Growth & Knowledge Navigator** → [plan](act/plan.md) (execution/growth domain).
- **Brainstorm Ideas + Content Outline + Mind Map** → [structure-ideas](create/structure-ideas.md) (list/outline/mindmap format).
- **Reflection + Emotions** → [journal-entry](create/journal-entry.md) (structure + emotional read in one pass).
- **Image + Infographic + B&W Infographic** → [visual](create/visual.md) (image/infographic type, B&W style).
- **Final Content Piece, Titles Brainstorm, Write Content Piece** → stages of [article-pipeline](build/article-pipeline.md) (each runnable standalone).
- **Custom Report** → [build-document](build/build-document.md) (the request can arrive in chat).
- **Generate Summary / Summary (Repeat) + Clean Transcript** → the `/vn-sync` skill's enrichment step (sync already brings Tana's summary down; enrichment covers the rest).
- **Autofill / Tag and Connect Entities** (Super Folder suggestions for Area/Project/Topic/Contemplation fields) → the `/vn-catalog` skill.
- **Generate Chat Report** → the `/vn-process` skill's wind-down step (offered at the end of every interactive session).
