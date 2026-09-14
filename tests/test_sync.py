"""Unit tests for scripts/sync_voice_notes.py (stdlib unittest, no network).

Run:  python3 -m unittest discover -s tests -v
"""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sync_voice_notes.py"

spec = importlib.util.spec_from_file_location("sync_voice_notes", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


TAGGED_NOTE_MD = """- Anne - Casa Nova - Sun, Aug 2, 18:25:39 #voice_note_ <!-- node-id: SM44CNI2VXQo -->
  - **Consumed by Claude Code**: [ ]
  - **Output Language**: [English](tana:ABWbGynQXa8y)
  - **Transcript**:
    - Transcript: <!-- node-id: NJdp_0lCn4wt -->
      - First paragraph of speech.
      - Second paragraph of speech.
  - **Area**: [4. Home & Family #key_area](tana:hg6UQLfpqB4G)
  - **Topic(s)**:
    - [Artificial Intelligence #topic](tana:Kd8sLmQ1xAbc)
    - [Astrology #topic](tana:Zz9yX8wV7uTt)
  - **Transcript Summary (AI)**:
    - 📝 **Note Summary:** <!-- node-id: trnv67uzbkRs -->
      - **Moving house.** Plans for the new home.
"""

MEMO_MD = """- Voice memo captured Mon, Feb 9, 12:17 PM <!-- node-id: -Q39ghCKlcSE -->
  - Hello this is the raw capture text.
  - And a second bullet of it.
"""

FIELDS_NO_TRANSCRIPT_MD = """- Some node #voice_note_ <!-- node-id: abc -->
  - **Area**:
    - [Health #area](tana:H1)
    - [Career #area](tana:C1)
  - **Project(s)**: Plain text project
  - Spoken words as a bare bullet.
"""

MAPPING = {"areas": "area", "projects": "project", "topics": "topic"}


class ParseTests(unittest.TestCase):
    def test_transcript_summary_unchanged(self):
        title, transcript, summary, _ = sync.parse(TAGGED_NOTE_MD, "Transcript", "Transcript Summary (AI)")
        self.assertEqual(title, "Anne - Casa Nova")
        self.assertEqual(transcript, ["First paragraph of speech.", "Second paragraph of speech."])
        self.assertEqual(summary, ["**Moving house.** Plans for the new home."])

    def test_memo_bare_children_are_transcript(self):
        title, transcript, summary, fields = sync.parse(MEMO_MD, "Transcript", "Transcript Summary (AI)")
        self.assertTrue(title.startswith("Voice memo captured"))
        self.assertIsNotNone(sync.CAPTURE_RE.match(title))
        self.assertEqual(transcript, ["Hello this is the raw capture text.", "And a second bullet of it."])
        self.assertEqual(fields, {})

    def test_fields_inline_ref(self):
        _, _, _, fields = sync.parse(TAGGED_NOTE_MD, "Transcript", "Transcript Summary (AI)")
        self.assertEqual(fields["area"], [("4. Home & Family", "hg6UQLfpqB4G", "key_area")])

    def test_fields_child_bullets(self):
        _, _, _, fields = sync.parse(TAGGED_NOTE_MD, "Transcript", "Transcript Summary (AI)")
        self.assertEqual(fields["topic"], [("Artificial Intelligence", "Kd8sLmQ1xAbc", "topic"),
                                           ("Astrology", "Zz9yX8wV7uTt", "topic")])

    def test_non_category_fields_captured_but_harmless(self):
        _, _, _, fields = sync.parse(TAGGED_NOTE_MD, "Transcript", "Transcript Summary (AI)")
        self.assertEqual(fields["output language"], [("English", "ABWbGynQXa8y", None)])
        self.assertEqual(fields["consumed by claude code"], [])   # checkbox: no value

    def test_field_ends_at_next_field_and_plain_text(self):
        _, transcript, _, fields = sync.parse(FIELDS_NO_TRANSCRIPT_MD, "Transcript", "Transcript Summary (AI)")
        self.assertEqual([v[0] for v in fields["area"]], ["Health", "Career"])
        self.assertEqual(fields["project"], [("Plain text project", None, None)])
        # field children no longer leak into the transcript; the bare bullet still does
        self.assertEqual(transcript, ["Spoken words as a bare bullet."])

    def test_norm_label(self):
        for raw in ("Area(s)", "Areas", "Area", "area", " AREA(S) "):
            self.assertEqual(sync.norm_label(raw), "area")
        self.assertEqual(sync.norm_label("Person(s)"), "person")
        self.assertEqual(sync.norm_label("Topic(s)"), "topic")

    def test_categories_from_fields(self):
        _, _, _, fields = sync.parse(TAGGED_NOTE_MD, "Transcript", "Transcript Summary (AI)")
        mapping = dict(MAPPING, people="person")
        cats, refs = sync.categories_from_fields(fields, mapping)
        self.assertEqual(cats, {"areas": ["home-family"], "projects": [],
                                "topics": ["artificial-intelligence", "astrology"], "people": []})
        self.assertEqual(refs, {"areas/home-family": "hg6UQLfpqB4G",
                                "topics/artificial-intelligence": "Kd8sLmQ1xAbc",
                                "topics/astrology": "Zz9yX8wV7uTt"})

    def test_category_fields_config(self):
        self.assertEqual(sync.category_fields({}), MAPPING)
        cfg = {"tana": {"field_labels": {"area": "Área(s)", "project": "Projeto(s)", "topic": "Tema(s)"}}}
        self.assertEqual(sync.category_fields(cfg), {"areas": "área", "projects": "projeto", "topics": "tema"})
        cfg = {"tana": {"category_fields": {"areas": "Area", "projects": "Project", "topics": "Topic",
                                            "people": "Person(s)"}}}
        self.assertEqual(list(sync.category_fields(cfg)), ["areas", "projects", "topics", "people"])
        self.assertEqual(sync.category_fields(cfg)["people"], "person")

    def test_derive_title_and_fingerprint(self):
        self.assertEqual(sync.derive_title("Voice memo captured", ["x"], ["Daily notes", "Video plan - Mon, Feb 9, 12:17:23 PM"]),
                         "Video plan")
        self.assertEqual(sync.derive_title("Voice memo captured", ["short words"], ["Week 07", "Mon, Feb 9"]), "short words")
        self.assertIsNone(sync.fingerprint("Transcript content was not available " * 5))
        self.assertIsNone(sync.fingerprint("too short"))
        long = "word " * 100
        self.assertEqual(sync.fingerprint(long), sync.fingerprint(long.upper() + "!!!"))

    def test_tag_names(self):
        self.assertEqual(sync.tag_names({"tags": [{"id": "x", "name": "voice note "}]}), ["voice-note"])
        self.assertEqual(sync.tag_names({"tags": []}), [])
        self.assertEqual(sync.tag_names({}), [])


class QueryTests(unittest.TestCase):
    def test_single_tag(self):
        self.assertEqual(sync.build_query("tagged", ["T1"]), {"and": [{"hasType": "T1"}]})
        self.assertEqual(sync.build_query("tagged", "T1"), {"and": [{"hasType": "T1"}]})

    def test_multiple_tags_or(self):
        self.assertEqual(sync.build_query("tagged", ["T1", "T2"]),
                         {"and": [{"or": [{"hasType": "T1"}, {"hasType": "T2"}]}]})

    def test_both(self):
        self.assertEqual(sync.build_query("both", ["T1"]),
                         {"and": [{"or": [{"has": "audio"}, {"hasType": "T1"}]}]})

    def test_since_and_window(self):
        self.assertEqual(sync.build_query("all_audio", None, 30),
                         {"and": [{"has": "audio"}, {"created": {"last": 30}}]})
        self.assertEqual(sync.build_query({"has": "audio"}, since=365, older_than=200),
                         {"and": [{"has": "audio"}, {"created": {"last": 365}},
                                  {"not": {"created": {"last": 200}}}]})
        # older_than=0 adds nothing
        self.assertEqual(sync.build_query({"has": "audio"}, older_than=0), {"and": [{"has": "audio"}]})

    def test_resolve_source_merges_tags(self):
        cfg = {"tana": {"source": "both", "voice_note_tag_id": "P", "extra_tag_ids": ["E1", "E2"]}}
        self.assertEqual(sync.resolve_source(cfg, "both", ["C", "E1"]), ("both", ["P", "E1", "E2", "C"]))
        self.assertEqual(sync.resolve_source(cfg, None, ["C"]), ("tagged", ["P", "E1", "E2", "C"]))
        self.assertEqual(sync.resolve_source({}, None, ["C"]), ("tagged", ["C"]))
        self.assertEqual(sync.resolve_source({}, None, None), ("all_audio", []))
        with self.assertRaises(SystemExit):
            sync.resolve_source({}, "tagged", None)


def fake_search_over(days_ago_by_id, cap):
    """A search_fn over synthetic nodes: node -> days ago. Honors the cap and
    the created/not-created shape produced by build_query."""
    def run(query):
        since = older = None
        for clause in query["and"]:
            if "created" in clause:
                since = clause["created"]["last"]
            if "not" in clause:
                older = clause["not"]["created"]["last"]
        hits = [{"id": i} for i, d in days_ago_by_id.items()
                if (since is None or d < since) and (older is None or d >= older)]
        return hits[:cap]
    return run


class WalkWindowsTests(unittest.TestCase):
    def test_covers_every_node_exactly_once(self):
        nodes = {f"n{i}": i * 3 for i in range(400)}       # 0 .. 1197 days ago
        seen = []
        for lo, hi, hits, sat in sync.walk_windows(fake_search_over(nodes, 100), {"has": "audio"}, window=90, cap=100):
            self.assertFalse(sat)
            seen += [h["id"] for h in hits]
        self.assertEqual(sorted(seen), sorted(nodes))
        self.assertEqual(len(seen), len(set(seen)))

    def test_halves_on_saturation(self):
        nodes = {f"d{i}": 5 + (i % 3) for i in range(150)}   # dense cluster days 5..7
        nodes.update({f"t{i}": 400 + i for i in range(20)})   # a tail
        windows = list(sync.walk_windows(fake_search_over(nodes, 100), {"has": "audio"}, window=90, cap=100))
        self.assertTrue(any(hi is not None and hi - lo < 90 for lo, hi, _, _ in windows))
        seen = [h["id"] for _, _, hits, _ in windows for h in hits]
        self.assertEqual(sorted(seen), sorted(nodes))

    def test_saturated_flag_at_window_one(self):
        nodes = {f"x{i}": 2 for i in range(120)}             # 120 nodes on one day, cap 100
        nodes.update({f"t{i}": 300 + i for i in range(5)})
        windows = list(sync.walk_windows(fake_search_over(nodes, 100), {"has": "audio"}, window=8, cap=100))
        self.assertTrue(any(sat for _, _, _, sat in windows))

    def test_stops_on_tail_and_empty(self):
        few = {f"n{i}": i for i in range(10)}
        windows = list(sync.walk_windows(fake_search_over(few, 100), {"has": "audio"}, window=90, cap=100))
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0][:2], (0, None))
        self.assertEqual(len(windows[0][2]), 10)
        empty = list(sync.walk_windows(fake_search_over({}, 100), {"has": "audio"}, cap=100))
        self.assertEqual(empty, [(0, None, [], False)])


class ManifestTests(unittest.TestCase):
    def test_roundtrip_with_and_without_synced_at(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sync-manifest.tsv"
            p.write_text("\n".join(sync.MANIFEST_HEADER[:2] + ["date\tnode_id\tmirrored\ttitle",
                                                                "2026-01-01\tA\tdone\tOld row"]) + "\n")
            rows, order = sync.load_manifest(p)
            self.assertEqual(rows["A"]["synced_at"], "")
            rows["B"] = {"date": "2026-02-02", "node_id": "B", "mirrored": "empty", "title": "New", "synced_at": "2026-09-14"}
            order.append("B")
            sync.write_manifest(p, rows, order)
            self.assertFalse((Path(d) / "sync-manifest.tsv.tmp").exists())
            rows2, order2 = sync.load_manifest(p)
            self.assertEqual(order2, ["A", "B"])
            self.assertEqual(rows2["B"]["synced_at"], "2026-09-14")
            self.assertEqual(rows2["B"]["mirrored"], "empty")
            self.assertTrue(p.read_text().startswith("#"))

    def test_add_hits_and_sort(self):
        rows, order = {}, []
        hits = [{"id": "child", "created": "2026-08-02T21:25:39Z", "name": "Voice memo captured", "tags": []},
                {"id": "parent", "created": "2026-08-02T21:25:39Z", "name": "Anne",
                 "tags": [{"id": "x", "name": "voice note "}]},
                {"id": "older", "created": 1700000000000, "name": "Old", "tags": []}]
        self.assertEqual(sync.add_hits(rows, order, hits), 3)
        self.assertEqual(sync.add_hits(rows, order, hits), 0)
        sync.sort_order(order, rows)
        self.assertEqual(order, ["older", "parent", "child"])
        self.assertEqual(rows["parent"]["tags"], ["voice-note"])


class FrontmatterTests(unittest.TestCase):
    def test_block_order_and_omitted_refs(self):
        cats = {"areas": ["home-family"], "projects": [], "topics": ["ai"], "people": ["anne"]}
        lines = sync.frontmatter_lines("T", "2026-08-02", ["voice-note"], cats, "SM44", ["voice-note"],
                                       {"areas/home-family": "hg6"}, "Tana — WS (id)")
        keys = [l.split(":")[0] for l in lines if l != "---" and not l.startswith("  ")]
        self.assertEqual(keys, ["title", "date", "type", "tags", "areas", "projects", "topics", "people",
                                "processed", "outputs", "tana_id", "tana_tags", "tana_refs", "source"])
        self.assertIn("  areas/home-family: hg6", lines)
        lines = sync.frontmatter_lines("T", "2026-08-02", ["voice-note"], {}, "SM44", [], {}, "src")
        self.assertNotIn("tana_refs:", lines)
        self.assertIn("tana_tags: []", lines)
        self.assertIn("areas: []", lines)

    def test_build_note_matches_legacy_shape(self):
        text = sync.build_note("T", "2026-08-02", ["voice-note"], {}, "SM44", [], {}, "src",
                               ["a", "b"], ["**One.** x"])
        self.assertIn("\n# T\n\n> Voice note recorded 2026-08-02. Mirrored from Tana node `SM44`.\n\n## Transcript\n\na\n\nb\n\n## Summary\n\n- **One.** x\n", text)
        self.assertIsNotNone(sync.TANA_ID_RE.search(text))
        self.assertEqual(sync.TANA_ID_RE.search(text).group(1), "SM44")

    def test_edit_frontmatter_preserves_body(self):
        text = ('---\ntitle: "T"\nareas: []\ntopics:\n  - ai\ntana_id: X\nsource: "s"\n---\n\n'
                "# T\n\nbody  with   spacing\n\n## Transcript\n\nwords\n")
        body = text.split("\n---", 1)[1]
        out = sync.edit_frontmatter(text, {"areas": ["home-family"], "topics": ["ai", "astro"],
                                           "tana_refs": {"areas/home-family": "hg6"}, "tana_tags": []})
        self.assertTrue(out.endswith(body))
        fm, _ = sync.split_frontmatter(out)
        self.assertIn("areas: [home-family]", fm)
        self.assertIn("topics: [ai, astro]", fm)
        self.assertIn("tana_refs:", fm)
        self.assertLess(fm.index("tana_refs:"), fm.index('source: "s"'))
        self.assertEqual(sync.edit_frontmatter(text, {}), text)
        self.assertEqual(sync.edit_frontmatter("no frontmatter", {"areas": ["x"]}), "no frontmatter")

    def test_merge_categories_union_only(self):
        text = ('---\ntitle: "T"\nareas: [local-only]\nprojects: []\ntopics: []\ntana_id: X\n'
                'tana_tags: [voice-note]\ntana_refs:\n  areas/local-only: L1\nsource: "s"\n---\n\nbody\n')
        cats = {"areas": ["home-family", "local-only"], "projects": [], "topics": []}
        out, changes = sync.merge_categories(text, cats, {"areas/home-family": "hg6"}, ["voice-note"])
        self.assertEqual(changes, ["+areas: home-family", "tana_refs"])
        fm, _ = sync.split_frontmatter(out)
        self.assertIn("areas: [local-only, home-family]", fm)
        self.assertIn("  areas/local-only: L1", fm)
        self.assertIn("  areas/home-family: hg6", fm)
        self.assertTrue(out.endswith("\n---\n\nbody\n"))
        same, changes = sync.merge_categories(out, cats, {"areas/home-family": "hg6"}, ["voice-note"])
        self.assertEqual(changes, [])
        self.assertEqual(same, out)


class ConfigTests(unittest.TestCase):
    def test_fallback_parser_inline_map_and_ints(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.yaml"
            p.write_text("tana:\n  extra_tag_ids: [\"A\", B]\n  history: {window_days: 45, batch: 0}\n"
                         "  category_fields:\n    areas: \"Area(s)\"\n  sync_connections: false\n")
            real_yaml = sys.modules.pop("yaml", None)
            try:
                sys.modules["yaml"] = None          # force the stdlib fallback
                cfg = sync.load_config(p)
            finally:
                sys.modules.pop("yaml", None)
                if real_yaml is not None:
                    sys.modules["yaml"] = real_yaml
            self.assertEqual(cfg["tana"]["extra_tag_ids"], ["A", "B"])
            self.assertEqual(cfg["tana"]["history"], {"window_days": 45, "batch": 0})
            self.assertEqual(cfg["tana"]["category_fields"], {"areas": "Area(s)"})
            self.assertIs(cfg["tana"]["sync_connections"], False)


if __name__ == "__main__":
    unittest.main()
