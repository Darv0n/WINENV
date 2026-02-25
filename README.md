# WINENV

AI-augmented Windows 11 developer workstation configuration. Single source of truth
for all environment config, deployed via symlinks.

## Quick Start

```powershell
# 1. Install tools (PS7, starship, zoxide, JetBrainsMono Nerd Font)
powershell -ExecutionPolicy Bypass -File bootstrap\install.ps1

# 2. Restart terminal, then deploy configs
pwsh scripts\deploy.ps1 -DryRun   # preview changes
pwsh scripts\deploy.ps1            # deploy symlinks

# 3. Verify
pwsh bootstrap\verify.ps1
```

## What Gets Deployed

| Config | Target | Mechanism |
|--------|--------|-----------|
| Git Bash (.bashrc, .bash_profile) | `~/.bashrc`, `~/.bash_profile` | Symlink |
| PowerShell 7 profile | `~/Documents/PowerShell/profile.ps1` | Symlink |
| Starship prompt | `~/.config/starship.toml` | Symlink |
| Git config | `~/.gitconfig` | `[include]` directive |
| Git ignore/attributes | `~/.config/git/` | Symlink |
| VS Code settings + keybindings | `AppData/Roaming/Code/User/` | Symlink |
| Windows Terminal settings | WT LocalState | Symlink |
| Claude Code (settings, hooks, rules) | `~/.claude/` | Symlink |

## Architecture

```
Layer 4: AI         Claude Code (settings, hooks, rules, MCP, status line)
Layer 3: Editor     VS Code (settings, keybindings, terminal profiles)
Layer 2: Shell      PS7 + Git Bash (shared starship prompt, zoxide)
Layer 1: Git        gitconfig-winenv (aliases, rerere, push behavior)
Layer 0: Platform   Windows Terminal, winget DSC, JetBrainsMono NF
```

## Design Principles

- **Single Source of Truth** — configs live in `WINENV/configs/`, nowhere else
- **Idempotent** — `deploy.ps1` can be re-run safely any number of times
- **Non-Destructive** — existing files backed up before replacement
- **LF Everywhere** — `.gitattributes` enforces LF (CRLF breaks hooks)
- **Identity Stays Local** — `~/.gitconfig` user/LFS sections are never managed

## Theme

Tokyo Night everywhere. JetBrainsMono Nerd Font for all terminals and editors.

## Project Structure

```
WINENV/
  bootstrap/          # Fresh-machine provisioning
    winget.dsc.yaml   # Declarative package manifest
    install.ps1       # Entry point (PS5-compatible)
    verify.ps1        # Post-install checks
  configs/            # All managed configuration files
    terminal/         # Windows Terminal
    powershell/       # PS7 profile
    git-bash/         # .bashrc, .bash_profile
    git/              # gitconfig, gitignore, gitattributes
    vscode/           # settings, keybindings, extensions list
    claude/           # settings, hooks, rules
    starship/         # starship.toml
    mcp/              # MCP server config
  scripts/
    deploy.ps1        # Symlink deployment engine
    statusline.ps1    # Claude Code status line
  templates/          # Starter configs for new repos
  docs/               # Architecture and design docs
  research/           # Original research documents
  backups/            # Auto-populated by deploy.ps1
```
