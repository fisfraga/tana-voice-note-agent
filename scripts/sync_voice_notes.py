#!/usr/bin/env python3
"""
Tana Voice Note Agent — sync script (v3).

Mirrors #voice-note-tagged nodes from Tana's local MCP server into a folder of
markdown files with YAML frontmatter. Pure stdlib; PyYAML is used only if present.

Configuration lives in vn-config.yaml at the repo root (see that file for docs).
The bearer token is NEVER stored in this repo: it is read from the harness MCP
config (~/.claude.json -> mcpServers.<name>.headers.Authorization) or from the
TANA_MCP_TOKEN environment variable.

Usage:
  python3 scripts/sync_voice_notes.py --setup            # first-time: pick workspace + tag
  python3 scripts/sync_voice_notes.py                    # sync notes created in the last 30 days
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
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "vn-config.yaml"
URL_DEFAULT = "http://127.0.0.1:8262/mcp"
MANIFEST_HEADER = [
    "# Voice Note Agent sync manifest — maintained by scripts/sync_voice_notes.py",
    "# mirrored: done (synced) | exists (file already on disk, untouched) | failed | skip (hand-set: never sync)",
    "date\tnode_id\tmirrored\ttitle",
]


# ---------------------------------------------------------------- config ----

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
    root, stack = {}, [(-1, {})]
    stack[0] = (-1, root)
    for raw in text.split("\n"):
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
            parent[key] = val.strip().strip("'\"")
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
        with urllib.request.urlopen(req, timeout=90) as r:
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


# ------------------------------------------------------------------ setup ---

def run_setup(mcp, cfg):
    print("Workspaces loaded in Tana:")
    workspaces = mcp.call_json("list_workspaces", {})
    for i, ws in enumerate(workspaces):
        print(f"  [{i}] {ws.get('name')}  ({ws.get('id')})")
    idx = input("Which workspace holds your voice notes? [number]: ").strip()
    ws = workspaces[int(idx)]
    print(f"\nTags in {ws['name']} (looking for your voice note supertag):")
    tags = mcp.call_json("list_tags", {"workspaceId": ws["id"], "limit": 200})
    candidates = [t for t in tags if "voice" in (t.get("name") or "").lower()] or tags
    for i, t in enumerate(candidates):
        print(f"  [{i}] #{t.get('name')}  ({t.get('id')})")
    idx = input("Which tag marks a voice note? [number]: ").strip()
    tag = candidates[int(idx)]
    save_config_values(CONFIG_PATH, {
        "tana.workspace_id": ws["id"],
        "tana.workspace_name": ws["name"],
        "tana.voice_note_tag_id": tag["id"],
    })
    print(f"\nSaved to {CONFIG_PATH.name}: workspace '{ws['name']}', tag #{tag.get('name')}.")
    print("Run the script again (optionally with --dry-run) to sync.")


# ------------------------------------------------------------------- main ---

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
    a = ap.parse_args()

    cfg = load_config(CONFIG_PATH)
    mcp = MCP(*load_endpoint(cfg))
    mcp.init()

    if a.setup:
        run_setup(mcp, cfg)
        return

    tag_id = cfg_get(cfg, "tana.voice_note_tag_id")
    if not tag_id:
        sys.exit("vn-config.yaml has no tana.voice_note_tag_id — run with --setup first.")
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

    # -- discover ------------------------------------------------------------
    query = {"and": [{"hasType": tag_id}]}
    if not a.all:
        query["and"].append({"created": {"last": a.since}})
    args = {"query": query, "limit": 1000}
    if workspace_id:
        args["workspaceIds"] = [workspace_id]
    found = mcp.call_json("search_nodes", args)
    if isinstance(found, dict):      # some servers wrap the array
        found = found.get("nodes") or found.get("results") or []
    print(f"found {len(found)} tagged notes" + ("" if a.all else f" in the last {a.since} days"))

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

            slug_src = re.sub(r"\s*\(.*?\)\s*$", "", title).strip() or title
            outdir = note_dir(archive, layout, r["date"])
            path = outdir / fname_pattern.format(date=r["date"], slug=slugify(slug_src))
            if path.exists():
                skipped += 1
                r["mirrored"] = "exists"
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
