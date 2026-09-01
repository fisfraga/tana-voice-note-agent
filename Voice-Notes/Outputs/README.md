# Outputs

Everything `/vn-process` produces lands here: `YYYY-MM-DD-<command>-<slug>.md`, plus `articles/`, `digests/`, and `briefs/` for the build-pipeline commands. Each file's frontmatter records its `command` and `sources` (wikilinks back to the notes it came from), and each source note's `processed:` list records the command — so the archive always knows what has been done to what.
