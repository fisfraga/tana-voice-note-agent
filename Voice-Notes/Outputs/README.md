# Outputs

Everything `/vn-process` produces lands here: `YYYY-MM-DD-<command>-<slug>.md`, plus `articles/`, `digests/`, and `briefs/` for the build-pipeline commands. Each file's frontmatter records its `command` and `sources` (wikilinks back to the notes it came from) — and each source note points forward too: its `processed:` list records the command, and its `outputs:` list carries a wikilink to the output with a one-line value gloss. The archive always knows what has been done to what, in both directions.
