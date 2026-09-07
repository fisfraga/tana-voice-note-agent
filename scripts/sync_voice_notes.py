#!/usr/bin/env python3
"""
Tana Voice Note Agent — sync script (v3).

Mirrors your voice memos from Tana's local MCP server into a folder of markdown
files with YAML frontmatter. Pure stdlib; PyYAML is used only if present.

By default it syncs EVERY voice memo in the workspace — any node with an audio
recording attached (Tana's `has: audio`), whether or not it carries a supertag.
Narrowing to a supertag is opt-in: `--source tagged --tag <id>`, or `tana.source`
in vn-config.yaml.

Configuration lives in vn-config.yaml at the repo root (see that file for docs).
The bearer token is NEVER stored in this repo: it is read from the harness MCP
config (~/.claude.json -> mcpServers.<name>.headers.Authorization) or from the
TANA_MCP_TOKEN environment variable.

Usage:
  python3 scripts/sync_voice_notes.py --setup            # first-time: pick workspace + what to sync
  python3 scripts/sync_voice_notes.py                    # sync memos created in the last 30 days
  python3 scripts/sync_voice_notes.py --source tagged --tag <id>   # only one supertag
  python3 scripts/sync_voice_notes.py --source both      # memos + tagged nodes
  python3 scripts/sync_voice_notes.py --since 90         # widen the window
  python3 scripts/sync_voice_notes.py --all              # full history
  python3 scripts/sync_voice_notes.py --dry-run          # show what would be written
  python3 scripts/sync_voice_notes.py --limit 5          # stop after N new files

Idempotency (three layers, safe to re-run any time):
  1. manifest rows marked done/exists/skip are never fetched again
  2. an existing file on disk is never overwritten (row becomes "exists")
  3. the manifest (Voice-Notes/sync-manifest.tsv) is rewritten in place
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "vn-config.yaml"
EXAMPLE_PATH = REPO / "vn-config.example.yaml"
URL_DEFAULT = "http://127.0.0.1:8262/mcp"
MANIFEST_HEADER = [
    "# Voice Note Agent sync manifest — maintained by scripts/sync_voice_notes.py",
    "# mirrored: done (synced) | exists (file already on disk, untouched) | failed | skip (hand-set: never sync)",
    "date\tnode_id\tmirrored\ttitle",
]


# ---------------------------------------------------------------- config ----

def bootstrap_config():
    """First run: create the personal vn-config.yaml from the tracked example.
    The personal file is gitignored so workspace ids, archive paths and catalog
    vocabulary never reach the repo."""
    if CONFIG_PATH.exists() or not EXAMPLE_PATH.exists():
        return
    CONFIG_PATH.write_text(EXAMPLE_PATH.read_text())
    print(f"Created {CONFIG_PATH.name} from {EXAMPLE_PATH.name} "
          "(gitignored — this is yours to edit).")


def load_config(path):
    """Load vn-config.yaml. Uses PyYAML when available, else a minimal parser
    that understands the subset of YAML this config file uses (nested maps,
    scalars, inline [] lists, quoted strings, # comments)."""
    text = path.read_text() if path.exists() else ""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        pass
    # Join wrapped inline lists ("key: [a, b,\n           c]") into one logical line.
    # Without this an unterminated "[" fell through to the scalar branch and the
    # value became the truncated *string* "[a, b," — silently, with no error.
    logical, buf = [], None
    for raw in text.split("\n"):
        bare = raw.split("#", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        if buf is not None:
            buf += " " + bare.strip()
            if "]" in bare:
                logical.append(buf)
                buf = None
            continue
        if bare.partition(":")[2].strip().startswith("[") and "]" not in bare:
            buf = bare
        else:
            logical.append(raw)
    if buf is not None:
        logical.append(buf)          # unterminated list: let the scalar branch see it

    root, stack = {}, [(-1, {})]
    stack[0] = (-1, root)
    for raw in logical:
        line = raw.split("#", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        key = key.strip().strip("'\"")
        val = val.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if val == "":
            child = {}
            parent[key] = child
            stack.append((indent, child))
        elif val == "{}":
            parent[key] = {}
        elif val.startswith("[") and val.endswith("]"):
            parent[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            scalar = val.strip()
            if scalar[:1] not in "'\"":
                low = scalar.lower()
                if low in ("true", "false"):      # keep booleans boolean: the
                    parent[key] = low == "true"   # string 'false' is truthy
                    continue
                if low in ("null", "~", ""):
                    parent[key] = None
                    continue
            parent[key] = scalar.strip("'\"")
    return root


def cfg_get(cfg, path, default=""):
    cur = cfg
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur if cur not in (None, {}) else default


def save_config_values(path, updates):
    """Set top-of-tree scalar values like tana.workspace_id in vn-config.yaml,
    editing lines in place so comments and structure survive."""
    lines = path.read_text().split("\n")
    for dotted, value in updates.items():
        section, key = dotted.split(".", 1)
        in_section = False
        done = False
        for i, line in enumerate(lines):
            stripped = line.split("#", 1)[0].rstrip()
            if stripped == f"{section}:":
                in_section = True
                continue
            if in_section and stripped and not line.startswith(" "):
                break  # left the section without finding the key
            if in_section and stripped.lstrip().startswith(f"{key}:"):
                indent = len(line) - len(line.lstrip())
                comment = line.split("#", 1)[1].rstrip() if "#" in line else ""
                suffix = f"  # {comment.strip()}" if comment else ""
                lines[i] = f'{" " * indent}{key}: "{value}"{suffix}'
                done = True
                break
        if not done:
            sys.exit(f"could not find {dotted} in {path} — add it by hand")
    path.write_text("\n".join(lines))


# ------------------------------------------------------------- transport ----

def load_endpoint(cfg):
    url = os.environ.get("TANA_MCP_URL") or cfg_get(cfg, "tana.url", URL_DEFAULT)
    token = os.environ.get("TANA_MCP_TOKEN")
    if token:
        auth = token if token.lower().startswith("bearer") else f"Bearer {token}"
        return url, auth
    server = cfg_get(cfg, "tana.mcp_server_name", "tana-local")
    claude_json = Path.home() / ".claude.json"
    if claude_json.exists():
        try:
            hcfg = json.load(open(claude_json))
            srv = (hcfg.get("mcpServers") or {}).get(server) or {}
            auth = (srv.get("headers") or {}).get("Authorization")
            if auth:
                return srv.get("url", url), auth
        except Exception:
            pass
    sys.exit(
        "No Tana token found. Either:\n"
        f"  - add the '{server}' MCP server to your harness config (~/.claude.json), or\n"
        "  - export TANA_MCP_TOKEN=<your Tana local API token>\n"
        "See SETUP.md."
    )


class MCP:
    def __init__(self, url, auth):
        self.url, self.auth, self.sid = url, auth, None

    def _post(self, body):
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", self.auth)
        if self.sid:
            req.add_header("Mcp-Session-Id", self.sid)
        try:
            r = urllib.request.urlopen(req, timeout=90)
        except urllib.error.URLError as e:
            sys.exit(
                f"Can't reach Tana MCP at {self.url}\n"
                f"  {e.reason}\n"
                "Start your Tana local MCP server (or set TANA_MCP_URL), then re-run.\n"
                "Nothing was written — this command is always safe to retry."
            )
        with r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                self.sid = sid
            raw = r.read().decode()
        for line in raw.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        return json.loads(raw) if raw.strip() else None

    def init(self):
        self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "voice-note-sync", "version": "3"}}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def call(self, tool, args):
        r = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": tool, "arguments": args}})
        content = (r or {}).get("result", {}).get("content", [])
        return "\n".join(x.get("text", "") for x in content if x.get("type") == "text")

    def call_json(self, tool, args):
        text = self.call(tool, args)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []


# --------------------------------------------------------------- parsing ----

NODEID_RE = re.compile(r"\s*<!--\s*node-id:[^>]*-->")
TIMESTAMP_RE = re.compile(
    r"\s*[-–]\s*(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\w{3}\s+\d{1,2},?(?:\s+\d{4},?)?|Today|Yesterday),?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*$", re.I)
PREFIX_RE = re.compile(r"^\s*\[[ xX]\]\s*")                  # Tana checkbox / status prefix
MEDIA_RE = re.compile(r"^!\[([^\]]*)\]\([^)]*\)\s*$")        # node named by media embed -> alt text
TAGSUFFIX_RE = re.compile(r"\s*#[\w_-]+(\s*,\s*#[\w_-]+)*\s*$")
CAPTURE_RE = re.compile(r"^(voice\s+memo|audio)\s+captured\b", re.I)   # Tana's generic capture label


def clean(line):
    return NODEID_RE.sub("", line).rstrip()


def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80] or "untitled"


def parse(md, transcript_label, summary_label):
    """Split Tana read_node markdown into (title, transcript_lines, summary_lines)."""
    t_marker = f"**{transcript_label.lower()}**:"
    s_marker = f"**{summary_label.lower()}**:"
    lines = md.split("\n")
    title = ""
    if lines:
        t = clean(lines[0]).lstrip()
        t = t[2:] if t.startswith("- ") else t
        t = TAGSUFFIX_RE.sub("", t)          # drop trailing #tags FIRST (order matters)...
        mm = MEDIA_RE.match(t.strip())       # ...so an ![alt](url) name can be unwrapped
        if mm:
            t = mm.group(1)
        t = PREFIX_RE.sub("", t)
        title = TIMESTAMP_RE.sub("", t).strip()

    transcript, summary, mode = [], [], None
    bare = []                      # direct child bullets when there is no Transcript field
    saw_field = False
    for raw in lines[1:]:
        c = clean(raw)
        if not c.strip():
            continue
        low = c.strip().lower()
        if t_marker in low:
            mode = "t"; saw_field = True; continue
        if s_marker in low:
            mode = "s"; continue
        if re.match(r"^\*\*[^*]+\*\*:", c.strip().lstrip("- ")) and transcript_label.lower() not in low:
            mode = None; continue          # some other field (Output Language, ...)
        body = c.strip()
        body = body[2:] if body.startswith("- ") else body
        if body.lower().rstrip(":.") == transcript_label.lower() or "note summary" in body.lower():
            continue
        if mode == "t":
            transcript.append(body)
        elif mode == "s":
            summary.append(body)
        elif mode is None:
            bare.append(body)
    if not transcript and not saw_field and bare:
        transcript = bare        # raw captures: spoken text sits as direct child bullets
    return title, transcript, summary


def derive_title(title, transcript):
    """Tana names an untagged capture 'Voice memo captured Mon, Feb 9, 12:17' —
    the same label on every recording, which would make every filename and index
    row look alike. When that generic label is all we have, lead with the words
    actually spoken instead."""
    if not transcript:
        return title
    if title and not CAPTURE_RE.match(title.strip()):
        return title
    spoken = " ".join(" ".join(transcript).split())
    if not spoken:
        return title
    if len(spoken) <= 70:
        return spoken
    return spoken[:70].rsplit(" ", 1)[0].rstrip(" ,.;:—-") + "…"


def derive_tags(title, keywords):
    tags = ["voice-note"]
    t = (title or "").lower()
    for kw, tag in (keywords or {}).items():
        if kw.lower() in t and tag not in tags:
            tags.append(tag)
    return tags


# --------------------------------------------------------------- manifest ---

def load_manifest(path):
    rows, order = {}, []
    if not path.exists():
        return rows, order
    for line in path.read_text().split("\n"):
        if not line.strip() or line.startswith("#") or line.startswith("date\t"):
            continue
        p = line.split("\t")
        if len(p) < 4:
            continue
        rows[p[1]] = {"date": p[0], "node_id": p[1], "mirrored": p[2], "title": p[3]}
        order.append(p[1])
    return rows, order


def write_manifest(path, rows, order):
    lines = list(MANIFEST_HEADER)
    for nid in order:
        r = rows[nid]
        lines.append("\t".join([r["date"], r["node_id"], r["mirrored"], r["title"]]))
    path.write_text("\n".join(lines) + "\n")


# ------------------------------------------------------------------ query ---

SOURCE_MODES = ("all_audio", "tagged", "both")


def build_query(source, tag_id, since=None):
    """The search_nodes query for a source mode.

    all_audio (default) is Tana's `has: audio` — every node with a recording
    attached, tagged or not. That is what a voice memo IS; a supertag is one
    way some people mark them, not a requirement of the format.
    """
    if source == "tagged":
        clause = {"hasType": tag_id}
    elif source == "both":
        clause = {"or": [{"has": "audio"}, {"hasType": tag_id}]}
    else:
        clause = {"has": "audio"}
    query = {"and": [clause]}
    if since is not None:
        query["and"].append({"created": {"last": since}})
    return query


def resolve_source(cfg, cli_source, cli_tag):
    """Settle the source mode from CLI flags over config, and fail loudly only
    when a tag-based mode was asked for without a tag."""
    source = cli_source or cfg_get(cfg, "tana.source", "all_audio") or "all_audio"
    if source not in SOURCE_MODES:
        sys.exit(f"unknown source '{source}' — choose one of: {', '.join(SOURCE_MODES)}")
    tag_id = cli_tag or cfg_get(cfg, "tana.voice_note_tag_id")
    if cli_tag and not cli_source:
        source = "tagged"                     # --tag alone means "only that tag"
    if source in ("tagged", "both") and not tag_id:
        sys.exit(
            f"source '{source}' needs a supertag, but tana.voice_note_tag_id is empty.\n"
            "  - run with --setup to pick one, or\n"
            "  - pass --tag <tagId>, or\n"
            "  - use the default --source all_audio to sync every voice memo."
        )
    return source, tag_id


def describe_source(source, tag_name=""):
    if source == "tagged":
        return f"notes tagged {tag_name or 'your voice-note supertag'}"
    if source == "both":
        return f"voice memos (audio) and notes tagged {tag_name or 'your voice-note supertag'}"
    return "voice memos (every node with audio attached)"


# ------------------------------------------------------------------ setup ---

def run_setup(mcp, cfg):
    print("Workspaces loaded in Tana:")
    workspaces = mcp.call_json("list_workspaces", {})
    for i, ws in enumerate(workspaces):
        print(f"  [{i}] {ws.get('name')}  ({ws.get('id')})")
    idx = input("Which workspace holds your voice notes? [number]: ").strip()
    ws = workspaces[int(idx)]

    def count(query):
        try:
            r = mcp.call_json("search_nodes", {"query": query, "limit": 1000,
                                               "workspaceIds": [ws["id"]]})
            if isinstance(r, dict):
                r = r.get("nodes") or r.get("results") or []
            return len(r)
        except Exception:
            return -1

    # -- what counts as a voice note ----------------------------------------
    n_audio = count({"and": [{"has": "audio"}]})
    print(f"\n{ws['name']} holds {n_audio} voice memo(s) — nodes with a recording attached.")
    print("\nWhat should sync pull in?")
    print("  [1] every voice memo                                   (default, recommended)")
    print("  [2] only memos carrying a specific supertag")
    print("  [3] both — every voice memo plus everything with that supertag")
    choice = input("Choose [1]: ").strip() or "1"
    source = {"1": "all_audio", "2": "tagged", "3": "both"}.get(choice, "all_audio")

    tag = None
    if source in ("tagged", "both"):
        print(f"\nTags in {ws['name']} (voice-looking ones first):")
        tags = mcp.call_json("list_tags", {"workspaceId": ws["id"], "limit": 200})
        voiceish = [t for t in tags if "voice" in (t.get("name") or "").lower()]
        candidates = voiceish + [t for t in tags if t not in voiceish] if voiceish else tags
        candidates = candidates[:40]
        for i, t in enumerate(candidates):
            n = count({"and": [{"hasType": t["id"]}]})
            print(f"  [{i}] #{t.get('name')}  — {n} node(s)")
        idx = input("Which tag marks a voice note? [number]: ").strip()
        tag = candidates[int(idx)]

    updates = {
        "tana.workspace_id": ws["id"],
        "tana.workspace_name": ws["name"],
        "tana.source": source,
    }
    if tag:
        updates["tana.voice_note_tag_id"] = tag["id"]
    save_config_values(CONFIG_PATH, updates)

    tag_name = f"#{tag.get('name')}" if tag else ""
    print(f"\nSaved to {CONFIG_PATH.name}: workspace '{ws['name']}', "
          f"syncing {describe_source(source, tag_name)}.")
    if source == "all_audio":
        print("Change your mind later with --source tagged --tag <id>, or edit tana.source.")
    print("Run the script again (optionally with --dry-run) to sync.")


# ------------------------------------------------------------------- main ---

TANA_ID_RE = re.compile(r"^tana_id:\s*[\"']?([A-Za-z0-9_-]+)", re.M)


def index_by_tana_id(archive):
    """Map every tana_id already in the archive to its file.

    Dedupe cannot rely on the filename alone: a note retitled in Tana slugs
    differently, and archives predating this script may use another slugging
    convention entirely (accents kept, say). tana_id is the stable identity,
    and it is in every note's frontmatter.
    """
    index = {}
    for f in archive.rglob("*.md"):
        try:
            head = f.read_text(errors="replace")[:1500]
        except OSError:
            continue
        m = TANA_ID_RE.search(head)
        if m:
            index.setdefault(m.group(1), f)
    return index


def note_dir(archive, layout, date):
    if layout == "by-month":
        return archive / date[:4] / date[5:7]
    if layout == "flat":
        return archive
    return archive / date[:4]     # by-year (default)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", action="store_true", help="interactive first-time configuration")
    ap.add_argument("--since", type=int, default=30, help="only consider notes created in the last N days (default 30)")
    ap.add_argument("--all", action="store_true", help="consider the entire history")
    ap.add_argument("--limit", type=int, default=0, help="stop after writing N files")
    ap.add_argument("--dry-run", action="store_true", help="report, but write nothing")
    ap.add_argument("--source", choices=SOURCE_MODES, default=None,
                    help="what counts as a voice note: all_audio (default — every node with "
                         "a recording attached), tagged (only voice_note_tag_id), or both")
    ap.add_argument("--tag", default=None, metavar="TAG_ID",
                    help="sync only nodes with this supertag id (implies --source tagged)")
    a = ap.parse_args()

    bootstrap_config()
    cfg = load_config(CONFIG_PATH)
    mcp = MCP(*load_endpoint(cfg))
    mcp.init()

    if a.setup:
        run_setup(mcp, cfg)
        return

    source_mode, tag_id = resolve_source(cfg, a.source, a.tag)
    workspace_id = cfg_get(cfg, "tana.workspace_id")
    workspace_name = cfg_get(cfg, "tana.workspace_name", "Tana")
    t_label = cfg_get(cfg, "tana.field_labels.transcript", "Transcript")
    s_label = cfg_get(cfg, "tana.field_labels.summary", "Transcript Summary (AI)")
    keywords = cfg_get(cfg, "catalog.tag_keywords", {}) or {}

    archive_cfg = cfg_get(cfg, "archive.dir", "Voice-Notes")
    archive = Path(archive_cfg) if os.path.isabs(str(archive_cfg)) else REPO / archive_cfg
    layout = cfg_get(cfg, "archive.layout", "by-year")
    fname_pattern = cfg_get(cfg, "archive.filename", "{date}-{slug}.md")
    manifest_path = archive / "sync-manifest.tsv"
    archive.mkdir(parents=True, exist_ok=True)
    id_index = index_by_tana_id(archive)

    # -- discover ------------------------------------------------------------
    query = build_query(source_mode, tag_id, None if a.all else a.since)
    args = {"query": query, "limit": 1000}
    if workspace_id:
        args["workspaceIds"] = [workspace_id]
    found = mcp.call_json("search_nodes", args)
    if isinstance(found, dict):      # some servers wrap the array
        found = found.get("nodes") or found.get("results") or []
    print(f"found {len(found)} {describe_source(source_mode)}"
          + ("" if a.all else f" in the last {a.since} days"))

    rows, order = load_manifest(manifest_path)
    for n in found:
        nid = n.get("id")
        if not nid or nid in rows:
            continue
        created = n.get("created")
        if isinstance(created, (int, float)):
            date = dt.datetime.fromtimestamp(created / 1000).strftime("%Y-%m-%d")
        else:
            date = str(created or "")[:10] or dt.date.today().isoformat()
        rows[nid] = {"date": date, "node_id": nid, "mirrored": "pending",
                     "title": (n.get("name") or "").replace("\t", " ")[:160]}
        order.append(nid)
    order.sort(key=lambda nid: rows[nid]["date"])

    # -- sync ----------------------------------------------------------------
    done = skipped = failed = 0
    for nid in order:
        r = rows[nid]
        if r["mirrored"] in ("done", "exists", "skip"):
            continue
        try:
            md = mcp.call("read_node", {"nodeId": nid, "maxDepth": 6})
            title, transcript, summary = parse(md, t_label, s_label)
            title = title or r["title"]
            if not transcript:
                if len(title) > 120:
                    # the node name IS the spoken content (e.g. questionnaire answers)
                    transcript = [title]
                    title = title[:70].rsplit(" ", 1)[0] + "…"
                else:
                    failed += 1
                    r["mirrored"] = "failed"
                    print(f"  ! {nid}: no transcript ({title[:50]})", file=sys.stderr)
                    continue

            title = derive_title(title, transcript)
            slug_src = re.sub(r"\s*\(.*?\)\s*$", "", title).strip() or title
            outdir = note_dir(archive, layout, r["date"])
            path = outdir / fname_pattern.format(date=r["date"], slug=slugify(slug_src))
            twin = id_index.get(nid)
            if twin is None and path.exists():
                twin = path
            if twin is not None:
                skipped += 1
                r["mirrored"] = "exists"
                if twin.name != path.name:
                    print(f"  = {nid}: already archived as {twin.name} "
                          f"(would have been {path.name})")
                continue

            source = f"Tana — {workspace_name}" + (f" ({workspace_id})" if workspace_id else "")
            fm = [
                "---",
                'title: "%s"' % title.replace('"', "'"),
                f"date: {r['date']}",
                "type: voice-note",
                "tags: [%s]" % ", ".join(derive_tags(title, keywords)),
                "areas: []",
                "projects: []",
                "topics: []",
                "processed: []",
                "outputs: []",
                f"tana_id: {nid}",
                f'source: "{source}"',
                "---", "",
                f"# {title}", "",
                f"> Voice note recorded {r['date']}. Mirrored from Tana node `{nid}`.", "",
                "## Transcript", "",
            ]
            body = "\n\n".join(transcript)
            tail = ""
            if summary:
                tail = "\n\n## Summary\n\n" + "\n".join(
                    ("- " + s) if not s.startswith("-") else s for s in summary)
            text = "\n".join(fm) + "\n" + body + tail + "\n"
            if not a.dry_run:
                outdir.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            done += 1
            r["mirrored"] = "done"
            print(f"  ✓ {path.relative_to(archive)}")
            if a.limit and done >= a.limit:
                break
        except Exception as e:
            failed += 1
            r["mirrored"] = "failed"
            print(f"  ✗ {nid}: {e}", file=sys.stderr)

    if not a.dry_run:
        write_manifest(manifest_path, rows, order)
    print(f"\nwritten={done} skipped_existing={skipped} failed={failed}"
          + (" (dry run — nothing written)" if a.dry_run else ""))


if __name__ == "__main__":
    main()
