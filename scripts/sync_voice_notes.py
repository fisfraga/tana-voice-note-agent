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
Override the path with the VN_CONFIG environment variable (handy for a demo or
a scratch archive). The bearer token is NEVER stored in this repo: it is read
from the harness MCP config (~/.claude.json -> mcpServers.<name>.headers.Authorization)
or from the TANA_MCP_TOKEN environment variable.

Usage:
  python3 scripts/sync_voice_notes.py --setup            # first-time: pick workspace + what to sync
  python3 scripts/sync_voice_notes.py                    # sync memos created in the last 30 days
  python3 scripts/sync_voice_notes.py --source tagged --tag <id>   # only one supertag
  python3 scripts/sync_voice_notes.py --tag <id> --tag <id2>       # several supertags
  python3 scripts/sync_voice_notes.py --source both      # memos + tagged nodes
  python3 scripts/sync_voice_notes.py --since 90         # widen the window
  python3 scripts/sync_voice_notes.py --history          # full history sweep (paged, resumable; --all is an alias)
  python3 scripts/sync_voice_notes.py --history --yes --batch 300   # sweep 300 notes per run, no prompt
  python3 scripts/sync_voice_notes.py --refresh-categories --since 60  # re-read Super Folder fields into frontmatter
  python3 scripts/sync_voice_notes.py --dry-run          # show what would be written
  python3 scripts/sync_voice_notes.py --limit 5          # stop after N new files

History mode (--history) walks the workspace backwards in date windows because
Tana's search returns at most 1000 nodes per call. It prints a pre-flight
(counts, tag breakdown, cost) and asks before fetching; in a non-interactive
shell it stops after the pre-flight — re-run with --yes. Progress is saved to
the manifest every few notes, so an interrupted sweep resumes where it stopped.
Enrichment (transcript cleanup, summaries) is agent-side and is NOT part of a
sweep — run it afterwards in batches.

Idempotency (three layers, safe to re-run any time):
  1. manifest rows marked done/exists/skip/empty are never fetched again
  2. an existing file on disk is never overwritten (row becomes "exists")
  3. the manifest (<archive>/sync-manifest.tsv) is rewritten atomically
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
CONFIG_PATH = Path(os.environ["VN_CONFIG"]) if os.environ.get("VN_CONFIG") else REPO / "vn-config.yaml"
EXAMPLE_PATH = REPO / "vn-config.example.yaml"
URL_DEFAULT = "http://127.0.0.1:8262/mcp"
SEARCH_CAP = 1000                     # Tana's search_nodes hard limit per call
MANIFEST_HEADER = [
    "# Voice Note Agent sync manifest — maintained by scripts/sync_voice_notes.py",
    "# mirrored: done (synced) | exists (file already on disk, untouched) | failed (retried next run) | "
    "empty (no transcript at fetch — history mode; --retry-empty re-tries) | skip (hand-set: never sync)",
    "date\tnode_id\tmirrored\ttitle\tsynced_at",
]
DEFAULT_CATEGORY_FIELDS = {"areas": "Area(s)", "projects": "Project(s)", "topics": "Topic(s)"}
CORE_CATEGORY_KEYS = ("areas", "projects", "topics")
FLUSH_EVERY = 25                      # fetches between manifest saves


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
    scalars, inline [] lists, inline {} maps, quoted strings, # comments)."""
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

    def scalar_value(scalar):
        if scalar[:1] not in "'\"":
            low = scalar.lower()
            if low in ("true", "false"):      # keep booleans boolean: the
                return low == "true"          # string 'false' is truthy
            if low in ("null", "~", ""):
                return None
            if re.fullmatch(r"-?\d+", low):
                return int(low)
        return scalar.strip("'\"")

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
        elif val.startswith("{") and val.endswith("}"):
            inner = {}
            for item in val[1:-1].split(","):
                k, _, v = item.partition(":")
                if k.strip():
                    inner[k.strip().strip("'\"")] = scalar_value(v.strip())
            parent[key] = inner
        elif val.startswith("[") and val.endswith("]"):
            parent[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            parent[key] = scalar_value(val.strip())
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

    def _post(self, body, _retry=True):
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", self.auth)
        if self.sid:
            req.add_header("Mcp-Session-Id", self.sid)
        try:
            r = urllib.request.urlopen(req, timeout=90)
        except urllib.error.HTTPError as e:
            # A long sweep outlives the MCP session: re-initialise once and retry.
            if _retry and body.get("method") == "tools/call":
                self.sid = None
                self.init()
                return self._post(body, _retry=False)
            raise RuntimeError(f"HTTP {e.code} from Tana MCP: {e.reason}")
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
        if isinstance(r, dict) and r.get("error"):
            err = r["error"]
            raise RuntimeError(err.get("message") if isinstance(err, dict) else str(err))
        content = (r or {}).get("result", {}).get("content", [])
        return "\n".join(x.get("text", "") for x in content if x.get("type") == "text")

    def call_json(self, tool, args):
        text = self.call(tool, args)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []


def search(mcp, query, workspace_id, limit=SEARCH_CAP):
    """One search_nodes call, unwrapped to a plain list."""
    args = {"query": query, "limit": limit}
    if workspace_id:
        args["workspaceIds"] = [workspace_id]
    r = mcp.call_json("search_nodes", args)
    if isinstance(r, dict):          # some servers wrap the array
        r = r.get("nodes") or r.get("results") or []
    return r or []


# --------------------------------------------------------------- parsing ----

NODEID_RE = re.compile(r"\s*<!--\s*node-id:[^>]*-->")
TIMESTAMP_RE = re.compile(
    r"\s*[-–]\s*(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\w{3}\s+\d{1,2},?(?:\s+\d{4},?)?|Today|Yesterday),?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*$", re.I)
PREFIX_RE = re.compile(r"^\s*\[[ xX]\]\s*")                  # Tana checkbox / status prefix
MEDIA_RE = re.compile(r"^!\[([^\]]*)\]\([^)]*\)\s*$")        # node named by media embed -> alt text
TAGSUFFIX_RE = re.compile(r"\s*#[\w_-]+(\s*,\s*#[\w_-]+)*\s*$")
CAPTURE_RE = re.compile(r"^(voice\s+memo|audio)\s+captured\b", re.I)   # Tana's generic capture label
CALENDAR_RE = re.compile(                                    # a Day/Week node, never a note title
    r"^(today|yesterday|tomorrow|week\s+\d+|\d{4}$|"
    r"(mon|tues|wednes|thurs|fri|satur|sun)day\b|"
    r"(mon|tue|wed|thu|fri|sat|sun),)", re.I)
MEDIA_NAME_RE = re.compile(r"^(audio/|video/|image/|\d+\.(m4a|mp3|wav)\b)", re.I)
FIELD_RE = re.compile(r"^(\s*)-?\s*\*\*([^*]+)\*\*:\s*(.*)$")   # a Tana field line
REF_RE = re.compile(r"\[([^\]]*?)\]\(tana:([A-Za-z0-9_-]+)\)")   # [Name #tag](tana:id)
REF_TAG_RE = re.compile(r"^(.*?)\s+#(\S.*)$")                  # "Name #tag" -> name, tag
NUMBERING_RE = re.compile(r"^\d+[.)]\s*")                      # "4. Home & Family" -> "Home & Family"


def clean(line):
    return NODEID_RE.sub("", line).rstrip()


def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80] or "untitled"


def norm_label(label):
    """Loose field-label key: 'Area(s)', 'Areas', 'Area', 'area' all -> 'area'."""
    s = (label or "").lower().replace("(s)", "").strip()
    if s.endswith("s") and len(s) > 1:
        s = s[:-1]
    return s


def parse_refs(text):
    """Every [Name #tag](tana:id) in a line -> [(display, node_id, tag)]."""
    out = []
    for name, nid in REF_RE.findall(text):
        m = REF_TAG_RE.match(name.strip())
        if m:
            out.append((m.group(1).strip(), nid, m.group(2).strip()))
        else:
            out.append((name.strip(), nid, None))
    return out


def parse(md, transcript_label, summary_label):
    """Split Tana read_node markdown into (title, transcript_lines, summary_lines, fields).

    fields maps a normalised field label (see norm_label) to the values found
    under it: a list of (display_name, tana_node_id_or_None, value_tag_or_None).
    Reference values keep their node id; plain-text values carry None.
    """
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

    transcript, summary, fields, mode = [], [], {}, None
    field_label, field_indent = None, -1
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
        fm = FIELD_RE.match(c)
        if fm and transcript_label.lower() not in low:
            # some other field (Area, Output Language, ...): capture its values
            field_label = norm_label(fm.group(2))
            field_indent = len(fm.group(1))
            mode = "f"
            fields.setdefault(field_label, [])
            rest = fm.group(3).strip()
            refs = parse_refs(rest)
            if refs:
                fields[field_label].extend(refs)
            elif rest and not re.fullmatch(r"\[[ xX]\]", rest):
                fields[field_label].append((rest, None, None))
            continue
        indent = len(c) - len(c.lstrip())
        body = c.strip()
        body = body[2:] if body.startswith("- ") else body
        if mode == "f":
            if indent > field_indent:
                refs = parse_refs(body)
                if refs:
                    fields[field_label].extend(refs)
                elif body:
                    fields[field_label].append((body, None, None))
                continue
            mode = None                    # back at the field's level: the field ended
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
    return title, transcript, summary, fields


def category_fields(cfg):
    """Frontmatter key -> normalised Tana field label, from tana.category_fields
    (falling back to the older tana.field_labels.area/project/topic)."""
    m = cfg_get(cfg, "tana.category_fields", {}) or {}
    if not isinstance(m, dict) or not m:
        m = {
            "areas": cfg_get(cfg, "tana.field_labels.area", DEFAULT_CATEGORY_FIELDS["areas"]),
            "projects": cfg_get(cfg, "tana.field_labels.project", DEFAULT_CATEGORY_FIELDS["projects"]),
            "topics": cfg_get(cfg, "tana.field_labels.topic", DEFAULT_CATEGORY_FIELDS["topics"]),
        }
    out = {}
    for k in CORE_CATEGORY_KEYS:            # core keys always exist, in canonical order
        out[k] = norm_label(m.get(k, DEFAULT_CATEGORY_FIELDS[k]))
    for k, v in m.items():
        if k not in out:
            out[k] = norm_label(v)
    return out


def kebab_value(display):
    return slugify(NUMBERING_RE.sub("", (display or "").strip()))


def categories_from_fields(fields, mapping):
    """-> (values {fm_key: [kebab, ...]}, refs {"fm_key/kebab": node_id})."""
    values, refs = {}, {}
    for fm_key, label in mapping.items():
        vals = []
        for display, nid, _tag in fields.get(label, []):
            k = kebab_value(display)
            if k == "untitled":
                continue
            if k not in vals:
                vals.append(k)
            if nid:
                refs[f"{fm_key}/{k}"] = nid
        values[fm_key] = vals
    return values, refs


def parent_title(breadcrumb):
    """The note a voice memo hangs under, from the search result's breadcrumb.

    `has: audio` matches the memo node itself — in Tana that is usually a child
    named 'Voice memo captured ...' sitting under the node that carries the real
    title. The breadcrumb's last entry IS that node's name, so it gives us the
    human title without a parent lookup (the API has no upward query).
    Returns None when the parent is a Day/Week node or another media node.
    """
    if not breadcrumb:
        return None
    name = TIMESTAMP_RE.sub("", str(breadcrumb[-1] or "")).strip()
    if not name or len(name) < 3:
        return None
    if CALENDAR_RE.match(name) or CAPTURE_RE.match(name) or MEDIA_NAME_RE.match(name):
        return None
    return name


def derive_title(title, transcript, breadcrumb=None):
    """Tana names an untagged capture 'Voice memo captured Mon, Feb 9, 12:17' —
    the same label on every recording, which would make every filename and index
    row look alike. Prefer the parent note's title; fall back to the words
    actually spoken."""
    if title and not CAPTURE_RE.match(title.strip()):
        return title
    parent = parent_title(breadcrumb)
    if parent:
        return parent
    if not transcript:
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


def tag_names(hit):
    """Supertag names on a search hit, slugified (['voice-note'] / [])."""
    out = []
    for t in hit.get("tags") or []:
        name = t.get("name") if isinstance(t, dict) else t
        s = slugify(str(name or "").strip())
        if s and s != "untitled" and s not in out:
            out.append(s)
    return out


# ------------------------------------------------------------ frontmatter ---

def yaml_list(values):
    return "[%s]" % ", ".join(values)


def frontmatter_lines(title, date, tags, cats, tana_id, tana_tags, tana_refs, source):
    """The frontmatter block of a note (list of lines, including the --- fences).
    cats is an ordered {fm_key: [values]} — areas/projects/topics first, then
    any extra keys declared in tana.category_fields."""
    fm = [
        "---",
        'title: "%s"' % title.replace('"', "'"),
        f"date: {date}",
        "type: voice-note",
        "tags: " + yaml_list(tags),
    ]
    for key in CORE_CATEGORY_KEYS:
        fm.append(f"{key}: " + yaml_list(cats.get(key, [])))
    for key, vals in cats.items():
        if key not in CORE_CATEGORY_KEYS:
            fm.append(f"{key}: " + yaml_list(vals))
    fm += [
        "processed: []",
        "outputs: []",
        f"tana_id: {tana_id}",
        "tana_tags: " + yaml_list(tana_tags),
    ]
    if tana_refs:
        fm.append("tana_refs:")
        for k, v in tana_refs.items():
            fm.append(f"  {k}: {v}")
    fm += [f'source: "{source}"', "---"]
    return fm


def build_note(title, date, tags, cats, tana_id, tana_tags, tana_refs, source, transcript, summary):
    fm = frontmatter_lines(title, date, tags, cats, tana_id, tana_tags, tana_refs, source)
    fm += ["", f"# {title}", "",
           f"> Voice note recorded {date}. Mirrored from Tana node `{tana_id}`.", "",
           "## Transcript", ""]
    body = "\n\n".join(transcript)
    tail = ""
    if summary:
        tail = "\n\n## Summary\n\n" + "\n".join(
            ("- " + s) if not s.startswith("-") else s for s in summary)
    return "\n".join(fm) + "\n" + body + tail + "\n"


def split_frontmatter(text):
    """-> (fm_lines, body_text) or (None, text) when there is no frontmatter."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm = text[:end].split("\n")[1:]
    body = text[end + len("\n---"):]
    return fm, body


def read_fm_value(fm_lines, key):
    """Value of a frontmatter key: inline list -> list, block list -> list,
    block map -> dict, scalar -> str, missing -> None. Also returns the line span."""
    for i, line in enumerate(fm_lines):
        if not line.startswith(f"{key}:"):
            continue
        rest = line[len(key) + 1:].strip()
        j = i + 1
        while j < len(fm_lines) and (fm_lines[j].startswith("  ") or fm_lines[j].startswith("\t")):
            j += 1
        block = [l.strip() for l in fm_lines[i + 1:j] if l.strip()]
        if rest.startswith("[") and rest.endswith("]"):
            return [v.strip().strip("'\"") for v in rest[1:-1].split(",") if v.strip()], (i, j)
        if rest == "{}":
            return {}, (i, j)
        if rest == "" and block and all(l.startswith("- ") for l in block):
            return [l[2:].strip().strip("'\"") for l in block], (i, j)
        if rest == "" and block:
            d = {}
            for l in block:
                k, _, v = l.partition(":")
                d[k.strip().strip("'\"")] = v.strip().strip("'\"")
            return d, (i, j)
        if rest == "":
            return [], (i, j)
        return rest.strip("'\""), (i, j)
    return None, None


def render_fm_value(key, value):
    if isinstance(value, dict):
        if not value:
            return []
        return [f"{key}:"] + [f"  {k}: {v}" for k, v in value.items()]
    if isinstance(value, list):
        return [f"{key}: " + yaml_list(value)]
    return [f"{key}: {value}"]


def edit_frontmatter(text, updates):
    """Replace/insert frontmatter keys; the body is returned byte-identical.
    updates: {key: list | dict | str}. An empty dict removes the key."""
    fm, body = split_frontmatter(text)
    if fm is None:
        return text
    for key, value in updates.items():
        _, span = read_fm_value(fm, key)
        new_lines = render_fm_value(key, value)
        if span:
            fm[span[0]:span[1]] = new_lines
        elif new_lines:
            # insert before `source:` (the conventional last key), else at the end
            idx = next((i for i, l in enumerate(fm) if l.startswith("source:")), len(fm))
            fm[idx:idx] = new_lines
    return "---\n" + "\n".join(fm) + "\n---" + body


def merge_categories(text, cats, refs, tana_tags):
    """Union-merge Tana categories into an archived note's frontmatter.
    Returns (new_text, changes) where changes lists '+areas: x' style entries."""
    fm, _ = split_frontmatter(text)
    if fm is None:
        return text, []
    updates, changes = {}, []
    for key, vals in cats.items():
        cur, _ = read_fm_value(fm, key)
        cur = list(cur) if isinstance(cur, list) else []
        added = [v for v in vals if v not in cur]
        if added:
            updates[key] = cur + added
            changes.append(f"+{key}: {', '.join(added)}")
    cur_refs, _ = read_fm_value(fm, "tana_refs")
    cur_refs = dict(cur_refs) if isinstance(cur_refs, dict) else {}
    new_refs = dict(cur_refs)
    new_refs.update({k: v for k, v in refs.items() if cur_refs.get(k) != v})
    if new_refs != cur_refs:
        updates["tana_refs"] = new_refs
        changes.append("tana_refs")
    cur_tags, _ = read_fm_value(fm, "tana_tags")
    if cur_tags is None or list(cur_tags) != list(tana_tags):
        updates["tana_tags"] = list(tana_tags)
        changes.append("tana_tags: " + yaml_list(tana_tags))
    if not updates:
        return text, []
    return edit_frontmatter(text, updates), changes


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
        rows[p[1]] = {"date": p[0], "node_id": p[1], "mirrored": p[2], "title": p[3],
                      "synced_at": p[4] if len(p) > 4 else ""}
        order.append(p[1])
    return rows, order


def write_manifest(path, rows, order):
    lines = list(MANIFEST_HEADER)
    for nid in order:
        r = rows[nid]
        lines.append("\t".join([r["date"], r["node_id"], r["mirrored"], r["title"],
                                r.get("synced_at", "") or ""]))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n")
    os.replace(tmp, path)


# ------------------------------------------------------------------ query ---

SOURCE_MODES = ("all_audio", "tagged", "both")


def build_clause(source, tag_ids):
    """The 'what is a voice note' clause for a source mode.

    all_audio (default) is Tana's `has: audio` — every node with a recording
    attached, tagged or not. That is what a voice memo IS; a supertag is one
    way some people mark them, not a requirement of the format.
    """
    tag_ids = [t for t in (tag_ids or []) if t]
    typed = [{"hasType": t} for t in tag_ids]
    if source == "tagged":
        return typed[0] if len(typed) == 1 else {"or": typed}
    if source == "both":
        return {"or": [{"has": "audio"}] + typed}
    return {"has": "audio"}


def build_query(source, tag_ids=None, since=None, older_than=None):
    """search_nodes query. `source` is a mode name or a prebuilt clause dict.
    since = created in the last N days; older_than = NOT created in the last N
    days. Both together select a date window (Tana has no cursor: this is how
    a workspace deeper than 1000 hits gets paged)."""
    if isinstance(source, dict):
        clause = source
    else:
        if isinstance(tag_ids, str):
            tag_ids = [tag_ids]
        clause = build_clause(source, tag_ids)
    query = {"and": [clause]}
    if since is not None:
        query["and"].append({"created": {"last": since}})
    if older_than is not None and older_than > 0:
        query["and"].append({"not": {"created": {"last": older_than}}})
    return query


def walk_windows(search_fn, clause, window=90, cap=SEARCH_CAP):
    """Walk the whole history backwards in date windows.

    Yields (lo_days, hi_days_or_None, hits, saturated). Before each window a
    probe asks for everything older than `lo`; when that fits under the cap it
    IS the tail and the walk ends. A window that hits the cap is halved down to
    one day; a saturated one-day window is yielded with saturated=True.
    """
    lo = 0
    while True:
        rest = search_fn(build_query(clause, older_than=lo))
        if len(rest) < cap:
            yield lo, None, rest, False
            return
        hi = lo + window
        chunk = search_fn(build_query(clause, since=hi, older_than=lo))
        while len(chunk) >= cap and window > 1:
            window = max(1, window // 2)
            hi = lo + window
            chunk = search_fn(build_query(clause, since=hi, older_than=lo))
        yield lo, hi, chunk, len(chunk) >= cap
        lo = hi


def resolve_source(cfg, cli_source, cli_tags):
    """Settle the source mode from CLI flags over config, and fail loudly only
    when a tag-based mode was asked for without a tag. Returns (source, tag_ids)."""
    source = cli_source or cfg_get(cfg, "tana.source", "all_audio") or "all_audio"
    if source not in SOURCE_MODES:
        sys.exit(f"unknown source '{source}' — choose one of: {', '.join(SOURCE_MODES)}")
    if isinstance(cli_tags, str):
        cli_tags = [cli_tags]
    cli_tags = [t for t in (cli_tags or []) if t]
    extra = cfg_get(cfg, "tana.extra_tag_ids", []) or []
    if isinstance(extra, str):
        extra = [extra]
    tag_ids = []
    for t in [cfg_get(cfg, "tana.voice_note_tag_id")] + list(extra) + cli_tags:
        if t and t not in tag_ids:
            tag_ids.append(t)
    if cli_tags and not cli_source:
        source = "tagged"                     # --tag alone means "only those tags"
    if source in ("tagged", "both") and not tag_ids:
        sys.exit(
            f"source '{source}' needs a supertag, but tana.voice_note_tag_id is empty.\n"
            "  - run with --setup to pick one, or\n"
            "  - pass --tag <tagId> (repeatable), or\n"
            "  - use the default --source all_audio to sync every voice memo."
        )
    return source, tag_ids


def describe_source(source, tag_name=""):
    if source == "tagged":
        return f"notes tagged {tag_name or 'your voice-note supertag(s)'}"
    if source == "both":
        return f"voice memos (audio) and notes tagged {tag_name or 'your voice-note supertag(s)'}"
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
            n = len(search(mcp, query, ws["id"]))
            return f"{SEARCH_CAP}+" if n >= SEARCH_CAP else str(n)
        except Exception:
            return "?"

    # -- what counts as a voice note ----------------------------------------
    n_audio = count({"and": [{"has": "audio"}]})
    print(f"\n{ws['name']} holds {n_audio} voice memo(s) — nodes with a recording attached."
          + (" Run --history for the exact count." if n_audio.endswith("+") else ""))
    print("\nWhat should sync pull in?")
    print("  [1] every voice memo                                   (default)")
    print("  [2] only memos carrying a specific supertag")
    print("  [3] both — every voice memo plus everything with that supertag")
    print("      (recommended with the Voice Note Agent template: your Area/Project/Topic")
    print("       fields live on the tagged note, and [3] brings them into the archive)")
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
        print("Note: Super Folder fields (Area/Project/Topic) sit on the tagged note, not on "
              "the audio memo — choose [3] both if you want them in the archive.")
    if tag:
        print("Older notes under other supertags? Add their ids to tana.extra_tag_ids in "
              f"{CONFIG_PATH.name} (inline list), then run --history.")
    print("Run the script again (optionally with --dry-run) to sync.")


# ------------------------------------------------------------------- main ---

TANA_ID_RE = re.compile(r"^tana_id:\s*[\"']?([A-Za-z0-9_-]+)", re.M)
DATE_RE = re.compile(r"^date:\s*[\"']?(\d{4}-\d{2}-\d{2})", re.M)


PLACEHOLDER_RE = re.compile(
    r"transcript content was not available|transcript field was empty", re.I)


def fingerprint(text):
    """A stable key for 'this is the same recording', independent of node id.

    Needed because one recording can be reachable as two nodes: the memo child
    that `has: audio` matches, and the parent that carries the supertag. They
    have different tana_ids, so an id index alone lets the same words be written
    twice. Normalised opening words of the transcript are the same either way.
    """
    words = re.sub(r"[^\w\s]", " ", (text or "").lower())
    words = " ".join(words.split())
    # Placeholders are identical across unrelated notes — six notes in one real
    # archive share the "transcript not available" stub. Fingerprinting those
    # would make every future stub look like a duplicate of the first.
    if PLACEHOLDER_RE.search(words) or len(words) < 80:
        return None
    return words[:300]


def transcript_of(md):
    """The transcript body of an archived note file."""
    m = re.search(r"^## Transcript\s*$(.*?)(?=^## |\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def index_by_tana_id(archive):
    """Map every tana_id already in the archive to its file.

    Dedupe cannot rely on the filename alone: a note retitled in Tana slugs
    differently, and archives predating this script may use another slugging
    convention entirely (accents kept, say). tana_id is the stable identity,
    and it is in every note's frontmatter.
    """
    index, prints = {}, {}
    for f in archive.rglob("*.md"):
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        m = TANA_ID_RE.search(text[:4000])
        if m:
            index.setdefault(m.group(1), f)
        fp = fingerprint(transcript_of(text))
        if fp:
            prints.setdefault(fp, f)
    return index, prints


def note_dir(archive, layout, date):
    if layout == "by-month":
        return archive / date[:4] / date[5:7]
    if layout == "flat":
        return archive
    return archive / date[:4]     # by-year (default)


def hit_date(hit):
    created = hit.get("created")
    if isinstance(created, (int, float)):
        return dt.datetime.fromtimestamp(created / 1000).strftime("%Y-%m-%d")
    return str(created or "")[:10] or dt.date.today().isoformat()


def add_hits(rows, order, hits):
    """Register search hits as manifest rows. Returns the number of new rows.
    Rows already settled (done/exists/skip/empty) are left alone; unsettled ones
    get their breadcrumb/tags refreshed so a resumed run still has them."""
    new = 0
    for n in hits:
        nid = n.get("id")
        if not nid:
            continue
        if nid in rows:
            if rows[nid]["mirrored"] in ("pending", "failed"):
                rows[nid]["breadcrumb"] = n.get("breadcrumb") or []
                rows[nid]["tags"] = tag_names(n)
            continue
        rows[nid] = {"date": hit_date(n), "node_id": nid, "mirrored": "pending",
                     "title": (n.get("name") or "").replace("\t", " ")[:160],
                     "breadcrumb": n.get("breadcrumb") or [], "tags": tag_names(n),
                     "synced_at": ""}
        order.append(nid)
        new += 1
    return new


def sort_order(order, rows):
    # tagged parents before their untagged audio children within a day, so the
    # fingerprint dedupe keeps the version that carries the Super Folder fields
    order.sort(key=lambda nid: (rows[nid]["date"], 0 if rows[nid].get("tags") else 1))


def preflight(rows, order, todo_states, windows, batch):
    todo = [nid for nid in order if rows[nid]["mirrored"] in todo_states]
    settled = len(order) - len(todo)
    breakdown = {}
    for nid in todo:
        tags = rows[nid].get("tags") or []
        key = "#" + tags[0].replace("-", " ") if tags else "untagged audio"
        breakdown[key] = breakdown.get(key, 0) + 1
    parts = " · ".join(f"{k} {v:,}" for k, v in sorted(breakdown.items(), key=lambda kv: -kv[1]))
    minutes = max(1, len(todo) // 100), max(2, len(todo) // 50)
    print(f"\nhistory: {len(order):,} nodes found across {windows} window(s) · "
          f"{len(todo):,} to fetch · {settled:,} already in manifest")
    if parts:
        print(f"tags: {parts}")
    print(f"cost: ~{len(todo):,} read_node calls (≈{minutes[0]}–{minutes[1]} min"
          + (f", {batch} per run with --batch" if batch else "") + ").")
    print("      Enrichment is NOT run in history mode — run /vn-sync enrich in batches\n"
          "      afterwards (one AI pass per note).")
    return todo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", action="store_true", help="interactive first-time configuration")
    ap.add_argument("--since", type=int, default=30, help="only consider notes created in the last N days (default 30)")
    ap.add_argument("--history", "--all", dest="history", action="store_true",
                    help="full history sweep: page the whole workspace in date windows, resumable (--all is an alias)")
    ap.add_argument("--window", type=int, default=None, metavar="DAYS",
                    help="history: initial window in days (default tana.history.window_days or 90; halves when a window hits the 1000 cap)")
    ap.add_argument("--batch", type=int, default=None, metavar="N",
                    help="history/refresh: stop after N node fetches (manifest saved; re-run to continue)")
    ap.add_argument("--yes", action="store_true", help="history: skip the confirmation gate")
    ap.add_argument("--retry-empty", action="store_true", help="re-fetch nodes marked empty (no transcript last time)")
    ap.add_argument("--refresh-categories", action="store_true",
                    help="re-read Super Folder fields of already-archived notes into their frontmatter (frontmatter-only edits)")
    ap.add_argument("--limit", type=int, default=0, help="stop after writing N files")
    ap.add_argument("--dry-run", action="store_true", help="report, but write nothing")
    ap.add_argument("--source", choices=SOURCE_MODES, default=None,
                    help="what counts as a voice note: all_audio (default — every node with "
                         "a recording attached), tagged (only voice_note_tag_id + extra_tag_ids), or both")
    ap.add_argument("--tag", action="append", default=None, metavar="TAG_ID",
                    help="sync only nodes with this supertag id (repeatable; implies --source tagged)")
    a = ap.parse_args()

    bootstrap_config()
    cfg = load_config(CONFIG_PATH)
    mcp = MCP(*load_endpoint(cfg))
    mcp.init()

    if a.setup:
        run_setup(mcp, cfg)
        return

    source_mode, tag_ids = resolve_source(cfg, a.source, a.tag)
    workspace_id = cfg_get(cfg, "tana.workspace_id")
    workspace_name = cfg_get(cfg, "tana.workspace_name", "Tana")
    t_label = cfg_get(cfg, "tana.field_labels.transcript", "Transcript")
    s_label = cfg_get(cfg, "tana.field_labels.summary", "Transcript Summary (AI)")
    keywords = cfg_get(cfg, "catalog.tag_keywords", {}) or {}
    cat_map = category_fields(cfg)
    window = a.window or int(cfg_get(cfg, "tana.history.window_days", 90) or 90)
    batch = a.batch if a.batch is not None else int(cfg_get(cfg, "tana.history.batch", 0) or 0)

    archive_cfg = cfg_get(cfg, "archive.dir", "Voice-Notes")
    archive = Path(archive_cfg) if os.path.isabs(str(archive_cfg)) else REPO / archive_cfg
    layout = cfg_get(cfg, "archive.layout", "by-year")
    fname_pattern = cfg_get(cfg, "archive.filename", "{date}-{slug}.md")
    manifest_path = archive / "sync-manifest.tsv"
    archive.mkdir(parents=True, exist_ok=True)
    id_index, fp_index = index_by_tana_id(archive)
    rows, order = load_manifest(manifest_path)
    today = dt.date.today().isoformat()

    def flush():
        if not a.dry_run and order:
            write_manifest(manifest_path, rows, order)

    # -- refresh categories (frontmatter-only edits of archived notes) -------
    if a.refresh_categories:
        cutoff = None if a.history else (dt.date.today() - dt.timedelta(days=a.since)).isoformat()
        candidates = []
        for nid, path in sorted(id_index.items(), key=lambda kv: kv[1].name, reverse=True):
            date = rows.get(nid, {}).get("date")
            if not date:
                m = DATE_RE.search(path.read_text(errors="replace")[:4000])
                date = m.group(1) if m else ""
            if cutoff and date and date < cutoff:
                continue
            candidates.append((nid, path))
        print(f"refresh-categories: {len(candidates)} archived note(s)"
              + (f" since {cutoff}" if cutoff else " (whole archive)")
              + (" — dry run" if a.dry_run else ""))
        changed = fetched = 0
        for nid, path in candidates:
            if batch and fetched >= batch:
                print(f"  batch limit reached ({batch}); re-run to continue")
                break
            try:
                md = mcp.call("read_node", {"nodeId": nid, "maxDepth": 6})
                fetched += 1
                _, _, _, fields = parse(md, t_label, s_label)
                cats, refs = categories_from_fields(fields, cat_map)
                tags = rows.get(nid, {}).get("tags")
                if tags is None:
                    m = TAGSUFFIX_RE.search(clean(md.split("\n", 1)[0]))
                    tags = [slugify(t.strip("# ")) for t in m.group(0).split(",")] if m else []
                text = path.read_text()
                new_text, changes = merge_categories(text, cats, refs, tags)
                if changes:
                    changed += 1
                    print(f"  ~ {path.relative_to(archive)} ({'; '.join(changes)})")
                    if not a.dry_run:
                        path.write_text(new_text)
            except Exception as e:
                print(f"  ✗ {nid}: {e}", file=sys.stderr)
        print(f"\nrefreshed={changed} checked={fetched}" + (" (dry run — nothing written)" if a.dry_run else ""))
        return

    # -- discover ------------------------------------------------------------
    windows = 0
    if a.history:
        clause = build_clause(source_mode, tag_ids)
        print(f"history: walking {describe_source(source_mode)} in {window}-day windows")
        for lo, hi, hits, saturated in walk_windows(lambda q: search(mcp, q, workspace_id), clause, window):
            windows += 1
            new = add_hits(rows, order, hits)
            label = f"older than {lo}d" if hi is None else f"{lo}–{hi}d ago"
            print(f"  window {label}: {len(hits)} node(s), {new} new"
                  + ("  ! SATURATED: 1000+ nodes in one day — some may be missing" if saturated else ""))
            flush()
    else:
        found = search(mcp, build_query(source_mode, tag_ids, a.since), workspace_id)
        print(f"found {len(found)} {describe_source(source_mode)} in the last {a.since} days")
        if len(found) >= SEARCH_CAP:
            print(f"  ! search returned {SEARCH_CAP} (the server cap) — notes in this window may be "
                  "missing; use --history or a smaller --since", file=sys.stderr)
        add_hits(rows, order, found)
    sort_order(order, rows)

    settled = {"done", "exists", "skip"} | (set() if a.retry_empty else {"empty"})
    todo_states = {"pending", "failed"} | ({"empty"} if a.retry_empty else set())

    # -- pre-flight gate (history only) --------------------------------------
    if a.history:
        todo = preflight(rows, order, todo_states, windows, batch)
        if not todo:
            print("\nnothing to fetch — the archive already holds every node found.")
            return
        if a.dry_run:
            print("\n(dry run — listing what would be written)")
        elif not a.yes:
            if sys.stdin.isatty():
                if input("\nProceed? [y/N] ").strip().lower() not in ("y", "yes"):
                    print("stopped; manifest saved. Re-run when ready.")
                    return
            else:
                print("\nre-run with --yes to proceed (or --dry-run to preview). Manifest saved.")
                return

    # -- sync ----------------------------------------------------------------
    done = skipped = failed = empty = fetched = 0
    todo_total = sum(1 for nid in order if rows[nid]["mirrored"] in todo_states)
    interrupted = False
    try:
        for nid in order:
            r = rows[nid]
            if r["mirrored"] in settled:
                continue
            if batch and fetched >= batch:
                print(f"\n  batch limit reached ({batch}); re-run the same command to continue")
                break
            try:
                md = mcp.call("read_node", {"nodeId": nid, "maxDepth": 6})
                fetched += 1
                if fetched % FLUSH_EVERY == 0:
                    flush()
                prefix = f"[{fetched}/{todo_total}] " if a.history else "  "
                title, transcript, summary, fields = parse(md, t_label, s_label)
                title = title or r["title"]
                if not transcript:
                    if len(title) > 120:
                        # the node name IS the spoken content (e.g. questionnaire answers)
                        transcript = [title]
                        title = title[:70].rsplit(" ", 1)[0] + "…"
                    elif a.history:
                        empty += 1
                        r["mirrored"] = "empty"
                        r["synced_at"] = today
                        print(f"{prefix}- {nid}: no transcript yet ({title[:50]})")
                        continue
                    else:
                        failed += 1
                        r["mirrored"] = "failed"
                        print(f"  ! {nid}: no transcript ({title[:50]})", file=sys.stderr)
                        continue

                title = derive_title(title, transcript, r.get("breadcrumb"))
                slug_src = re.sub(r"\s*\(.*?\)\s*$", "", title).strip() or title
                outdir = note_dir(archive, layout, r["date"])
                path = outdir / fname_pattern.format(date=r["date"], slug=slugify(slug_src))
                twin = id_index.get(nid) or fp_index.get(fingerprint("\n".join(transcript)))
                if twin is None and path.exists():
                    twin = path
                if twin is not None:
                    skipped += 1
                    r["mirrored"] = "exists"
                    r["synced_at"] = today
                    if twin.name != path.name:
                        print(f"{prefix}= {nid}: already archived as {twin.name} "
                              f"(would have been {path.name})")
                    continue

                source = f"Tana — {workspace_name}" + (f" ({workspace_id})" if workspace_id else "")
                cats, refs = categories_from_fields(fields, cat_map)
                text = build_note(title, r["date"], derive_tags(title, keywords), cats, nid,
                                  r.get("tags") or [], refs, source, transcript, summary)
                if not a.dry_run:
                    outdir.mkdir(parents=True, exist_ok=True)
                    path.write_text(text)
                    id_index[nid] = path
                    fp = fingerprint("\n".join(transcript))
                    if fp:
                        fp_index.setdefault(fp, path)
                done += 1
                r["mirrored"] = "done"
                r["synced_at"] = today
                print(f"{prefix}✓ {path.relative_to(archive)}")
                if a.limit and done >= a.limit:
                    break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                failed += 1
                r["mirrored"] = "failed"
                print(f"  ✗ {nid}: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        flush()

    remaining = sum(1 for nid in order if rows[nid]["mirrored"] in todo_states)
    print(f"\nwritten={done} skipped_existing={skipped} empty={empty} failed={failed}"
          + (" (dry run — nothing written)" if a.dry_run else ""))
    if interrupted:
        print("interrupted — manifest saved; resumable: re-run the same command")
        sys.exit(130)
    if a.history and remaining:
        print(f"resume: {remaining} still pending — re-run the same command to continue")


if __name__ == "__main__":
    main()
