<div align="center">

# WINENV

**AI-augmented Windows 11 developer workstation.**
**One repo. One command. Everything configured.**

<br>

[![Windows 11](https://img.shields.io/badge/Windows_11-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](#architecture)
[![PowerShell 7](https://img.shields.io/badge/PowerShell_7-5391FE?style=for-the-badge&logo=powershell&logoColor=white)](#shell-environment)
[![Claude Code](https://img.shields.io/badge/Claude_Code-191919?style=for-the-badge&logo=anthropic&logoColor=white)](#claude-code)
[![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](#vs-code)
[![Starship](https://img.shields.io/badge/Starship-DD0B78?style=for-the-badge&logo=starship&logoColor=white)](#starship-prompt)

<br>

> Single source of truth for every config on the machine.<br>
> Change it here, it changes everywhere. No manual sync. No drift.

</div>

<br>

## Quick Start

```powershell
powershell -ExecutionPolicy Bypass -File bootstrap\install.ps1   # 1. install tools
# restart terminal
pwsh scripts\deploy.ps1                                          # 2. deploy configs
pwsh bootstrap\verify.ps1                                        # 3. verify
```

**[Cheatsheet &rarr;](docs/cheatsheet.md)** &mdash; copy-paste combos for every workflow, basic to S-tier.

---

## Architecture

```
Layer 4  AI Agent     Claude Code  ·  settings  ·  hooks  ·  rules  ·  MCP  ·  status line
Layer 3  Editor       VS Code  ·  settings  ·  keybindings  ·  terminal profiles
Layer 2  Shell        PowerShell 7  ·  Git Bash  ·  Starship prompt  ·  Zoxide
Layer 1  Git          gitconfig  ·  aliases  ·  rerere  ·  push defaults  ·  ignore/attributes
Layer 0  Platform     Windows Terminal  ·  winget DSC  ·  JetBrainsMono Nerd Font
```

Each layer builds on the one below. `deploy.ps1` handles all of them in one pass.

---

## What Gets Deployed

| Config | Target | Method |
|--------|--------|--------|
| PowerShell 7 profile | `~/Documents/PowerShell/profile.ps1` | Symlink |
| Git Bash | `~/.bashrc`, `~/.bash_profile` | Symlink |
| Starship prompt | `~/.config/starship.toml` | Symlink |
| Git config | `~/.gitconfig` | `[include]` directive |
| Git ignore + attributes | `~/.config/git/` | Symlink |
| VS Code settings + keybindings | `%APPDATA%/Code/User/` | Symlink |
| Windows Terminal | WT `LocalState/settings.json` | Symlink |
| Claude Code (settings, hooks, rules) | `~/.claude/` | Symlink |

<details>
<summary><b>Why symlinks? Why [include] for git?</b></summary>

<br>

**Symlinks** mean you edit configs in WINENV and they're live everywhere instantly. `git pull` updates your entire workstation.

**`[include]`** for git keeps your `~/.gitconfig` identity (`[user]`, LFS) untouched. WINENV manages behavior only — aliases, rerere, push defaults. Clean separation.

</details>

---

## Claude Code

WINENV treats Claude Code as infrastructure, not an afterthought.

### Status Line

Live session metrics at the bottom of every Claude session:

```
[main] | claude-opus-4-6 | $2.47 | 18.3k tok | 41% cache
```

Git branch, model, cost, tokens, cache hit rate. Zero overhead.

### Destructive Command Guard

A `PreToolUse` hook intercepts every Bash command Claude runs. These get blocked:

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete |
| `git push --force` | History rewrite |
| `git reset --hard` | Discard uncommitted work |
| `git clean -f` | Nuke untracked files |
| `git branch -D` | Force-delete branch |
| `git checkout .` | Discard working tree |
| `DROP DATABASE / TABLE` | Destructive SQL |

The hook fires **even in YOLO mode**. Go fast without going off a cliff.

### Permission Modes

Three escalation levels. One command.

```powershell
yolo              # toggle NORMAL <-> YOLO
yolo -Sicko       # escalate to SICKO
yolo -Off         # return to NORMAL from any level
yolo -Status      # check current mode
```

| | Mode | Permissions | Hooks | Use case |
|-|------|------------|-------|----------|
| ![n](https://img.shields.io/badge/_-9ECE6A?style=flat-square) | **NORMAL** | Per-tool approval | Active | Learning a codebase, reviewing output |
| ![y](https://img.shields.io/badge/_-F7768E?style=flat-square) | **YOLO** | Bypass all | **Still active** | Trust the agent. Guard has your back. |
| ![s](https://img.shields.io/badge/_-BB9AF7?style=flat-square) | **SICKO** | Bypass all | **Disabled** | Deep system work. You are the safety net. |

<details>
<summary><b>How the escalation works</b></summary>

<br>

```
NORMAL ──yolo──> YOLO ──-Sicko──> SICKO
  ^                                  │
  └──────────-Off from any level─────┘
```

Both modes write to `~/.claude/settings.local.json` (overrides `settings.json` at the project level):

**YOLO** writes `bypassPermissions`. Hooks in `settings.json` still fire because the local override only touches permissions.

**SICKO** writes `bypassPermissions` + `"hooks": {}`. The empty hooks object shadows the shared hooks entirely — the guard is sleeping.

Your original `settings.local.json` is backed up to `.pre-yolo` on first escalation and restored on `-Off`. Auto-toggle from any elevated mode goes straight back to NORMAL.

</details>

<details>
<summary><b>Operating principles (auto-loaded every session)</b></summary>

<br>

Ten principles load into every Claude session via `rules/principles.md`:

1. **Redistribution Over Removal** — Move capabilities, don't delete them
2. **Explicit State Over Implicit Context** — Write to artifacts; context degrades at boundaries
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

Both shells get the same aliases, the same prompt, and the same navigation. Switching is seamless.

### Starship Prompt

Single-line, shared across PowerShell 7 and Git Bash:

```
~/projects/WINENV  main ?1 >
```

Directory (3 levels) + git branch + status indicators + language versions when detected. Agent-friendly — no decorative noise.

### Aliases

| Alias | Command | | Alias | Command |
|-------|---------|--|-------|---------|
| `gs` | `git status` | | `proj` | `cd ~/projects` |
| `ga` | `git add` | | `apps` | `cd ~/projects/apps` |
| `gc` | `git commit` | | `yolo` | permission mode toggle |
| `gp` | `git push` | | `ll` | `ls -la` |
| `gl` | `git log --oneline -20` | | `la` | `ls -A` |
| `gd` | `git diff` | | `z` | zoxide jump |
| `gco` | `git checkout` |
| `gb` | `git branch` |

<details>
<summary><b>PSReadLine (PowerShell)</b></summary>

<br>

| Key | Behavior |
|-----|----------|
| **Up / Down** | Search history by prefix — type `git` then press Up |
| **Tab** | Cycle through completions (MenuComplete) |
| **Prediction** | Inline suggestions from command history |

</details>

<details>
<summary><b>Zoxide</b></summary>

<br>

Smart directory jumping. `z projects` from anywhere. Learns from your `cd` history. Replaces `cd` muscle memory with something faster.

</details>

---

## VS Code

<details>
<summary><b>Editor</b></summary>

<br>

| Setting | Value |
|---------|-------|
| Font | JetBrainsMono Nerd Font, 13pt, ligatures |
| Theme | Tokyo Night |
| Tab size | 2 spaces (4 for Python) |
| Line endings | LF enforced |
| Format on save | Yes (critical for AI output) |
| Auto-save | On focus change |
| Minimap | Off |
| Preview mode | Off — files open directly |

</details>

<details>
<summary><b>Keybindings</b></summary>

<br>

| Shortcut | Action |
|----------|--------|
| `Alt+;` | Toggle focus: editor / terminal |
| `Alt+J` / `Alt+K` | Previous / next tab |
| `Alt+B` | Toggle sidebar |
| `Alt+P` | Toggle panel |

Minimize mouse during AI-supervised sessions.

</details>

<details>
<summary><b>Terminal profiles</b></summary>

<br>

| Profile | Command | Default |
|---------|---------|---------|
| PowerShell 7 | `pwsh.exe -NoLogo` | Yes |
| Git Bash | `bash.exe --login -i` | |
| Command Prompt | `cmd.exe` | Fallback |

All start in `~/projects`. Same font. Same theme.

</details>

---

## Git

<details>
<summary><b>Behavior</b></summary>

<br>

| Setting | Value | Why |
|---------|-------|-----|
| `push.default` | `current` | Push current branch only |
| `push.autoSetupRemote` | `true` | Auto-track on first push |
| `pull.rebase` | `true` | Linear history |
| `fetch.prune` | `true` | Auto-delete stale remotes |
| `merge.conflictstyle` | `diff3` | Show original + current + incoming |
| `rerere.enabled` | `true` | Record and replay conflict resolutions |
| `diff.colorMoved` | `default` | Highlight moved code blocks |
| `core.autocrlf` | `false` | LF via `.gitattributes`, not conversion |

</details>

<details>
<summary><b>Git aliases</b></summary>

<br>

| Alias | Expands to |
|-------|-----------|
| `git st` | `status` |
| `git co` | `checkout` |
| `git br` | `branch` |
| `git ci` | `commit` |
| `git lg` | `log --oneline --graph --decorate -20` |
| `git last` | `log -1 HEAD` |
| `git unstage` | `reset HEAD --` |
| `git amend` | `commit --amend --no-edit` |
| `git wip` | `!git add -A && git commit -m 'WIP'` |

</details>

<details>
<summary><b>Global ignore</b></summary>

<br>

OS files, editor artifacts, Python/Node build outputs, env files (`.env`, `*.pem`, `*.key`), Claude Code ephemeral state, common build dirs. [Full list &rarr;](configs/git/gitignore-global)

</details>

---

## Bootstrap

From a fresh Windows 11 with just PowerShell 5.1 and winget:

| Step | Command | What happens |
|------|---------|-------------|
| 1 | `powershell bootstrap\install.ps1` | Installs PS7, Starship, Zoxide, JetBrainsMono NF |
| 2 | Restart terminal | PATH + font registration |
| 3 | `pwsh scripts\deploy.ps1 -DryRun` | Preview all symlinks |
| 4 | `pwsh scripts\deploy.ps1` | Deploy everything |
| 5 | Restart terminal | Load profiles |
| 6 | `pwsh bootstrap\verify.ps1` | Confirm all tools |

<details>
<summary><b>What install.ps1 does</b></summary>

<br>

- Installs PowerShell 7, Starship, zoxide via winget
- Downloads JetBrainsMono Nerd Font v3.3.0 from GitHub, installs per-user with registry entry
- Skips anything already installed
- Refreshes PATH between installs

</details>

<details>
<summary><b>What verify.ps1 checks</b></summary>

<br>

Git, Node.js, Python, PowerShell 7, Starship, Zoxide, VS Code, GitHub CLI, Docker, Claude Code, Winget, JetBrainsMono NF.

Each tool gets PASS/FAIL with version. Exit code 1 if any fail.

</details>

---

## Templates

Starter configs for new repos in `templates/repo/`:

| File | Purpose |
|------|---------|
| `.gitattributes` | LF enforcement + binary markers |
| `.claude/settings.json` | Read-only Claude permissions (safe default) |
| `CLAUDE.md` | Starter project context for Claude Code |

---

## Commands

| Command | What it does |
|---------|-------------|
| `pwsh scripts/deploy.ps1` | Deploy all configs via symlinks |
| `pwsh scripts/deploy.ps1 -DryRun` | Preview without changes |
| `pwsh bootstrap/install.ps1` | Install all tools from scratch |
| `pwsh bootstrap/verify.ps1` | Validate tools are present |
| `yolo` | Toggle NORMAL / YOLO |
| `yolo -Sicko` | Escalate to SICKO |
| `yolo -Off` | Return to NORMAL |
| `yolo -Status` | Show current mode |

---

## Design Invariants

| Invariant | Meaning |
|-----------|---------|
| **Single Source of Truth** | Configs live in `configs/`. Period. |
| **Idempotent** | Run `deploy.ps1` 100 times. Same result. |
| **Non-Destructive** | Existing files backed up before replacement. |
| **LF Everywhere** | `.gitattributes` enforces LF. CRLF breaks hooks. |
| **Identity Stays Local** | `~/.gitconfig` user section is never touched. |
| **Bootstrap from Nothing** | Fresh Windows 11 &rarr; full config in three commands. |
| **Agent-Friendly** | Parseable output. No decorative noise. |

---

## Theme

<div align="center">

### Tokyo Night

<br>

![](https://img.shields.io/badge/bg%20%231A1B26-1A1B26?style=for-the-badge)
![](https://img.shields.io/badge/fg%20%23A9B1D6-A9B1D6?style=for-the-badge)
![](https://img.shields.io/badge/blue%20%237AA2F7-7AA2F7?style=for-the-badge)
![](https://img.shields.io/badge/green%20%239ECE6A-9ECE6A?style=for-the-badge)
![](https://img.shields.io/badge/red%20%23F7768E-F7768E?style=for-the-badge)
![](https://img.shields.io/badge/yellow%20%23E0AF68-E0AF68?style=for-the-badge)
![](https://img.shields.io/badge/purple%20%23BB9AF7-BB9AF7?style=for-the-badge)
![](https://img.shields.io/badge/cyan%20%237DCFFF-7DCFFF?style=for-the-badge)

<br>

Applied everywhere: **Windows Terminal** &bull; **VS Code** &bull; **Starship prompt**

**JetBrainsMono Nerd Font** &mdash; ligatures, powerline icons, consistent rendering.

</div>

---

## Project Structure

```
WINENV/
  bootstrap/
    install.ps1           fresh-machine tool installation
    verify.ps1            post-install validation
    winget.dsc.yaml       declarative package manifest
  configs/
    claude/               settings, hooks, rules
    git/                  gitconfig, gitignore, gitattributes
    git-bash/             .bashrc, .bash_profile
    mcp/                  MCP server configuration
    powershell/           PS7 profile
    starship/             cross-shell prompt
    terminal/             Windows Terminal + Tokyo Night
    vscode/               editor settings + keybindings
  scripts/
    deploy.ps1            idempotent symlink deployment
    statusline.ps1        Claude Code live metrics
    yolo.ps1              permission mode toggle
  templates/              starter configs for new repos
  docs/                   architecture and design philosophy
  research/               original requirements and research
  backups/                auto-populated by deploy.ps1
```

---

<div align="center">

MIT &bull; Built for the workflow where the human holds direction and the AI holds complexity.

</div>
