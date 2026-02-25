<div align="center">

# WINENV

**AI-augmented Windows 11 developer workstation.**
**One repo. One command. Everything configured.**

`bootstrap` &rarr; `deploy` &rarr; `verify` &rarr; code.

---

[![Windows 11](https://img.shields.io/badge/Windows_11-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](#)
[![PowerShell 7](https://img.shields.io/badge/PowerShell_7-5391FE?style=for-the-badge&logo=powershell&logoColor=white)](#)
[![Claude Code](https://img.shields.io/badge/Claude_Code-191919?style=for-the-badge&logo=anthropic&logoColor=white)](#)
[![Tokyo Night](https://img.shields.io/badge/Tokyo_Night-1A1B26?style=for-the-badge&logoColor=white)](#)

</div>

---

WINENV is a **single-source-of-truth configuration system** for a Windows 11 development machine. Every config file lives in this repo and gets deployed to the right place via symlinks. Change it here, it changes everywhere. No manual sync. No drift.

Built for an AI-augmented workflow where Claude Code is a first-class citizen — with live cost tracking, destructive command guardrails, and a one-command YOLO mode for when you trust the agent and want to move fast.

---

## Quick Start

```powershell
# Fresh machine? Three commands.
powershell -ExecutionPolicy Bypass -File bootstrap\install.ps1   # install tools
pwsh scripts\deploy.ps1                                          # deploy configs
pwsh bootstrap\verify.ps1                                        # confirm everything works
```

> Preview before deploying: `pwsh scripts/deploy.ps1 -DryRun`

---

## Architecture

```
 Layer 4  AI Agent     Claude Code settings, hooks, rules, MCP, status line
 Layer 3  Editor       VS Code settings, keybindings, terminal profiles
 Layer 2  Shell        PowerShell 7 + Git Bash, shared Starship prompt, zoxide
 Layer 1  Git          Managed gitconfig (aliases, rerere, push), global ignore/attributes
 Layer 0  Platform     Windows Terminal, winget DSC, JetBrainsMono Nerd Font
```

Each layer builds on the one below. Deploy handles all of them in one pass.

---

## What Gets Deployed

| Config | Target | Method |
|--------|--------|--------|
| PowerShell 7 profile | `~/Documents/PowerShell/profile.ps1` | Symlink |
| Git Bash (.bashrc, .bash_profile) | `~/.bashrc`, `~/.bash_profile` | Symlink |
| Starship prompt | `~/.config/starship.toml` | Symlink |
| Git config | `~/.gitconfig` | `[include]` directive |
| Git ignore + attributes | `~/.config/git/` | Symlink |
| VS Code settings + keybindings | `%APPDATA%/Code/User/` | Symlink |
| Windows Terminal | WT `LocalState/settings.json` | Symlink |
| Claude Code (settings, hooks, rules) | `~/.claude/` | Symlink |

> **Why symlinks?** Change the config in WINENV, it's live everywhere instantly. `git pull` updates your entire workstation.

> **Why `[include]` for git?** Your `~/.gitconfig` keeps your `[user]` identity and LFS config. WINENV manages behavior (aliases, rerere, push defaults) without touching identity. Clean separation.

---

## Claude Code Integration

WINENV treats Claude Code as infrastructure, not an afterthought.

### Live Status Line

Real-time session metrics in your terminal — model, cost, tokens, and cache hit rate:

```
[main] | claude-opus-4-6 | $2.47 | 18.3k tok | 41% cache
```

Zero-overhead observability. Always know what the agent is costing you.

### Destructive Command Guard

A `PreToolUse` hook intercepts every Bash command Claude tries to run. Blocked patterns:

```
rm -rf                    # recursive force delete
git push --force          # history rewrite
git reset --hard          # discard uncommitted work
git clean -f              # nuke untracked files
git branch -D             # force-delete branch
git checkout .            # discard working tree
DROP DATABASE / TABLE     # destructive SQL
```

The hook fires **even in YOLO mode**. You can go fast without going off a cliff.

### Permission Modes

Three escalation levels, one command:

```powershell
yolo              # toggle NORMAL <-> YOLO
yolo -Sicko       # escalate to SICKO
yolo -Off         # return to NORMAL from any level
yolo -Status      # check current mode
```

| Mode | Permissions | Hooks | When to use |
|------|------------|-------|-------------|
| **NORMAL** | Per-tool approval | Active | Default. Learning a codebase, reviewing agent output. |
| **YOLO** | Bypass all | **Still active** | You trust the agent. Move fast. Guard has your back. |
| **SICKO** | Bypass all | **Disabled** | Deep system work. Registry, drivers, infra. You are the safety net. |

<details>
<summary><b>How it works</b></summary>

<br>

Both modes manipulate `settings.local.json`, which overrides `settings.json` at the project level.

**YOLO** writes `bypassPermissions` — hooks in `settings.json` still fire because the local override only covers permissions. `guard-destructive-bash.sh` remains your safety net.

**SICKO** writes `bypassPermissions` + `"hooks": {}` — the empty hooks object at the local level shadows the shared hooks entirely. The guard is sleeping. You are the operator.

Your original `settings.local.json` is backed up to `.pre-yolo` on first escalation and restored on `-Off`. Auto-toggle from any elevated mode returns straight to NORMAL.

</details>

### Operating Principles

Ten principles auto-load into every Claude session via `rules/principles.md`:

<details>
<summary><b>View all 10 principles</b></summary>

<br>

1. **Redistribution Over Removal** — Move capabilities, don't delete them
2. **Explicit State Over Implicit Context** — Write state to artifacts; context degrades at boundaries
3. **The Razor and the Pause** — Critical analysis then charitable interpretation, in order
4. **Errors Are Curriculum** — Name failures; ask what structural condition made them possible
5. **Correction Is Additive** — Add the complementary impulse, don't suppress the original
6. **Recursive Self-Application** — Validate frameworks by applying them to themselves
7. **Tension as Generative Force** — Hold opposing forces; the design satisfying both poles wins
8. **Vocabulary Is Architecture** — One term means exactly one thing, everywhere
9. **Single Source of Truth** — Every artifact exists in exactly one canonical location
10. **Progressive Disclosure** — Load only what's needed for the current phase

</details>

---

## Shell Environment

Both shells share the same aliases, the same prompt, and the same navigation — so switching between them is seamless.

### Shared Aliases

```
gs    git status              proj   cd ~/projects
ga    git add                 apps   cd ~/projects/apps
gc    git commit              yolo   toggle YOLO mode
gp    git push
gl    git log --oneline -20
gd    git diff
gco   git checkout
gb    git branch
```

### Starship Prompt

Minimal, single-line, shared across PowerShell 7 and Git Bash:

```
~/projects/WINENV  main ?1 >
```

Shows directory (truncated to 3 levels), git branch, git status indicators, and language versions when detected. No decorative noise — optimized for AI agent output parsing.

### Zoxide

Smart directory jumping. `z projects` from anywhere. Learns from your `cd` history.

### PSReadLine (PowerShell)

- **Up/Down arrows** — search history by prefix (type `git` then press Up)
- **Tab** — cycle through completions (MenuComplete)
- **Prediction** — inline suggestions from history

---

## VS Code

<details>
<summary><b>Editor settings</b></summary>

<br>

- **Font:** JetBrainsMono Nerd Font, 13pt, ligatures on
- **Theme:** Tokyo Night
- **Format on save:** enabled (critical for AI-generated code)
- **Auto-save:** on focus change
- **Tab size:** 2 spaces (4 for Python)
- **Line endings:** LF enforced
- **Trim trailing whitespace** and insert final newline
- **Minimap:** off
- **Preview mode:** off (files open, not preview)

</details>

<details>
<summary><b>Keybindings</b></summary>

<br>

| Shortcut | Action |
|----------|--------|
| `Alt+;` | Toggle focus: editor ↔ terminal |
| `Alt+J` / `Alt+K` | Previous / next tab |
| `Alt+B` | Toggle sidebar |
| `Alt+P` | Toggle panel |

Designed to minimize mouse usage during AI-supervised coding sessions.

</details>

<details>
<summary><b>Terminal profiles</b></summary>

<br>

- **PowerShell 7** (default) — `pwsh.exe -NoLogo`
- **Git Bash** — `bash.exe --login -i`
- **Command Prompt** — available as fallback

All start in `~/projects`. Same font. Same theme.

</details>

---

## Git Configuration

<details>
<summary><b>Behavior (managed by WINENV)</b></summary>

<br>

```
push.default          = current       # push current branch, not all
push.autoSetupRemote  = true          # auto-track on first push
pull.rebase           = true          # rebase over merge (linear history)
fetch.prune           = true          # auto-delete stale remotes
merge.conflictstyle   = diff3         # show original + current + incoming
rerere.enabled        = true          # record & replay conflict resolutions
diff.colorMoved       = default       # highlight moved code blocks
core.autocrlf         = false         # LF enforced via .gitattributes, not conversion
core.editor           = code --wait
```

</details>

<details>
<summary><b>Git aliases</b></summary>

<br>

```
git st         status
git co         checkout
git br         branch
git ci         commit
git lg         log --oneline --graph --decorate -20
git last       log -1 HEAD
git unstage    reset HEAD --
git amend      commit --amend --no-edit
git wip        !git add -A && git commit -m 'WIP'
```

</details>

<details>
<summary><b>Global ignore patterns</b></summary>

<br>

OS files, editor artifacts, Python/Node build outputs, environment files (`.env`, `*.pem`, `*.key`), Claude Code ephemeral state, and common build directories. [Full list →](configs/git/gitignore-global)

</details>

---

## Bootstrap

Starting from a fresh Windows 11 machine with nothing but PowerShell 5.1 and winget:

```
 1. powershell install.ps1     Installs PS7, Starship, Zoxide, JetBrainsMono NF
 2. restart terminal            Pick up new PATH and fonts
 3. pwsh deploy.ps1 -DryRun    Preview all symlinks and includes
 4. pwsh deploy.ps1             Deploy everything
 5. restart terminal            Load new profiles
 6. pwsh verify.ps1             Confirm all tools present and versioned
 7. code                        Done.
```

<details>
<summary><b>What install.ps1 does</b></summary>

<br>

- Installs PowerShell 7 via winget
- Installs Starship (cross-shell prompt) via winget
- Installs zoxide (directory jumper) via winget
- Downloads and installs JetBrainsMono Nerd Font v3.3.0 (per-user, registry entry)
- Skips anything already installed
- Refreshes PATH between installs
- Prints next steps at the end

</details>

<details>
<summary><b>What verify.ps1 checks</b></summary>

<br>

```
Git, Node.js, Python, PowerShell 7, Starship, Zoxide,
VS Code, GitHub CLI, Docker, Claude Code, Winget, JetBrainsMono NF
```

Each tool gets a PASS/FAIL with version. Exit code 1 if anything fails.

</details>

---

## Repo Templates

New projects get sane defaults from `templates/repo/`:

```
.gitattributes          LF enforcement + binary markers
.claude/settings.json   Read-only Claude permissions (safe default)
CLAUDE.md               Starter project context for Claude Code
```

Copy into any new repo. Customize from there.

---

## Commands Reference

| Command | What it does |
|---------|-------------|
| `pwsh scripts/deploy.ps1` | Deploy all configs via symlinks |
| `pwsh scripts/deploy.ps1 -DryRun` | Preview without changes |
| `pwsh bootstrap/install.ps1` | Install all tools from scratch |
| `pwsh bootstrap/verify.ps1` | Validate all tools are present |
| `yolo` | Toggle NORMAL / YOLO |
| `yolo -Sicko` | Escalate to SICKO (hooks disabled) |
| `yolo -Off` | Return to NORMAL from any level |
| `yolo -Status` | Show current permission mode |

---

## Design Invariants

| Invariant | What it means |
|-----------|--------------|
| **Single Source of Truth** | Configs live in `configs/`. Period. |
| **Idempotent Deployment** | Run `deploy.ps1` 100 times. Same result. |
| **Non-Destructive** | Existing files backed up before replacement. |
| **LF Everywhere** | `.gitattributes` enforces LF. CRLF breaks hooks. |
| **Identity Stays Local** | `~/.gitconfig` user section is never managed. |
| **Bootstrap from Nothing** | Fresh Windows 11 to full config in three commands. |
| **Agent-Friendly** | Parseable output, minimal prompts, no decorative noise. |

---

## Project Structure

```
WINENV/
  bootstrap/
    install.ps1 .............. Fresh-machine tool installation
    verify.ps1 ............... Post-install validation
    winget.dsc.yaml .......... Declarative package manifest
  configs/
    claude/ .................. Claude Code settings, hooks, rules
    git/ ..................... gitconfig, gitignore, gitattributes
    git-bash/ ................ .bashrc, .bash_profile
    mcp/ ..................... MCP server configuration
    powershell/ .............. PS7 profile
    starship/ ................ Cross-shell prompt
    terminal/ ................ Windows Terminal + Tokyo Night
    vscode/ .................. Editor settings + keybindings
  scripts/
    deploy.ps1 ............... Idempotent symlink deployment
    statusline.ps1 ........... Claude Code live metrics
    yolo.ps1 ................. YOLO mode toggle
  templates/ ................. Starter configs for new repos
  docs/ ...................... Architecture and design philosophy
  research/ .................. Original requirements and research
  backups/ ................... Auto-populated by deploy.ps1
```

---

## Safety Model

```
                          +--------------------------+
                          |    yolo.ps1 toggle       |
                          |  (settings.local.json)   |
                          +---+--------+--------+----+
                              |        |        |
                          NORMAL     YOLO     SICKO
                          approve   bypass    bypass
                          prompts   perms     perms
                              |        |        |
                              v        v        |
                          +---+--------+---+    |
                          | PreToolUse     |    |
                          | hook fires     |    |  hooks: {}
                          +-------+--------+    |  (shadowed)
                                  |             |
                          +-------v--------+    |
                          | guard-destruct |    |
                          | ive-bash.sh    |    |
                          | blocks: rm -rf |    |
                          | force push,    |    |
                          | reset --hard,  |    |
                          | DROP TABLE...  |    |
                          +-------+--------+    |
                                  |             |
                                  v             v
                          +-------+-------------+---+
                          |    command executes      |
                          +--------------------------+
```

In NORMAL and YOLO, the guard is structural. In SICKO, the guard is sleeping — you are the safety net.

---

## Theme

**Tokyo Night** everywhere. Terminal. VS Code. Starship accents.
**JetBrainsMono Nerd Font** everywhere. Ligatures. Icons. Consistent rendering.

<details>
<summary><b>Color palette</b></summary>

<br>

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#1A1B26` | Terminal, editor |
| Foreground | `#A9B1D6` | Default text |
| Blue | `#7AA2F7` | Keywords, links |
| Green | `#9ECE6A` | Strings, success |
| Red | `#F7768E` | Errors, deletions |
| Yellow | `#E0AF68` | Warnings, modifications |
| Purple | `#BB9AF7` | Git branch, constants |
| Selection | `#33467C` | Highlighted text |
| Cursor | `#C0CAF5` | Cursor color |

</details>

---

## License

MIT

---

<div align="center">

Built for the workflow where the human holds direction and the AI holds complexity.

</div>
