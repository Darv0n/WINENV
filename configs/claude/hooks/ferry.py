#!/usr/bin/env python3
"""ferry -- carry a Claude Code session across the compaction boundary.

The transcript (.jsonl) is the session's write-ahead log: every message lands there first.
Compaction rewrites the model's working memory into one summary (2026-11-08: 969,833 tokens ->
27,697). ferry makes what matters cross that boundary intact:

  flush    PreCompact hook. Its plain-text stdout becomes the summarizer's instructions: keep the
           owner's words, open loops, decisions and unsaved knowledge, and end with a canary line
           that names the checkpoint. Records what was sent and the repos' git facts.
  land     SessionStart hook (source "compact"). Rebuilds from the transcript and hands the new
           context: whether the canary survived, the owner's latest words verbatim, project
           instructions loaded before compaction, open loops, repo state. Also tells the owner.
  archive  SessionEnd hook. Keeps the owner's words (scrubbed) and one index line per session,
           so they outlive transcript cleanup (cleanupPeriodDays).
  replay   CLI: python ferry.py replay <transcript.jsonl> [out_dir]   full organized digest.
  now      CLI: python ferry.py now [transcript.jsonl]   manual checkpoint ("save our work").
  selftest CLI: python ferry.py selftest [transcript.jsonl]   proves every hook path; run it after
           each Claude Code update (land says when the version changed since the last pass).

Hooks never block and never fail in the session: every path exits 0; errors go to errors.log.
Store: ~/.claude/ferry (FERRY_STORE overrides).
"""

import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(os.environ.get("FERRY_STORE", Path.home() / ".claude" / "ferry"))
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
CHUNK_BYTES = 240_000
CANARY = "ferry-checkpoint:"
CAP = 9_500  # hook strings are capped at 10,000 characters


# --- small utilities ----------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc)


def _err(where, exc=None):
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        with open(STORE / "errors.log", "a", encoding="utf-8") as f:
            f.write(f"{_now().isoformat()} {where}\n{traceback.format_exc() if exc else ''}\n")
    except Exception:  # noqa: BLE001 - the error log must never raise
        pass


def _cut(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f" [...+{len(s) - n} chars]"


SECRET_PATTERNS = [  # prefixes anchored at a word boundary: "ask-before-..." is prose, not a key
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    re.compile(r"\b[0-9a-f]{32}\b"),
]
SECRET_ASSIGN = re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password|passwd)(\s*[=:]\s*)([^\s'\"<>]{6,})")


def scrub(text):
    """Redact common credential shapes. Checkpoints outlive transcripts, so they carry no keys."""
    text = text or ""
    for p in SECRET_PATTERNS:
        text = p.sub("[redacted]", text)
    return SECRET_ASSIGN.sub(lambda m: m.group(1) + m.group(2) + "[redacted]", text)


# --- reading the log ----------------------------------------------------------------------------

def _when(o):
    ts = o.get("timestamp")
    if not ts:
        return ""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%m-%d %H:%M")
    except ValueError:
        return ts[:16]


def _text(content):
    """Plain text of a message/tool-result content (str or list of blocks); images noted."""
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text":
            out.append(b.get("text", ""))
        elif b.get("type") == "image":
            out.append("[image]")
        elif b.get("type") == "tool_reference":
            out.append(f"[tool {b.get('tool_name', '')}]")
    return "\n".join(out)


def _clean(text):
    return REMINDER.sub("", text or "").strip()


OWNER_TAGS = {"command-name", "command-message", "bash-input"}
TAG = re.compile(r"<([a-z][\w-]*)[\s>]")


def _owner_kind(text):
    """turn | command | interrupt | notification | summary | machinery (agent hand-backs, tool echo)."""
    t = text.lstrip()
    if t.startswith("<task-notification"):
        return "notification"
    m = TAG.match(t)
    if m:  # a message that opens with a tag is machinery unless it is one of the owner's own commands
        return "command" if m.group(1) in OWNER_TAGS else "machinery"
    if t.startswith("Caveat:"):
        return "machinery"
    if t.startswith("[Request interrupted"):
        return "interrupt"
    if t.startswith("This session is being continued from a previous conversation"):
        return "summary"
    return "turn"


def _call_gist(name, inp):
    g = inp.get
    if name in ("Bash", "PowerShell"):
        d = f"  # {g('description')}" if g("description") else ""
        return _cut(g("command", ""), 500) + d
    if name == "Read":
        return f"{g('file_path')}" + (f" @{g('offset')}+{g('limit')}" if g("offset") or g("limit") else "")
    if name == "Write":
        return f"{g('file_path')} ({len((g('content') or '').splitlines())} lines)"
    if name == "Edit":
        return f"{g('file_path')}: {_cut(g('old_string'), 120)!r} => {_cut(g('new_string'), 240)!r}"
    if name in ("Grep", "Glob"):
        return f"{g('pattern')!r} in {g('path') or '.'}"
    if name == "Agent":
        return f"[{g('subagent_type') or 'general'}] {g('description')}: {_cut(g('prompt'), 2500)}"
    if name == "AskUserQuestion":
        return json.dumps(g("questions"), ensure_ascii=False)
    if name == "Artifact":
        return f"{g('action') or 'publish'} {g('file_path') or ''} {g('url') or ''}".strip()
    if name == "SendUserFile":
        return f"{g('files')} {g('caption') or ''}"
    if name == "WebSearch":
        return f"{g('query')!r}"
    if name == "WebFetch":
        return f"{g('url')} :: {_cut(g('prompt'), 200)}"
    if name == "Monitor":
        return f"{g('description')} :: {_cut(g('command'), 300)}"
    return _cut(json.dumps(inp, ensure_ascii=False), 400)


def _records(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


MIDTURN = re.compile(r"The user sent a new message while you were working:\n(.*?)(?:\n\nThis is how Claude Code surfaces|\Z)", re.S)


def read_events(path):
    """Normalized events from a transcript, main thread only, in log order."""
    names = {}
    for o in _records(path):
        if o.get("isSidechain"):
            continue
        t, when = o.get("type"), _when(o)
        if t == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if b.get("type") == "text" and b.get("text", "").strip():
                    yield {"when": when, "kind": "me", "text": b["text"].strip()}
                elif b.get("type") == "tool_use":
                    names[b.get("id")] = b.get("name")
                    yield {"when": when, "kind": "call", "tool": b.get("name"),
                           "gist": _call_gist(b.get("name", ""), b.get("input") or {}), "input": b.get("input") or {}}
        elif t == "user":
            if o.get("isCompactSummary"):
                yield {"when": when, "kind": "summary", "text": _text(o["message"].get("content"))}
                continue
            content = (o.get("message") or {}).get("content")
            blocks = content if isinstance(content, list) else None
            if blocks and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                for b in blocks:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                        continue
                    text = _text(b.get("content"))
                    tool = names.get(b.get("tool_use_id"), "?")
                    denied = "doesn't want to proceed" in text or "user denied" in text.lower()
                    yield {"when": when, "kind": "denial" if denied else "result", "tool": tool,
                           "error": bool(b.get("is_error")), "text": text}
                    for m in MIDTURN.finditer(text):
                        yield {"when": when, "kind": "owner", "how": "mid-turn", "text": m.group(1).strip()}
                continue
            if o.get("isMeta"):
                continue
            raw = _text(content)
            for m in MIDTURN.finditer(raw):  # mid-turn words can ride inside a reminder block
                yield {"when": when, "kind": "owner", "how": "mid-turn", "text": m.group(1).strip()}
            text = _clean(raw)
            if not text:
                continue
            kind = _owner_kind(text)
            if kind == "turn":
                yield {"when": when, "kind": "owner", "how": "turn", "text": text}
            elif kind in ("command", "interrupt"):
                yield {"when": when, "kind": "owner", "how": kind, "text": text}
            elif kind == "notification":
                yield {"when": when, "kind": "notification", "text": text}
            elif kind == "summary":
                yield {"when": when, "kind": "summary", "text": text}
        elif t == "attachment":
            a = o.get("attachment") or {}
            k = a.get("type")
            if k == "queued_command":
                text = _clean(_text(a.get("prompt")))
                if not text:
                    continue
                kind = _owner_kind(text)
                if kind in ("turn", "command"):
                    yield {"when": when, "kind": "owner", "how": "mid-turn", "text": text}
                elif kind == "notification" or text.startswith("<agent-message"):
                    yield {"when": when, "kind": "notification", "text": text}
            elif k in ("hook_success", "hook_system_message", "hook_additional_context", "hook_non_blocking_error"):
                body = a.get("stdout") or a.get("stderr") or a.get("content") or ""
                yield {"when": when, "kind": "hook", "text": f"{a.get('hookName') or k} [{k}]: {_cut(str(body), 600)}"}
            elif k == "inlined_image_paths":
                yield {"when": when, "kind": "owner_image", "text": ", ".join(a.get("paths") or [])}
        elif t == "system":
            st = o.get("subtype")
            if st == "compact_boundary":
                m = o.get("compactMetadata") or {}
                yield {"when": when, "kind": "system",
                       "text": f"COMPACTION ({m.get('trigger')}): {m.get('preTokens')} -> {m.get('postTokens')} tokens, {m.get('durationMs')} ms"}
            elif st in ("away_summary", "local_command"):
                yield {"when": when, "kind": "system", "text": f"{st}: {_clean(str(o.get('content')))}"}


def _minute(when):
    """'11-09 02:09' (local, as _when writes it) as a datetime, for distances within one session."""
    try:
        return datetime.strptime(f"2000-{when}", "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return None


def _dedupe_owner(events, window_s=600):
    """A mid-turn message can appear both inside a tool result and as a queued attachment: the same words
    within minutes are one message. Two turn records are two sends, and words sent again later are new
    messages: keyed on the text alone, three repeated approvals ("Engage" twice, "Done") vanished from
    the record (2026-11-09)."""
    last, out = {}, []
    for e in events:
        if e["kind"] == "owner":
            key = re.sub(r"\s+", " ", e["text"])[:300]
            at, prev = _minute(e.get("when")), last.get(key)
            if prev and not (prev[1] == "turn" and e.get("how") == "turn") and at and prev[0] \
                    and abs((at - prev[0]).total_seconds()) <= window_s:
                continue
            last[key] = (at, e.get("how"))
        out.append(e)
    return out


def scan(path):
    """Everything the hooks need from one transcript, in one pass plus the event pass."""
    s = {"boundaries": [], "summary": None, "nested": [], "edited": [], "cwd": None, "launch_cwd": None, "version": None,
         "title": None, "first": None, "last": None, "user_records": 0, "delivered_landings": 0}
    after_boundary_nested = []
    for o in _records(path):
        if o.get("isSidechain"):
            continue
        ts = o.get("timestamp")
        if ts:
            s["first"] = s["first"] or ts
            s["last"] = ts
        s["cwd"] = o.get("cwd") or s["cwd"]
        s["launch_cwd"] = s["launch_cwd"] or o.get("cwd")  # where `claude --resume` must run
        s["version"] = o.get("version") or s["version"]
        t = o.get("type")
        if t == "ai-title":
            s["title"] = o.get("aiTitle") or s["title"]
        elif t == "system" and o.get("subtype") == "compact_boundary":
            s["boundaries"].append(o.get("compactMetadata") or {})
            s["summary"] = None
            after_boundary_nested = []
        elif t == "user":
            if o.get("isCompactSummary"):
                s["summary"] = _text(o["message"].get("content"))
                s.setdefault("summaries", []).append(s["summary"])
            elif not o.get("isMeta"):
                c = (o.get("message") or {}).get("content")
                if isinstance(c, str) or (isinstance(c, list) and not any(
                        isinstance(b, dict) and b.get("type") == "tool_result" for b in c)):
                    s["user_records"] += 1
        elif t == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use":
                    fp = (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
                    if fp:
                        s["edited"].append(fp) if b.get("name") in ("Write", "Edit", "NotebookEdit") else None
        elif t == "attachment":
            a = o.get("attachment") or {}
            if a.get("type") == "nested_memory" and a.get("path"):
                s["nested"].append(a["path"])
                after_boundary_nested.append(a["path"])
            elif a.get("type") == "hook_additional_context" and str(a.get("hookName", "")).startswith("SessionStart") \
                    and "ferry:" in json.dumps(a.get("content")):
                s["delivered_landings"] += 1
    s["nested_before_last"] = [p for p in dict.fromkeys(s["nested"]) if p not in after_boundary_nested] \
        if s["boundaries"] else list(dict.fromkeys(s["nested"]))
    s["owner"] = [e for e in _dedupe_owner(list(read_events(path))) if e["kind"] == "owner"]
    return s


# --- git facts (read-only, never takes the index lock) --------------------------------------------

def _git(repo, *args):
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=4)
        return r.stdout.rstrip("\r\n") if r.returncode == 0 else None  # porcelain lines start with a space
    except Exception:  # noqa: BLE001
        return None


def _vendored(path):
    """True inside a tree an enclosing repo ignores (a vendored clone such as apps/kodi/upstream).
    Instructions found there belong to that project, not to the owner."""
    try:
        p = Path(path).resolve()
        repos = [d for d in p.parents if (d / ".git").exists()]
        for inner, outer in zip(repos, repos[1:]):
            r = subprocess.run(["git", "--no-optional-locks", "-C", str(outer), "check-ignore", "-q", str(inner)],
                               capture_output=True, timeout=4)
            if r.returncode == 0:
                return True
        return any(part in ("node_modules", ".venv", "site-packages") for part in p.parts)
    except Exception:  # noqa: BLE001
        return False


def _repo_of(path):
    try:
        p = Path(path)
        p = p if p.is_dir() else p.parent
        for d in [p, *p.parents]:
            if (d / ".git").exists():
                return d
    except Exception:  # noqa: BLE001
        return None
    return None


def repo_facts(paths, limit=8):
    roots = []
    for p in paths:
        r = _repo_of(p) if p else None
        if r and r not in roots:
            roots.append(r)
    facts = []
    for r in roots[:limit]:
        status = _git(r, "status", "--porcelain")
        dirty = [l[3:] for l in (status or "").splitlines() if len(l) > 3]
        remotes = (_git(r, "remote") or "").split()
        ahead = _git(r, "rev-list", "--count", "@{u}..HEAD") if remotes else None
        facts.append({"repo": str(r), "branch": _git(r, "branch", "--show-current") or _git(r, "rev-parse", "--abbrev-ref", "HEAD"),
                      "dirty": dirty, "remote": bool(remotes), "ahead": ahead,
                      "last": _git(r, "log", "-1", "--format=%h %s") or "no commits yet"})
    return facts


def _repo_lines(facts):
    out = []
    for f in facts:
        bits = [f"{f['branch'] or '?'}"]
        bits.append(f"{len(f['dirty'])} uncommitted: {', '.join(f['dirty'][:6])}" if f["dirty"] else "clean")
        if not f["remote"]:
            bits.append("NO REMOTE (exists on this disk only)")
        elif f["ahead"] not in (None, "0"):
            bits.append(f"{f['ahead']} commit{'' if f['ahead'] == '1' else 's'} not pushed")
        out.append(f"- {f['repo']}: {'; '.join(bits)}; last {f['last']}")
    return "\n".join(out)


# --- flush (PreCompact) ---------------------------------------------------------------------------

INSTRUCTIONS = """Compaction instructions from the owner's continuity hook (ferry). Follow them in addition to your usual summary format; they decide what survives this boundary.

1. The owner's words. In the section that lists the user's messages, give every message from the owner's last 12 turns completely and verbatim, including messages typed while work was running. Never shorten an owner message with "..." or a paraphrase; if space runs short, give older messages one line each and say they are kept verbatim in the checkpoint.
2. Open loops. List every question put to the owner that has no answer yet (quote it, with its time), every promise made ("I'll ...") that is not done, and every task in flight with the exact state it was left in: what is running, what is on screen, what was about to happen next.
3. Decisions and reasons. For each decision made, give the choice, the reason stated, and where it is written down (file path, or "only in conversation").
4. Unsaved knowledge. Name every requirement, literal wording the owner dictated, fact, measurement or lesson that exists only in this conversation and not yet in a file, commit or memory. These get written down right after compaction.
5. Standing rules. Quote verbatim every instruction the owner gave about how to work.
6. End the summary with this exact line, alone, as its last line:
{canary}
"""


def _checkpoint_dir(sid, trigger):
    return STORE / (sid or "unknown") / f"{_now().strftime('%Y%m%d-%H%M%S')}-{trigger or 'manual'}"


def flush(inp):
    if inp.get("agent_id"):
        return ""
    sid, tp, trigger = inp.get("session_id"), inp.get("transcript_path"), inp.get("trigger") or "manual"
    ck = _checkpoint_dir(sid, trigger)
    text = INSTRUCTIONS.format(canary=f"{CANARY} {ck}")
    record = {"ts": _now().isoformat(), "trigger": trigger, "canary": f"{CANARY} {ck}", "session": sid}
    try:
        s = scan(tp) if tp and Path(tp).exists() else None
        if s:
            facts = repo_facts(list(dict.fromkeys(s["edited"])) + ([s["cwd"]] if s["cwd"] else []))
            prev = (s.get("summaries") or [None])[-1]  # the last compaction's summary is on disk by now
            record.update(owner_messages=len(s["owner"]), user_records=s["user_records"], repos=facts,
                          version=s["version"], delivered_landings=s["delivered_landings"],
                          boundaries=len(s["boundaries"]),
                          previous_canary=None if prev is None else ("honored" if CANARY in prev else "ignored"))
            if facts:
                text += "\nRepository state at compaction (carry it into the summary's current-work section):\n" + _repo_lines(facts) + "\n"
    except Exception as e:  # noqa: BLE001 - the instructions still go out
        _err("flush.scan", e)
    try:
        ck.mkdir(parents=True, exist_ok=True)
        (ck / "instructions.txt").write_text(text, encoding="utf-8")
        (ck / "flush.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        _err("flush.record", e)
    return text[:CAP]


# --- land (SessionStart, source=compact) ------------------------------------------------------------

def _loops_table(body, src):
    """The table and the lines that introduce it. The answers and decisions below it stay in the file:
    carried whole, they spent the landing's budget and were cut mid-sentence (2026-11-09)."""
    start = next((i for i, line in enumerate(body) if line.lstrip().startswith("|")), None)
    if start is None:
        return body
    end = start
    while end < len(body) and body[end].lstrip().startswith("|"):
        end += 1
    keep = body[:end]
    if any(line.strip() for line in body[end:]):
        keep.append(f"(Answers and decisions below the table stay in {src}.)")
    return keep


def _ledger_loops(repos, budget=3000):
    out = []
    for r in repos:
        for name in ("docs/LEDGER.md", "LEDGER.md"):
            f = Path(r) / name
            if not f.exists():
                continue
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            for i, l in enumerate(lines):
                m = re.match(r"^(#+)\s+.*open loops", l, re.I)
                if m:
                    level, body = len(m.group(1)), []
                    for nxt in lines[i + 1:]:
                        h = re.match(r"^(#+)\s", nxt)
                        if h and len(h.group(1)) <= level:
                            break
                        body.append(nxt)
                    out.append(f"From {f}:\n" + "\n".join(_loops_table(body, f)).strip())
                    break
    return _cut("\n\n".join(out), budget)


def _latest_flush(sid):
    d = STORE / (sid or "unknown")
    try:
        cks = sorted(p for p in d.iterdir() if (p / "flush.json").exists())
        return json.loads((cks[-1] / "flush.json").read_text(encoding="utf-8")) if cks else None
    except Exception:  # noqa: BLE001
        return None


def _write_owner(sid, owner):
    d = STORE / (sid or "unknown")
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"# Owner's words, verbatim (secrets scrubbed) -- session {sid}\n", f"{len(owner)} messages.\n"]
    for i, e in enumerate(owner, 1):
        lines.append(f"\n### {i} . {e['when']} . {e['how']}\n\n{scrub(e['text'])}\n")
    p = d / "owner.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _boundary_after(tp, since, wait=0.0):
    """Is a compaction boundary newer than our flush already on disk? Claude Code (2.1.319) writes
    the compaction records only after SessionStart(compact) hooks return (measured 2026-11-08:
    a 3 s wait never saw them), so land asks the model to check the canary itself, and flush and
    archive verify it afterwards. Reads only the file's tail; `wait` stays 0 unless that changes."""
    deadline = time.time() + wait
    while True:
        try:
            with open(tp, "rb") as f:
                f.seek(0, 2)
                f.seek(max(0, f.tell() - 2_000_000))
                tail = f.read().decode("utf-8", "replace")
            for line in reversed(tail.splitlines()):
                if '"compact_boundary"' in line:
                    t = _ts(json.loads(line).get("timestamp"))
                    if t and since and t >= since:
                        return True
                    break
        except Exception:  # noqa: BLE001 - a partial line or a locked file: try again
            pass
        if time.time() >= deadline:
            return False
        time.sleep(0.25)


def land(inp):
    if inp.get("agent_id") or (inp.get("source") and inp.get("source") != "compact"):
        return None
    sid, tp = inp.get("session_id"), inp.get("transcript_path")
    fl = _latest_flush(sid)
    fresh = bool(fl) and _boundary_after(tp, _ts(fl.get("ts")))
    s = scan(tp)
    owner_md = _write_owner(sid, s["owner"])
    summary = s["summary"] if fresh else None  # never judge this compaction by an older summary
    expected = (fl or {}).get("canary", "").strip()
    if fl is None:
        canary = "ABSENT: no ferry checkpoint was written before this compaction (flush not wired, or it failed)"
    elif summary is None:
        canary = (f"self-check: the summary above should end with the line '{expected}'. If it does not, the "
                  "summarizer ignored ferry's instructions: trust it less")
    elif expected and expected in summary:
        canary = "honored: the summarizer followed ferry's instructions"
    elif CANARY in summary:
        canary = "honored (it names an older checkpoint)"
    else:
        canary = "IGNORED: the summarizer did not follow ferry's instructions; trust the summary less"
    meta = s["boundaries"][-1] if fresh and s["boundaries"] else {}
    how = meta.get("trigger") or (fl or {}).get("trigger", "?")
    size = f", {meta['preTokens']} -> {meta['postTokens']} tokens" if meta.get("preTokens") else ""
    n = len(s["owner"])
    head = [f"ferry: this context was rebuilt from a compaction summary ({how}{size}). "
            "The summary is lossy; the transcript is not.",
            f"Canary: {canary}.",
            "Before acting:",
            f"1. The owner's {n} message{'' if n == 1 else 's'} are kept verbatim in {owner_md}. Check it before acting on, "
            "or writing down, anything the summary paraphrases (requirements, literal wording, memory edits).",
            "2. Re-read the project instructions listed below that were loaded before compaction.",
            "3. Write any requirement or open question that lives only in the summary into its durable home now."]
    parts = ["\n".join(head)]
    # the owner's latest words, verbatim, most recent last, within budget
    budget, picked = 3600, []
    for e in reversed(s["owner"]):
        piece = f"[{e['when']} {e['how']}] {scrub(e['text'])}"
        if budget - len(piece) < 0 and picked:
            break
        picked.append(_cut(piece, budget))
        budget -= len(piece)
    if picked:
        parts.append("The owner's latest messages, verbatim:\n" + "\n\n".join(reversed(picked)))
    nested = [p for p in s.get("nested_before_last", []) if Path(p).exists() and not _vendored(p)]
    if nested:
        budget, shown, listed = 2400, [], []
        for p in nested:
            body = Path(p).read_text(encoding="utf-8", errors="replace")
            if len(body) <= budget:
                shown.append(f"--- {p} ---\n{body.strip()}")
                budget -= len(body)
            else:
                listed.append(p)
        block = "Project instructions loaded before compaction (they do not reload on their own):\n" + "\n\n".join(shown)
        if listed:
            block += "\nAlso read: " + ", ".join(listed)
        parts.append(block)
    paths = list(dict.fromkeys(s["edited"])) + ([s["cwd"]] if s["cwd"] else [])
    facts = repo_facts(paths)
    loops = _ledger_loops([f["repo"] for f in facts])
    repos = ("Repositories touched this session:\n" + _repo_lines(facts)) if facts else ""
    if loops:  # the loops take the room that is left, so the cap never cuts the repositories' state
        room = CAP - len("\n\n".join(parts)) - len(repos) - 60
        parts.append("Open loops on record:\n" + _cut(loops, max(room, 600)))
    if repos:
        parts.append(repos)
    context = _cut("\n\n".join(parts), CAP)
    drift = ""
    if s["user_records"] and not s["owner"]:
        drift = " Parser found no owner messages: run ferry selftest."
    seen = _selftest_version()
    if seen and s["version"] and seen != s["version"]:
        drift += f" Claude Code is {s['version']}; ferry last passed selftest on {seen}: run ferry selftest."
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": f"ferry: landed after compaction; canary {canary.split(':')[0]}; "
                             f"{len(s['owner'])} owner messages kept at {owner_md}.{drift}"}


# --- archive (SessionEnd) -----------------------------------------------------------------------------

def archive(inp):
    if inp.get("agent_id"):
        return None
    sid, tp = inp.get("session_id"), inp.get("transcript_path")
    s = scan(tp)
    if not s["owner"]:
        return None
    owner_md = _write_owner(sid, s["owner"])
    first = (s["first"] or "")[:16].replace("T", " ")
    last = (s["last"] or "")[:16].replace("T", " ")
    sums = s.get("summaries") or []
    canaries = f" | canary {sum(CANARY in x for x in sums)}/{len(sums)} compactions" if sums else ""
    line = (f"- {first} .. {last} UTC | {s['title'] or '(untitled)'} | {len(s['owner'])} owner msgs{canaries} | "
            f"resume: cd \"{s['launch_cwd']}\" && claude --resume {sid} | {owner_md} | {sid}")
    idx = STORE / "INDEX.md"
    old = idx.read_text(encoding="utf-8").splitlines() if idx.exists() else ["# ferry index: one line per session"]
    idx.write_text("\n".join([l for l in old if not l.endswith(sid)] + [line]) + "\n", encoding="utf-8")
    return None


def now(transcript=None):
    """Manual checkpoint: the owner said 'save our work'. Prints what is at risk."""
    tp = transcript or _newest_transcript()
    s = scan(tp)
    sid = Path(tp).stem
    owner_md = _write_owner(sid, s["owner"])
    facts = repo_facts(list(dict.fromkeys(s["edited"])) + ([s["cwd"]] if s["cwd"] else []))
    return (f"checkpoint: {len(s['owner'])} owner messages -> {owner_md}\n"
            + (_repo_lines(facts) or "no repositories touched"))


# --- replay (CLI) -------------------------------------------------------------------------------------

def replay(transcript, out_dir=None):
    transcript = Path(transcript)
    session = transcript.stem
    out = Path(out_dir) if out_dir else STORE / session / "replay"
    out.mkdir(parents=True, exist_ok=True)
    events = _dedupe_owner(list(read_events(transcript)))

    owner = [e for e in events if e["kind"] == "owner"]
    lines = [f"# Owner's words, verbatim -- session {session}\n",
             f"{len(owner)} messages. `how`: turn = sent as a prompt; mid-turn = typed while work ran; "
             "command = slash or ! command; interrupt = stop pressed.\n"]
    for i, e in enumerate(owner, 1):
        lines.append(f"\n### {i} . {e['when']} . {e['how']}\n\n{e['text']}\n")
    (out / "owner.md").write_text("\n".join(lines), encoding="utf-8")

    sk, n = [f"# Conversation skeleton -- session {session}\n"], 0
    for e in events:
        if e["kind"] == "owner":
            n += 1
            sk.append(f"\n---\n\n## [{n}] OWNER {e['when']} ({e['how']})\n\n{e['text']}\n")
        elif e["kind"] == "me":
            sk.append(f"\n**me {e['when']}:** {e['text']}\n")
        elif e["kind"] == "system":
            sk.append(f"\n> {e['when']} {e['text']}\n")
        elif e["kind"] == "summary":
            sk.append(f"\n> {e['when']} [compaction summary handed to the next context: {len(e['text'])} chars]\n")
        elif e["kind"] == "denial":
            sk.append(f"\n> {e['when']} OWNER DENIED a {e['tool']} call: {_cut(e['text'], 600)}\n")
    (out / "turns.md").write_text("\n".join(sk), encoding="utf-8")

    calls = [e for e in events if e["kind"] == "call"]
    (out / "calls.tsv").write_text("\n".join(f"{e['when']}\t{e['tool']}\t{e['gist'].replace(chr(9), ' ').replace(chr(10), ' | ')[:400]}"
                                             for e in calls), encoding="utf-8")

    def paired(tool):
        res, pend = [], []
        for e in events:
            if e["kind"] == "call" and e["tool"] == tool:
                pend.append(e)
            elif e["kind"] in ("result", "denial") and e["tool"] == tool and pend:
                res.append((pend.pop(0), e))
        return res + [(c, None) for c in pend]

    ag = [f"# Subagents -- session {session}\n"]
    for c, r in paired("Agent"):
        ag.append(f"\n## {c['when']} {c['input'].get('description')} [{c['input'].get('subagent_type') or 'general'}]\n\n"
                  f"**Brief:**\n\n{c['input'].get('prompt')}\n\n**Result:**\n\n{r['text'] if r else '(none in log)'}\n")
    notes = [e for e in events if e["kind"] == "notification"]
    ag.append(f"\n# Task notifications ({len(notes)})\n")
    for e in notes:
        ag.append(f"\n## {e['when']}\n\n{_cut(e['text'], 8000)}\n")
    (out / "agents.md").write_text("\n".join(ag), encoding="utf-8")

    asks = [f"# Questions put to the owner -- session {session}\n"]
    for c, r in paired("AskUserQuestion"):
        asks.append(f"\n## {c['when']}\n\n```json\n{json.dumps(c['input'].get('questions'), indent=1, ensure_ascii=False)}\n```\n\n"
                    f"**Answer:** {r['text'] if r else '(no answer in log)'}\n")
    (out / "asks.md").write_text("\n".join(asks), encoding="utf-8")

    errs = [f"# Failed tool calls -- session {session}\n"]
    last_call = {}
    for e in events:
        if e["kind"] == "call":
            last_call[e["tool"]] = e
        elif e["kind"] in ("result", "denial") and (e.get("error") or e["kind"] == "denial"):
            c = last_call.get(e["tool"], {})
            errs.append(f"\n## {e['when']} {e['tool']}{' (DENIED)' if e['kind'] == 'denial' else ''}\n\n"
                        f"call: `{_cut(c.get('gist', ''), 400)}`\n\n{_cut(e['text'], 1500)}\n")
    (out / "errors.md").write_text("\n".join(errs), encoding="utf-8")

    sysl = [f"# System record -- session {session}\n"]
    for e in events:
        if e["kind"] in ("system", "hook", "owner_image"):
            sysl.append(f"- {e['when']} [{e['kind']}] {e['text']}")
        elif e["kind"] == "summary":
            sysl.append(f"\n## {e['when']} Compaction summary as handed over\n\n{e['text']}\n")
    (out / "system.md").write_text("\n".join(sysl), encoding="utf-8")

    for old in out.glob("log-*.md"):
        old.unlink()
    chunk, size, idx = [], 0, 1

    def flush_chunk():
        nonlocal chunk, size, idx
        if chunk:
            (out / f"log-{idx:02d}.md").write_text("\n".join(chunk), encoding="utf-8")
            idx, chunk, size = idx + 1, [], 0

    for e in events:
        k = e["kind"]
        if k == "owner":
            s = f"\n[{e['when']}] OWNER ({e['how']}): {e['text']}\n"
        elif k == "me":
            s = f"[{e['when']}] ME: {e['text']}"
        elif k == "call":
            s = f"[{e['when']}] -> {e['tool']}: {e['gist']}"
        elif k in ("result", "denial"):
            lim = 6000 if e["tool"] in ("Agent", "AskUserQuestion") else (1500 if e.get("error") or k == "denial" else 400)
            tag = "DENIED" if k == "denial" else ("ERROR" if e.get("error") else "ok")
            s = f"[{e['when']}] <- {tag}: {_cut(e['text'], lim)}"
        elif k == "notification":
            s = f"[{e['when']}] NOTIFY: {_cut(e['text'], 3000)}"
        elif k == "summary":
            s = f"\n[{e['when']}] ===== COMPACTION SUMMARY ({len(e['text'])} chars) =====\n{e['text']}\n===== END SUMMARY =====\n"
        else:
            s = f"[{e['when']}] {k.upper()}: {e['text']}"
        chunk.append(s)
        size += len(s.encode("utf-8"))
        if size >= CHUNK_BYTES:
            flush_chunk()
    flush_chunk()

    stats = {"session": session, "transcript": str(transcript),
             "events": dict(Counter(e["kind"] for e in events)),
             "owner_by_how": dict(Counter(e["how"] for e in owner)),
             "tools": dict(Counter(e["tool"] for e in calls).most_common()),
             "chunks": idx - 1, "out": str(out)}
    (out / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    return stats


# --- selftest (CLI) ---------------------------------------------------------------------------------

def _newest_transcript(min_bytes=50_000):
    root = Path.home() / ".claude" / "projects"
    files = [p for p in root.glob("*/*.jsonl") if p.stat().st_size >= min_bytes]
    return str(max(files, key=lambda p: p.stat().st_mtime)) if files else None


def _selftest_version():
    try:
        return json.loads((STORE / "selftest.json").read_text(encoding="utf-8")).get("version")
    except Exception:  # noqa: BLE001
        return None


def _settings_hooks():
    """Every script path a settings.json hook runs, and whether it exists."""
    out = []
    f = Path.home() / ".claude" / "settings.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for event, groups in (data.get("hooks") or {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                for tok in re.findall(r"[A-Za-z]:[/\\][^\s\"']+\.(?:py|sh|ps1)|~?/[^\s\"']+\.(?:py|sh|ps1)", h.get("command", "")):
                    p = Path(os.path.expanduser(tok))
                    out.append((event, g.get("matcher", ""), str(p), p.exists(), h.get("timeout")))
    return out


def selftest(transcript=None):
    global STORE
    import tempfile
    real_store, STORE = STORE, Path(tempfile.mkdtemp(prefix="ferry-selftest-"))
    tp = transcript or _newest_transcript()
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    try:
        t0 = time.time()
        s = scan(tp)
        how = Counter(e["how"] for e in s["owner"])
        check("parse: owner messages found", s["owner"] or not s["user_records"],
              f"{len(s['owner'])} owner ({dict(how)}) from {s['user_records']} user records, {time.time() - t0:.2f}s")
        machine = [e["text"][:40] for e in s["owner"] if TAG.match(e["text"].lstrip())
                   and TAG.match(e["text"].lstrip()).group(1) not in OWNER_TAGS]
        check("parse: no machine messages taken for the owner's", not machine, "; ".join(machine))
        payload = {"session_id": "selftest", "transcript_path": tp, "cwd": s["cwd"], "trigger": "manual"}
        t0 = time.time()
        out = flush(payload)
        check("flush: plain text, starts with a letter", out[:1].isalpha(), repr(out[:40]))
        check("flush: under the 10,000-char cap", len(out) < 10_000, f"{len(out)} chars, {time.time() - t0:.2f}s")
        check("flush: carries the canary line", CANARY in out and _latest_flush("selftest") is not None)
        out2 = flush({"session_id": "selftest", "transcript_path": "C:/nope/missing.jsonl", "trigger": "auto"})
        check("flush: still instructs when the transcript is missing", CANARY in out2)
        check("flush: silent in subagents", flush({**payload, "agent_id": "x"}) == "")
        t0 = time.time()
        res = land({**payload, "source": "compact"})
        ctx = res["hookSpecificOutput"]["additionalContext"]
        check("land: JSON with additionalContext", isinstance(ctx, str) and ctx.startswith("ferry:"),
              f"{len(ctx)} chars, {time.time() - t0:.2f}s")
        check("land: under the 10,000-char cap", len(ctx) < 10_000)
        check("land: the repositories' state survives the cap",
              "Repositories touched this session" in ctx or not s["edited"])
        check("land: heartbeat for the owner", "ferry: landed" in res.get("systemMessage", ""))
        check("land: wrote owner.md", (STORE / "selftest" / "owner.md").exists())
        check("land: silent on startup and in subagents",
              land({**payload, "source": "startup"}) is None and land({**payload, "source": "compact", "agent_id": "x"}) is None)
        t0 = time.time()
        archive(payload)
        idx = (STORE / "INDEX.md").read_text(encoding="utf-8") if (STORE / "INDEX.md").exists() else ""
        check("archive: one index line", sum(l.endswith("| selftest") for l in idx.splitlines()) == 1
              and "claude --resume selftest" in idx,
              f"{time.time() - t0:.2f}s (SessionEnd budget: hook timeout)")
        archive(payload)
        check("archive: idempotent", (STORE / "INDEX.md").read_text(encoding="utf-8").count("| selftest") == 1)
        sample = "key 0123456789abcdef0123456789abcdef token=hunter2secret ghp_abcdefghijklmnopqrstuvwx1234"
        cleaned = scrub(sample)
        check("scrub: hex key, assignment, GitHub token", "0123456789abcdef" not in cleaned and "hunter2" not in cleaned
              and "ghp_" not in cleaned, cleaned)
        prose = "the existing ask-before-driving-the-lab rule; tasks-for-the-owner-are-written-down"
        check("scrub: leaves prose alone", scrub(prose) == prose, scrub(prose))
        ev = [{"kind": "owner", "how": "turn", "text": "Engage", "when": "11-08 18:00"},
              {"kind": "owner", "how": "turn", "text": "Engage", "when": "11-09 02:09"},
              {"kind": "owner", "how": "turn", "text": "Done", "when": "11-09 02:12"},
              {"kind": "owner", "how": "turn", "text": "Done", "when": "11-09 02:14"},
              {"kind": "owner", "how": "mid-turn", "text": "Wait", "when": "11-09 02:10"},
              {"kind": "owner", "how": "mid-turn", "text": "Wait", "when": "11-09 02:11"}]
        kept = [f"{e['when']} {e['text']}" for e in _dedupe_owner(ev)]
        check("parse: words sent again are kept; one message seen twice is one", len(kept) == 5, "; ".join(kept))
        repo = Path(tempfile.mkdtemp(prefix="ferry-loops-"))
        (repo / "docs").mkdir()
        (repo / "docs" / "LEDGER.md").write_text(
            "# L\n\n## 0. Open loops\n\nEvery question lands here.\n\n| # | Question |\n|---|---|\n| 1 | first? |\n"
            "| 2 | last row? |\n\nDecided long ago: " + "prose " * 600 + "\n\n## 1. Next\n", encoding="utf-8")
        loops = _ledger_loops([str(repo)])
        check("land: the open-loops table whole, the answers left in the file",
              "| 2 | last row? |" in loops and "prose prose" not in loops and "stay in" in loops, f"{len(loops)} chars")
        hooks = _settings_hooks()
        missing = [h for h in hooks if not h[3]]
        check("settings: every hook script exists", not missing, "; ".join(f"{e}:{p}" for e, _, p, _, _ in missing))
        odd = [h for h in hooks if isinstance(h[4], (int, float)) and h[4] > 600]
        check("settings: hook timeouts are seconds (<= 600)", not odd, "; ".join(f"{e}:{Path(p).name}={t}" for e, _, p, _, t in odd))
    except Exception as e:  # noqa: BLE001
        check("selftest crashed", False, f"{type(e).__name__}: {e}")
    finally:
        STORE = real_store
    passed = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    print(f"\n{sum(ok for _, ok, _ in results)}/{len(results)} passed on {tp}")
    if passed:
        try:
            STORE.mkdir(parents=True, exist_ok=True)
            (STORE / "selftest.json").write_text(json.dumps({"version": scan(tp)["version"], "ts": _now().isoformat(),
                                                             "transcript": tp}), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return 0 if passed else 1


# --- entry --------------------------------------------------------------------------------------------

def _hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:  # noqa: BLE001
        return {}


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    cmd = argv[0] if argv else ""
    if cmd in ("flush", "land", "archive"):  # hook mode: never fail the session
        inp = _hook_input()
        try:
            if cmd == "flush":
                sys.stdout.write(flush(inp))
            elif cmd == "land":
                out = land(inp)
                if out:
                    sys.stdout.write(json.dumps(out))
            else:
                archive(inp)
        except Exception as e:  # noqa: BLE001 - fail visibly, never silently
            _err(f"hook {cmd}", e)
            if cmd == "flush":  # the summarizer still gets the essentials
                sys.stdout.write(INSTRUCTIONS.format(canary=f"{CANARY} unavailable"))
            elif cmd == "land":
                tp = inp.get("transcript_path", "?")
                sys.stdout.write(json.dumps({
                    "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
                        f"ferry: this context was rebuilt from a compaction summary, and ferry's landing failed "
                        f"({type(e).__name__}: {e}). The summary is lossy. The full record is the transcript {tp}; "
                        f"rebuild the owner's words with: python ~/.claude/hooks/ferry.py replay \"{tp}\""},
                    "systemMessage": f"ferry: landing FAILED ({type(e).__name__}); see {STORE / 'errors.log'}"}))
        return 0
    if cmd == "replay" and len(argv) >= 2:
        print(json.dumps(replay(argv[1], argv[2] if len(argv) > 2 else None), indent=1))
        return 0
    if cmd == "now":
        print(now(argv[1] if len(argv) > 1 else None))
        return 0
    if cmd == "selftest":
        return selftest(argv[1] if len(argv) > 1 else None)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
