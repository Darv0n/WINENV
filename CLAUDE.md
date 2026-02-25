# WINENV

AI-augmented Windows 11 developer workstation configuration.

## What This Is

A symlink-deployed config repo that is the Single Source of Truth for all
environment configuration on TrashWizard's daily driver machine.

## Structure

- `bootstrap/` — Fresh-machine provisioning (winget DSC, install, verify)
- `configs/` — All configuration files (deployed via symlink)
- `scripts/` — Deployment engine and utilities
- `templates/` — Starter configs for new repos
- `docs/` — Design philosophy and architecture
- `research/` — Original research documents

## Key Commands

- `scripts/deploy.ps1 -DryRun` — Preview what would be deployed
- `scripts/deploy.ps1` — Deploy all configs via symlinks
- `bootstrap/verify.ps1` — Check all tools are installed and working

## Conventions

- All text files use LF line endings (enforced by `.gitattributes`)
- Configs live in `configs/`, never directly in target locations
- `~/.gitconfig` uses `[include]` — identity stays local, config stays here
- Backups are auto-created before overwriting existing files

## Color Scheme

Tokyo Night everywhere: Windows Terminal, VS Code, starship prompt.

## Font

JetBrainsMono Nerd Font — required for starship icons and terminal ligatures.
