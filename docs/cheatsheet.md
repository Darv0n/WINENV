# WINENV Cheatsheet

Quick reference for the full environment. Organized by task, escalating from basic to S-tier.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `>` | Run in any shell (PS7 or Git Bash) |
| `PS>` | PowerShell 7 only |
| `$` | Git Bash only |
| `CC` | Inside a Claude Code session |
| `VSC` | VS Code keybinding |

---

## Navigation

```bash
proj                      # jump to ~/projects
apps                      # jump to ~/projects/apps
z my-api                  # zoxide: jump to frecent match
z -                       # zoxide: back to previous dir
```

**S-tier:** Zoxide learns from your `cd` history. After a few days, `z` + a fragment gets you anywhere.

---

## Git — Daily Flow

### Basics

```bash
gs                        # status
ga .                      # stage all
gc -m "message"           # commit
gp                        # push
gd                        # diff unstaged
gd --cached               # diff staged
gl                        # log, last 20 one-liners
```

### Intermediate

```bash
git lg                    # graph view, decorated, 20 entries
git last                  # show last commit
git unstage file.txt      # unstage a file without losing changes
git amend                 # amend last commit (keep message)
git wip                   # stage everything + commit "WIP"
```

### S-tier combos

```bash
# Start feature, push, come back
gco -b feature/thing && gp    # autoSetupRemote handles tracking

# Quick save before risky operation
git wip                        # snapshot everything as WIP
gco main                       # switch to main
# ... do stuff ...
gco feature/thing              # come back
git reset HEAD~1               # unwrap the WIP commit, files intact

# Conflict replay (rerere is on)
# First time: resolve manually. Git records it.
# Next time: same conflict auto-resolves.
```

---

## Claude Code — Session Modes

### Start a session

```bash
claude                    # start in current dir
claude "do the thing"     # start with a prompt
claude -r                 # resume last session
```

### Permission modes

```bash
yolo                      # NORMAL -> YOLO (bypass perms, hooks ON)
yolo                      # YOLO -> NORMAL (toggle back)
yolo -Sicko               # any -> SICKO (bypass perms, hooks OFF)
yolo -Off                 # any -> NORMAL
yolo -Status              # check current mode
```

### Mode selection guide

| Task | Mode | Why |
|------|------|-----|
| Exploring new codebase | NORMAL | Review what the agent touches |
| Building feature you designed | YOLO | Trust the agent, guard catches mistakes |
| Rapid prototyping / vibe coding | YOLO | Speed over caution, hooks still protect you |
| Multi-file refactor you understand | YOLO | You know what to expect |
| Registry edits, driver config | SICKO | Guard would block legitimate ops |
| Bootstrap / system provisioning | SICKO | Deep system access needed |
| Anything with `rm`, `reset`, `force` | NORMAL | Let the guard do its job |

### S-tier session flow

```bash
# 1. Start session in YOLO for speed
yolo

# 2. Build the feature
claude "implement the auth middleware per CLAUDE.md spec"

# 3. Drop back to NORMAL for review
yolo

# 4. Review in a fresh session
claude "review the last 3 commits for issues"
```

---

## VS Code — Keyboard Flow

| Shortcut | Action | When |
|----------|--------|------|
| `Alt+;` | Editor / terminal toggle | Supervising Claude in integrated terminal |
| `Alt+J` | Previous tab | Reviewing files Claude changed |
| `Alt+K` | Next tab | Reviewing files Claude changed |
| `Alt+B` | Toggle sidebar | Clear screen space during long sessions |
| `Alt+P` | Toggle panel | Show/hide terminal + output |

### S-tier combo

```
Alt+;          → jump to terminal
run claude     → start session
Alt+;          → jump back to editor to watch file changes
Alt+J / Alt+K  → flip through modified files
Alt+;          → back to terminal to give feedback
```

---

## Deploy & Maintain

### Update configs

```bash
# Edit a config in WINENV (symlinks mean it's live immediately)
code ~/projects/apps/WINENV/configs/starship/starship.toml

# If you change a config that needs profile reload:
# just restart terminal — symlinks point to the repo
```

### Re-deploy after git pull

```powershell
pwsh scripts/deploy.ps1 -DryRun    # preview changes
pwsh scripts/deploy.ps1             # deploy (idempotent)
```

### Verify everything

```powershell
pwsh bootstrap/verify.ps1           # all tools PASS/FAIL with versions
```

### New machine

```powershell
# 1. Clone WINENV
git clone https://github.com/Darv0n/WINENV.git ~/projects/apps/WINENV

# 2. Bootstrap
powershell -ExecutionPolicy Bypass -File ~/projects/apps/WINENV/bootstrap/install.ps1

# 3. Restart terminal, then deploy
pwsh ~/projects/apps/WINENV/scripts/deploy.ps1

# 4. Verify
pwsh ~/projects/apps/WINENV/bootstrap/verify.ps1
```

---

## New Project Setup

### Basic

```bash
mkdir ~/projects/apps/my-project && cd $_
git init
cp ~/projects/apps/WINENV/templates/repo/.gitattributes .
cp ~/projects/apps/WINENV/templates/repo/CLAUDE.md .
cp -r ~/projects/apps/WINENV/templates/repo/.claude .
```

### S-tier (repo + GitHub + Claude context in one shot)

```bash
mkdir ~/projects/apps/my-project && cd $_
git init

# Copy templates
cp ~/projects/apps/WINENV/templates/repo/.gitattributes .
cp -r ~/projects/apps/WINENV/templates/repo/.claude .
cp ~/projects/apps/WINENV/templates/repo/CLAUDE.md .

# Customize CLAUDE.md
code CLAUDE.md    # edit project name, structure, conventions

# First commit + GitHub
ga . && gc -m "Initialize project"
gh repo create my-project --public --source . --push

# Start building
yolo
claude "scaffold this project based on CLAUDE.md"
```

---

## Starship Prompt — Reading It

```
~/projects/WINENV  main ?1 >
│                    │    │  └── green = last command succeeded, red = failed
│                    │    └──── ?1 = 1 untracked file (git status codes)
│                    └───────── branch name (purple)
└────────────────────────────── cwd, truncated to 3 levels
```

### Git status symbols

| Symbol | Meaning |
|--------|---------|
| `?` | Untracked files |
| `!` | Modified files |
| `+` | Staged files |
| `>` | Ahead of remote |
| `<` | Behind remote |
| `=` | Up to date |
| `~` | Conflicted |

---

## Safety — What Gets Blocked

These commands are blocked by `guard-destructive-bash.sh` in NORMAL and YOLO modes:

| Blocked | Safe alternative |
|---------|-----------------|
| `rm -rf dir/` | `rm -r dir/` (no force) or `git clean -n` (dry run first) |
| `git push --force` | `git push --force-with-lease` (safer) |
| `git reset --hard` | `git stash` then reset, or `git reset --soft` |
| `git clean -f` | `git clean -n` (dry run) then `git clean -f` manually |
| `git branch -D` | `git branch -d` (safe delete, fails if unmerged) |
| `git checkout .` | `git stash` first |

**In SICKO mode:** None of these are blocked. You are the guard.

---

## Status Line — Reading It

```
[main] | claude-opus-4-6 | $12.34 | 45.2k tok | 23% cache
```

| Segment | Meaning | Watch for |
|---------|---------|-----------|
| `[main]` | Current git branch | Wrong branch = wrong context |
| `claude-opus-4-6` | Active model | Confirms which model is running |
| `$12.34` | Session cost | Budget awareness |
| `45.2k tok` | Tokens consumed | Context window pressure |
| `23% cache` | Cache hit rate | Low = repetitive uncached work |

---

## Quick Combos by Goal

| I want to... | Commands |
|--------------|----------|
| Start coding fast | `yolo && claude` |
| Start coding carefully | `yolo -Off && claude` |
| Do dangerous system work | `yolo -Sicko && claude` |
| Check what mode I'm in | `yolo -Status` |
| Update my whole environment | `cd ~/projects/apps/WINENV && git pull && pwsh scripts/deploy.ps1` |
| Start a new project | Copy templates, `git init`, `gh repo create` |
| See what deploy would do | `pwsh scripts/deploy.ps1 -DryRun` |
| Check all tools work | `pwsh bootstrap/verify.ps1` |
| Quick save before experimenting | `git wip` |
| Undo that quick save | `git reset HEAD~1` |
| Jump to a project fast | `z project-name` |
| Review what Claude did | `git lg` then `gd HEAD~3..HEAD` |
