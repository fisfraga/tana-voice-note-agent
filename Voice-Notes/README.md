# Voice Notes Archive

This folder is the local, canonical home of your voice notes once `/vn-sync` mirrors them from Tana. (If you pointed `vn-config.yaml → archive.dir` at your own Second Brain, this folder stays empty and that location gets this structure instead.)

```
Voice-Notes/
├── 2026/                    # note files: 2026-08-31-my-idea.md (layout: by-year)
├── Collections/             # wikilink groups by area/project/topic/theme/manual
├── Outputs/                 # everything /vn-process produces
├── INDEX.md                 # generated navigation — never hand-edit
├── sync-manifest.tsv        # sync state — created on first sync, never hand-edit
└── README.md                # this file
```

## Ground rules

- **Note files are yours.** Sync never overwrites an existing file; edit transcripts, add thoughts — nothing will clobber them. The body is touched exactly once — `/vn-sync` enrichment on arrival (clean + summarize); after that only frontmatter is maintained (`/vn-catalog` for areas/projects/topics/tags, `/vn-process` for `processed:` and `outputs:` back-links).
- **`date` in a filename/frontmatter is the Tana capture date.** For imported or migrated audio that can differ from the recording date — trust the transcript when it clearly describes another time.
- **The manifest is memory.** `sync-manifest.tsv` rows: `done` (synced) · `exists` (file was already here) · `failed` (usually still transcribing in Tana — retried next sync) · `skip` (hand-set: never sync this node).
- **INDEX.md and Collections' `## Notes` sections are generated** by `/vn-catalog` — write prose in a collection above its `## Notes` heading; it survives regeneration.

Formats: see [`docs/frontmatter-schema.md`](../docs/frontmatter-schema.md). A worked example note, collection, and output live in [`docs/examples/`](../docs/examples/).
