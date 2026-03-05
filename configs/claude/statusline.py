#!/usr/bin/env python3
"""Claude Code status line — git, context, cost, lines."""
import json
import subprocess
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


def get_git_info():
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=2
        ).stdout.strip()
        if not branch:
            return None, False
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=2
        ).stdout.strip())
        return branch, dirty
    except Exception:
        return None, False


def ctx_color(pct):
    if pct < 50:
        return GREEN
    if pct < 80:
        return YELLOW
    return RED


def main():
    data = json.load(sys.stdin)

    # Project name
    project_dir = data.get("workspace", {}).get("project_dir", "")
    project_name = project_dir.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1] if project_dir else "?"

    # Model
    model = data.get("model", {}).get("display_name", "?")

    # Context window
    ctx_pct = data.get("context_window", {}).get("used_percentage", 0)

    # Cost
    cost = data.get("cost", {}).get("total_cost_usd", 0)

    # Tokens
    ctx = data.get("context_window", {})
    total_in = ctx.get("total_input_tokens", 0)
    total_out = ctx.get("total_output_tokens", 0)
    total_tokens = total_in + total_out

    # Lines changed
    added = data.get("cost", {}).get("total_lines_added", 0)
    removed = data.get("cost", {}).get("total_lines_removed", 0)

    # Git
    branch, dirty = get_git_info()

    sep = f" {DIM}|{RESET} "
    parts = []

    # Project
    parts.append(f"{BOLD}{CYAN}{project_name}{RESET}")

    # Git branch + dirty flag
    if branch:
        if dirty:
            parts.append(f"{YELLOW}{branch} *{RESET}")
        else:
            parts.append(f"{GREEN}{branch}{RESET}")

    # Model name
    parts.append(f"{DIM}{model}{RESET}")

    # Context usage (color shifts green -> yellow -> red)
    cc = ctx_color(ctx_pct)
    parts.append(f"{cc}ctx:{ctx_pct:.0f}%{RESET}")

    # Session cost + tokens
    parts.append(f"${cost:.2f}")
    if total_tokens:
        tok_str = f"{total_tokens / 1000:.1f}k" if total_tokens < 1_000_000 else f"{total_tokens / 1_000_000:.1f}M"
        parts.append(f"{DIM}{tok_str} tok{RESET}")

    # Lines added/removed
    if added or removed:
        parts.append(f"{GREEN}+{added}{RESET} {RED}-{removed}{RESET}")

    print(sep.join(parts))


if __name__ == "__main__":
    main()
