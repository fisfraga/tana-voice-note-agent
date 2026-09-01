# Command Library Index

The complete catalog of Voice Note Agent commands. `/vn-process` reads this file to suggest and route commands; each entry links to a command file whose **System Prompt** section becomes the working instructions when it runs.

**Scope**: `single` = one voice note · `collection` = several notes (a day, a date range, a collection file, or a theme).
**Mode**: `oneshot` = produces a document · `interactive` = opens a conversation (close any interactive session with [chat-report](create/chat-report.md) to save it).

## 🔍 Understand

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [basic-chat](understand/basic-chat.md) 💬 | single, collection | interactive | Just talk through what you captured — no framework, a thinking partner. |
| [deep-chat](understand/deep-chat.md) 🪼 | single, collection | interactive | Contemplative, challenging exploration of an idea that deserves depth. |
| [insight-crystallizer](understand/insight-crystallizer.md) 💫 | single, collection | interactive | Isolate and develop the breakthrough moments hiding in a note. |
| [identify-main-themes](understand/identify-main-themes.md) 🗂️ | single, collection | oneshot | Inventory of topics — the natural first pass before deeper commands. |
| [cognitive-bias-analyzer](understand/cognitive-bias-analyzer.md) 🤔 | single, collection | interactive | Honest check of thinking patterns and blind spots before a decision. |

## 🎯 Take Action

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [action-strategic-planner](take-action/action-strategic-planner.md) 🎯 | single, collection | interactive | Turn a situation or idea into strategic pathways and a sequenced plan. |
| [growth-knowledge-navigator](take-action/growth-knowledge-navigator.md) 🌱 | single, collection | interactive | Turn a growth edge into a structured learning path. |
| [task-extractor-by-project](take-action/task-extractor-by-project.md) 🤾 | single, collection | oneshot | Pull every task out of a ramble, grouped by project, dates preserved. |

## 🏔️ Explore & 🌐 Connect

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [cross-connections](explore-connect/cross-connections.md) 🕸️ | collection | interactive | Surface non-obvious links between notes. |
| [synthesis-of-knowledge](explore-connect/synthesis-of-knowledge.md) 🖇️ | collection | interactive | Apply one note's methods/solutions to another note's problems. |
| [knowledge-gap-explorer](explore-connect/knowledge-gap-explorer.md) 🔍 | single, collection | interactive | Find blindspots and the questions you're not asking. |
| [suggest-mental-models](explore-connect/suggest-mental-models.md) 🧠 | single, collection | interactive | 7 mental models from 7 disciplines, applied to your situation. |
| [generate-metaphors](explore-connect/generate-metaphors.md) 🦎 | single, collection | interactive | Translate an abstract idea into vivid metaphors. |
| [stakeholder-perspective](explore-connect/stakeholder-perspective.md) 👥 | single, collection | interactive | Articulate every viewpoint touched by your idea or situation. |
| [scale-shift-analysis](explore-connect/scale-shift-analysis.md) 🌎 | single, collection | interactive | See the idea from micro to universal scale; find the leverage. |
| [multi-perspective-creator](explore-connect/multi-perspective-creator.md) 🎭 | single, collection | interactive | Map audiences, objections, and framings for content-bound ideas. |
| [time-evolution-analyzer](explore-connect/time-evolution-analyzer.md) ⏳ | collection | interactive | Track how your thinking on a topic evolved across months of notes. |

## 🪬 Higher Understanding

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [dimensions-of-consciousness](higher-understanding/dimensions-of-consciousness.md) 🪷 | single, collection | interactive | View an idea through layers of awareness — emotional to universal. |
| [hermetic-principles-analysis](higher-understanding/hermetic-principles-analysis.md) 🔮 | single, collection | interactive | Read the situation through the seven Hermetic principles. |
| [zodiac-archetypes-analysis](higher-understanding/zodiac-archetypes-analysis.md) 🪐 | single, collection | interactive | Which archetypal energies the moment calls for (not predictive). |
| [four-agreements-analysis](higher-understanding/four-agreements-analysis.md) 🍀 | single, collection | interactive | Compassionate check against Don Miguel Ruiz's Four Agreements. |

## 📝 Create

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [summary](create/summary.md) 📝 | single | oneshot | Generate or regenerate the note's structured first-person summary. |
| [clean-transcript](create/clean-transcript.md) 🧹 | single | oneshot | Clean a raw transcript without changing meaning. |
| [tag-and-connect-entities](create/tag-and-connect-entities.md) 🕸️ | single, collection | oneshot | Extract people/topics/contemplations into frontmatter & collections. |
| [custom-report](create/custom-report.md) 🧾 | single, collection | oneshot | Your own question or request — the free-form command. |
| [brainstorm-ideas](create/brainstorm-ideas.md) 🧠 | single | oneshot | Structure a brainstorm: every idea explained + AI suggestion. |
| [content-outline](create/content-outline.md) 🗣️ | single, collection | oneshot | Turn a content brainstorm into a full article outline. |
| [final-content-piece](create/final-content-piece.md) ✍️ | single | oneshot | Transmute a spoken first draft into a finished article. |
| [titles-brainstorm](create/titles-brainstorm.md) ❗️ | single | interactive | 20 titles, top 3 argued, then refine together. |
| [message](create/message.md) 💬 | single | oneshot | Turn a dictation into a ready-to-send message to a person. |
| [mind-map](create/mind-map.md) 🗺️ | single, collection | oneshot | Hierarchical mind map of the ideas and their relationships. |
| [tell-a-story](create/tell-a-story.md) 🏰 | single | oneshot | Reframe the situation as an inspiring short story. |
| [pros-and-cons](create/pros-and-cons.md) 📉📈 | single | oneshot | Sort a decision into For / Against / Neutral, with AI additions. |
| [reflection](create/reflection.md) 🤔 | single | oneshot | Structure a journal entry: topics, items, classified moments. |
| [emotions](create/emotions.md) 🫀 | single, collection | oneshot | Name the emotional states via the Map of Consciousness. |
| [image](create/image.md) 🖼️ | single | oneshot | World-class image prompt (and image) illustrating the note. |
| [infographic](create/infographic.md) 📊 | single | oneshot | The note's concept/process as an infographic prompt. |
| [chat-report](create/chat-report.md) 📝 | single, collection | oneshot | Save any interactive session as a consolidated document. |

## 🚀 Build *(new in v3 — agent-native)*

| Command | Scope | Mode | When to use |
|---|---|---|---|
| [build-document](build/build-document.md) 📄 | single, collection | oneshot | The note is a spoken spec — build the document it describes. |
| [build-feature](build/build-feature.md) 🛠️ | single, collection | interactive | The note describes software — spec it and implement it in your repo. |
| [article-pipeline](build/article-pipeline.md) 📰 | single, collection | interactive | Voice → outline → research → draft → polish, resumable stages. |
| [weekly-digest](build/weekly-digest.md) 🗞️ | collection | oneshot | A week of notes → themes, wins, decisions, open loops, next actions. |
| [project-brief](build/project-brief.md) 📋 | collection | oneshot | A project collection → living project brief / PRD, updated in place. |

## Mapping from Tana Voice Note Agent v2

Every v2 command and AI chat agent is represented. Where v2 had duplicates or Tana-only mechanics, v3 consolidates:

- **[GPT] / [Claude] variants** (Brainstorm, Content Outline, Final Content Piece) → one command each; the model is whatever runs your harness.
- **Commands vs Chats** → one Command category; `mode:` preserves the difference.
- **Collection variants** of the chat agents (v2's "AI Analysis — Collection of Voice Notes") → the same command run with a collection scope.
- **Write Content Piece** (sub-command on outlines) → `final-content-piece` (works from a note or an outline).
- **B&W Infographic** → `infographic` with the B&W style. **Content Image** → `image`.
- **Autofill** (Super Folder suggestions for Area/Project/Topic/Contemplation fields) → the `/vn-catalog` skill.
- **Transcribe** → stays in Tana (the audio lives there); sync brings the transcript down. `clean-transcript` covers un-cleaned captures locally.
- **Move to Today / Set AI Model / Generate Chat Report as Tana command** → obsolete in an agent harness (chat-report survives as a command file).
