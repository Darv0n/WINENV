# WINENV Manifesto

## Design Invariants

1. **Single Source of Truth** — Every config exists in exactly one place: `WINENV/configs/`.
   Target locations receive symlinks, never copies.

2. **Idempotent Deployment** — Running `deploy.ps1` any number of times produces the
   same result. No manual steps. No "run this first" dependencies between configs.

3. **Non-Destructive** — Existing files are backed up before replacement. `deploy.ps1`
   never deletes without creating a backup first. `--DryRun` is always available.

4. **LF Everywhere** — All text files use LF line endings. CRLF breaks bash scripts,
   git hooks, and Claude Code hooks. `.gitattributes` enforces this at the repo level.

5. **Identity Stays Local** — `~/.gitconfig` is never fully managed. We use `[include]`
   to layer our config on top of the user's identity and LFS settings.

6. **Bootstrap from Nothing** — A fresh Windows 11 machine can reach full config with:
   `install.ps1` then `deploy.ps1`. PowerShell 5.1 (built-in) is sufficient to start.

7. **Agent-Friendly** — Prompts are single-line. Output is parseable. Status information
   is machine-readable. No decorative elements that consume terminal real estate.

## Philosophy

This is not a dotfiles repo. It's a workstation operating system — the layer between
the tools and the human (and the AI). Every config decision serves one of:

- **Speed** — Reduce keystrokes, eliminate context switches
- **Safety** — Prevent destructive operations, enforce line endings
- **Clarity** — Make state visible (starship prompt, status line, git aliases)
- **Collaboration** — Keep the human-AI pair working in the same environment
