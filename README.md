<div align="center">

# WINENV

**AI-augmented Windows 11 developer workstation.**
**One repo. One command. Everything configured.**

`bootstrap` &rarr; `deploy` &rarr; `verify` &rarr; code.

---

[![Windows 11](https://img.shields.io/badge/Windows_11-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](#)
[![PowerShell 7](https://img.shields.io/badge/PowerShell_7-5391FE?style=for-the-badge&logo=powershell&logoColor=white)](#)
[![Claude Code](https://img.shields.io/badge/Claude_Code-191919?style=for-the-badge&logo=anthropic&logoColor=white)](#)
[![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](#)

<br>

![bg](https://img.shields.io/badge/_%20-1A1B26?style=flat-square&logoColor=white)
![fg](https://img.shields.io/badge/foreground-A9B1D6?style=flat-square&logoColor=white)
![blue](https://img.shields.io/badge/blue-7AA2F7?style=flat-square&logoColor=white)
![green](https://img.shields.io/badge/green-9ECE6A?style=flat-square&logoColor=white)
![red](https://img.shields.io/badge/red-F7768E?style=flat-square&logoColor=white)
![yellow](https://img.shields.io/badge/yellow-E0AF68?style=flat-square&logoColor=white)
![purple](https://img.shields.io/badge/purple-BB9AF7?style=flat-square&logoColor=white)
![cyan](https://img.shields.io/badge/cyan-7DCFFF?style=flat-square&logoColor=white)

**Tokyo Night** &bull; **JetBrainsMono Nerd Font**

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

## What It Looks Like

> The terminal, prompt, status line, and mode indicators — all running on Tokyo Night with JetBrainsMono Nerd Font.

### Terminal

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                          ─ □ ×      │
│  ~/projects/WINENV  main >                                         │
│                                                                      │
│  > pwsh scripts/deploy.ps1                                           │
│                                                                      │
│  WINENV Deploy                                                       │
│  ==================================================                  │
│                                                                      │
│  >> Shell configs                                                    │
│     OK: ~/.bashrc -> WINENV/configs/git-bash/.bashrc                 │
│     OK: ~/.bash_profile -> WINENV/configs/git-bash/.bash_profile     │
│     OK: ~/.config/starship.toml -> WINENV/configs/starship/...       │
│                                                                      │
│  >> PowerShell 7 profile                                             │
│     OK: ~/Documents/PowerShell/profile.ps1 -> WINENV/configs/...     │
│                                                                      │
│  >> Git config                                                       │
│     SKIP: Git include already present                                │
│                                                                      │
│  >> Claude Code                                                      │
│     OK: ~/.claude/settings.json -> WINENV/configs/claude/...         │
│     OK: ~/.claude/hooks/guard-destructive-bash.sh -> WINENV/...      │
│     OK: ~/.claude/rules/principles.md -> WINENV/configs/claude/...   │
│                                                                      │
│  ==================================================                  │
│  Deployment complete. Restart terminal to pick up changes.           │
│                                                                      │
│  [main] | claude-opus-4-6 | $2.47 | 18.3k tok | 41% cache          │
└──────────────────────────────────────────────────────────────────────┘
```

### Starship Prompt

```
~/projects/WINENV  main ?1 >
│                    │    │  └── success (green) / error (red)
│                    │    └──── modified files (yellow)
│                    └───────── git branch (purple)
└────────────────────────────── directory, truncated to 3 levels
```

Detects Python and Node.js when project files are present:

```
~/projects/my-api  feature/auth  v20.11.0 >
```

### Permission Mode Indicators

```
 NORMAL                                 ← green, default
 YOLO (bypassPermissions)              ← red, hooks still active
 SICKO (bypassPermissions + hooks off) ← magenta, you are the safety net
```

### Claude Code Status Line

Live metrics at the bottom of every Claude session:

```
[main] | claude-opus-4-6 | $12.34 | 45.2k tok | 23% cache
  │           │              │          │           └── cache hit rate
  │           │              │          └────────────── token count
  │           │              └───────────────────────── session cost
  │           └──────────────────────────────────────── active model
  └──────────────────────────────────────────────────── git branch
```

### Verify Output

```
 > pwsh bootstrap/verify.ps1

 WINENV Verification
 ==================================================

   PASS: Git 2.47.1
   PASS: Node.js v20.11.0
   PASS: Python 3.12.4
   PASS: PowerShell 7.4.6
   PASS: Starship 1.21.1
   PASS: Zoxide 0.9.6
   PASS: VS Code 1.96.0
   PASS: GitHub CLI 2.62.0
   PASS: Claude Code 1.0.16
   PASS: Winget v1.9.25180
   PASS: JetBrainsMono Nerd Font

 ==================================================
 All checks passed.
```

---

## Architecture

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  Layer 4   AI Agent                                             │
 │  ┌───────────────────────────────────────────────────────────┐  │
 │  │  Claude Code settings ─ hooks ─ rules ─ MCP ─ statusline │  │
 │  └───────────────────────────────────────────────────────────┘  │
 │  Layer 3   Editor                                               │
 │  ┌───────────────────────────────────────────────────────────┐  │
 │  │  VS Code settings ─ keybindings ─ terminal profiles       │  │
 │  └───────────────────────────────────────────────────────────┘  │
 │  Layer 2   Shell                                                │
 │  ┌───────────────────────────────────────────────────────────┐  │
 │  │  PowerShell 7 ─ Git Bash ─ Starship prompt ─ Zoxide      │  │
 │  └───────────────────────────────────────────────────────────┘  │
 │  Layer 1   Git                                                  │
 │  ┌───────────────────────────────────────────────────────────┐  │
 │  │  gitconfig-winenv ─ aliases ─ rerere ─ push defaults      │  │
 │  └───────────────────────────────────────────────────────────┘  │
 │  Layer 0   Platform                                             │
 │  ┌───────────────────────────────────────────────────────────┐  │
 │  │  Windows Terminal ─ winget DSC ─ JetBrainsMono Nerd Font  │  │
 │  └───────────────────────────────────────────────────────────┘  │
 └─────────────────────────────────────────────────────────────────┘
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

A `PreToolUse` hook intercepts every Bash command Claude tries to run:

```
 ┌─ guard-destructive-bash.sh ───────────────────────────────────────┐
 │                                                                    │
 │  BLOCKED    rm -rf                  recursive force delete         │
 │  BLOCKED    git push --force        history rewrite                │
 │  BLOCKED    git reset --hard        discard uncommitted work       │
 │  BLOCKED    git clean -f            nuke untracked files           │
 │  BLOCKED    git branch -D           force-delete branch            │
 │  BLOCKED    git checkout .          discard working tree           │
 │  BLOCKED    DROP DATABASE/TABLE     destructive SQL                │
 │                                                                    │
 └────────────────────────────────────────────────────────────────────┘
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

```
  ┌────────────┐        ┌────────────┐        ┌────────────┐
  │   NORMAL   │ yolo   │    YOLO    │-Sicko  │   SICKO    │
  │            │───────>│            │───────>│            │
  │  approve   │        │  bypass    │        │  bypass    │
  │  prompts   │        │  perms     │        │  perms     │
  │  hooks: ON │        │  hooks: ON │        │  hooks: OFF│
  └────────────┘        └────────────┘        └────────────┘
        ^                                           │
        │              -Off from any level           │
        └───────────────────────────────────────────┘
```

| Mode | Permissions | Hooks | When to use |
|------|------------|-------|-------------|
| ![normal](https://img.shields.io/badge/NORMAL-9ECE6A?style=flat-square&logoColor=white) | Per-tool approval | Active | Default. Learning a codebase, reviewing agent output. |
| ![yolo](https://img.shields.io/badge/YOLO-F7768E?style=flat-square&logoColor=white) | Bypass all | **Still active** | You trust the agent. Move fast. Guard has your back. |
| ![sicko](https://img.shields.io/badge/SICKO-BB9AF7?style=flat-square&logoColor=white) | Bypass all | **Disabled** | Deep system work. Registry, drivers, infra. You are the safety net. |

<details>
<summary><b>How it works under the hood</b></summary>

<br>

Both modes manipulate `~/.claude/settings.local.json`, which overrides `settings.json` at the project level.

**YOLO** writes:
```json
{
  "permissions": { "defaultMode": "bypassPermissions" }
}
```
Hooks in `settings.json` still fire because the local override only covers permissions.

**SICKO** writes:
```json
{
  "permissions": { "defaultMode": "bypassPermissions" },
  "hooks": {}
}
```
The empty `hooks` object at the local level shadows the shared hooks entirely. The guard is sleeping.

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
 ┌─ Git ──────────────────────┐  ┌─ Navigation ──────────────┐
 │  gs   git status           │  │  proj   cd ~/projects     │
 │  ga   git add              │  │  apps   cd ~/projects/apps│
 │  gc   git commit           │  │  z ..   zoxide jump       │
 │  gp   git push             │  └───────────────────────────┘
 │  gl   git log --oneline    │  ┌─ Tools ────────────────────┐
 │  gd   git diff             │  │  yolo   permission toggle  │
 │  gco  git checkout         │  │  ll     ls -la             │
 │  gb   git branch           │  │  la     ls -A              │
 └────────────────────────────┘  └────────────────────────────┘
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

```
 ┌─ PSReadLine ────────────────────────────────────────────────┐
 │                                                              │
 │  Up/Down     search history by prefix (type "git" + Up)     │
 │  Tab         cycle through completions (MenuComplete)        │
 │  Prediction  inline suggestions from command history         │
 │                                                              │
 └──────────────────────────────────────────────────────────────┘
```

---

## VS Code

<details>
<summary><b>Editor settings</b></summary>

<br>

```
 ┌─ Editor ──────────────────────────────────────────────┐
 │                                                        │
 │  Font          JetBrainsMono Nerd Font, 13pt           │
 │  Ligatures     enabled                                 │
 │  Theme         Tokyo Night                             │
 │  Tab size      2 spaces (4 for Python)                 │
 │  Line endings  LF enforced                             │
 │  Format        on save (critical for AI output)        │
 │  Auto-save     on focus change                         │
 │  Minimap       off                                     │
 │  Preview       off (files open, not preview)           │
 │  Trim          trailing whitespace + final newlines    │
 │                                                        │
 └────────────────────────────────────────────────────────┘
```

</details>

<details>
<summary><b>Keybindings</b></summary>

<br>

```
 ┌─ Keybindings ─────────────────────────────────────────┐
 │                                                        │
 │  Alt + ;       toggle focus: editor <-> terminal       │
 │  Alt + J / K   previous / next editor tab              │
 │  Alt + B       toggle sidebar                          │
 │  Alt + P       toggle panel                            │
 │                                                        │
 └────────────────────────────────────────────────────────┘
```

Designed to minimize mouse usage during AI-supervised coding sessions.

</details>

<details>
<summary><b>Terminal profiles</b></summary>

<br>

```
 ┌─ Terminal Profiles ───────────────────────────────────┐
 │                                                        │
 │  PowerShell 7   pwsh.exe -NoLogo          (default)   │
 │  Git Bash       bash.exe --login -i                    │
 │  Command Prompt cmd.exe                   (fallback)   │
 │                                                        │
 │  All start in ~/projects                               │
 │  All use JetBrainsMono Nerd Font                       │
 │  All use Tokyo Night color scheme                      │
 │                                                        │
 └────────────────────────────────────────────────────────┘
```

</details>

---

## Git Configuration

<details>
<summary><b>Behavior (managed by WINENV)</b></summary>

<br>

```
 ┌─ Git Behavior ────────────────────────────────────────────────┐
 │                                                                │
 │  push.default          current     push current branch only    │
 │  push.autoSetupRemote  true        auto-track on first push    │
 │  pull.rebase           true        linear history preferred     │
 │  fetch.prune           true        auto-delete stale remotes   │
 │  merge.conflictstyle   diff3       original + current + theirs │
 │  rerere.enabled        true        record & replay resolutions │
 │  diff.colorMoved       default     highlight moved code blocks │
 │  core.autocrlf         false       LF via .gitattributes only  │
 │  core.editor           code --wait                              │
 │                                                                │
 └────────────────────────────────────────────────────────────────┘
```

</details>

<details>
<summary><b>Git aliases</b></summary>

<br>

```
 ┌─ Git Aliases ─────────────────────────────────────────────────┐
 │                                                                │
 │  git st        status                                          │
 │  git co        checkout                                        │
 │  git br        branch                                          │
 │  git ci        commit                                          │
 │  git lg        log --oneline --graph --decorate -20            │
 │  git last      log -1 HEAD                                     │
 │  git unstage   reset HEAD --                                   │
 │  git amend     commit --amend --no-edit                        │
 │  git wip       !git add -A && git commit -m 'WIP'             │
 │                                                                │
 └────────────────────────────────────────────────────────────────┘
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
 ┌─ Fresh Machine to Full Config ────────────────────────────────┐
 │                                                                │
 │  1. powershell install.ps1    PS7, Starship, Zoxide, Font     │
 │  2. restart terminal          pick up new PATH + fonts         │
 │  3. pwsh deploy.ps1 -DryRun  preview all symlinks             │
 │  4. pwsh deploy.ps1           deploy everything                │
 │  5. restart terminal          load new profiles                │
 │  6. pwsh verify.ps1           confirm all tools versioned      │
 │  7. code .                    done                             │
 │                                                                │
 └────────────────────────────────────────────────────────────────┘
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
 ┌─ templates/repo/ ─────────────────────────────────────────────┐
 │                                                                │
 │  .gitattributes          LF enforcement + binary markers       │
 │  .claude/settings.json   read-only Claude perms (safe default) │
 │  CLAUDE.md               starter project context               │
 │                                                                │
 └────────────────────────────────────────────────────────────────┘
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

## Safety Model

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                        yolo.ps1 toggle                           │
  │                    (settings.local.json)                          │
  │                                                                  │
  │     NORMAL              YOLO                SICKO                │
  │  ┌──────────┐       ┌──────────┐        ┌──────────┐            │
  │  │ approve  │ yolo  │ bypass   │ -Sicko │ bypass   │            │
  │  │ prompts  │──────>│ perms    │───────>│ perms    │            │
  │  │          │       │          │        │          │            │
  │  │ hooks:ON │       │ hooks:ON │        │ hooks:OFF│            │
  │  └──────────┘       └──────────┘        └──────────┘            │
  │       ^                                      │                   │
  │       │           -Off from any level         │                   │
  │       └──────────────────────────────────────┘                   │
  │                                                                  │
  │  ┌───────────────────────────────────────┐                       │
  │  │         PreToolUse hook fires         │  <- NORMAL + YOLO     │
  │  │    guard-destructive-bash.sh active   │                       │
  │  │    blocks: rm -rf, force push,        │     SICKO: hooks      │
  │  │    reset --hard, DROP TABLE...        │     shadowed by {}    │
  │  └───────────────────────────────────────┘                       │
  │                                                                  │
  │  In NORMAL and YOLO, the guard is structural.                    │
  │  In SICKO, the guard is sleeping — you are the safety net.       │
  └──────────────────────────────────────────────────────────────────┘
```

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
    yolo.ps1 ................. Permission mode toggle
  templates/ ................. Starter configs for new repos
  docs/ ...................... Architecture and design philosophy
  research/ .................. Original requirements and research
  backups/ ................... Auto-populated by deploy.ps1
```

---

## Theme

<div align="center">

### Tokyo Night

![bg](https://img.shields.io/badge/Background__%231A1B26-1A1B26?style=for-the-badge)
![fg](https://img.shields.io/badge/Foreground__%23A9B1D6-A9B1D6?style=for-the-badge)

![blue](https://img.shields.io/badge/Blue__%237AA2F7-7AA2F7?style=for-the-badge&logoColor=white)
![green](https://img.shields.io/badge/Green__%239ECE6A-9ECE6A?style=for-the-badge&logoColor=white)
![red](https://img.shields.io/badge/Red__%23F7768E-F7768E?style=for-the-badge&logoColor=white)
![yellow](https://img.shields.io/badge/Yellow__%23E0AF68-E0AF68?style=for-the-badge&logoColor=white)

![purple](https://img.shields.io/badge/Purple__%23BB9AF7-BB9AF7?style=for-the-badge&logoColor=white)
![cyan](https://img.shields.io/badge/Cyan__%237DCFFF-7DCFFF?style=for-the-badge&logoColor=white)
![selection](https://img.shields.io/badge/Selection__%2333467C-33467C?style=for-the-badge&logoColor=white)
![cursor](https://img.shields.io/badge/Cursor__%23C0CAF5-C0CAF5?style=for-the-badge&logoColor=white)

</div>

Applied to: Windows Terminal, VS Code, Starship prompt accents.

**JetBrainsMono Nerd Font** — ligatures, powerline icons, consistent rendering across every surface.

---

## License

MIT

---

<div align="center">

Built for the workflow where the human holds direction and the AI holds complexity.

</div>
