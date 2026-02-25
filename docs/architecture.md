# WINENV Architecture

## Layered Systems

```
Layer 4: AI Integration
  Claude Code (settings, hooks, rules, MCP, status line)

Layer 3: Editor
  VS Code (settings, keybindings, terminal profiles)

Layer 2: Shell
  PowerShell 7 (PSReadLine, aliases, conda)
  Git Bash (.bashrc, aliases, winpty)
  Starship (prompt theme — shared by both shells)
  Zoxide (directory jumper — shared by both shells)

Layer 1: Git Safety
  gitconfig-winenv (aliases, rerere, push behavior)
  gitignore-global (OS/editor/runtime ignores)
  gitattributes-global (LF enforcement for .sh)

Layer 0: Platform
  Windows Terminal (profiles, font, color scheme)
  Winget DSC (package manifest)
  JetBrainsMono Nerd Font
```

## Deployment Flow

```
WINENV/configs/  ──symlink──>  Target locations (~/.bashrc, AppData, etc.)
                               │
WINENV/configs/git/  ──include──>  ~/.gitconfig [include] directive
                               │
WINENV/bootstrap/  ──one-time──>  Package installation (winget, fonts)
```

## Config Ownership

| Domain          | Managed By  | Mechanism   |
|-----------------|-------------|-------------|
| Shell prompts   | starship    | starship.toml → ~/.config/starship.toml |
| Shell behavior  | .bashrc / profile.ps1 | Symlinks to home |
| Git behavior    | gitconfig-winenv | [include] from ~/.gitconfig |
| Git ignores     | gitignore-global | ~/.config/git/ignore |
| Editor          | VS Code settings | Symlink to AppData |
| AI agent        | Claude configs | Symlinks to ~/.claude/ |
| Terminal        | WT settings.json | Symlink to WT LocalState |
| Packages        | winget DSC  | One-time bootstrap |
