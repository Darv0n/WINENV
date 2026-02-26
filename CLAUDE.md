# WINENV

AI-augmented Windows 11 developer workstation configuration.
Symlink-deployed config repo — Single Source of Truth for all environment
configuration on this machine.

## Structure

```
bootstrap/          Fresh-machine provisioning (install.ps1, verify.ps1, winget DSC)
configs/            All configuration files (deployed via symlink)
  claude/           settings.json, hooks, rules, CLAUDE.md (global)
  git/              gitconfig-winenv, gitignore-global, gitattributes-global
  git-bash/         .bashrc, .bash_profile
  powershell/       profile.ps1 (PSReadLine, aliases, starship)
  starship/         starship.toml (shared prompt for PS7 + Bash)
  terminal/         Windows Terminal settings.json (Tokyo Night)
  vscode/           settings.json, keybindings.json, extensions.txt
  mcp/              .mcp.json (context7, filesystem)
scripts/            deploy.ps1, statusline.ps1, yolo.ps1
templates/repo/     Starter configs for new project repos
docs/               architecture.md, manifesto.md, cheatsheet.md
research/           Original design documents
```

## Commands

| Command | What it does |
|---------|--------------|
| `scripts/deploy.ps1 -DryRun` | Preview symlink deployment |
| `scripts/deploy.ps1` | Deploy all configs via symlinks |
| `bootstrap/install.ps1` | Install all tools (fresh machine) |
| `bootstrap/verify.ps1` | Validate 13 tools installed and working |
| `yolo` | Toggle NORMAL <> YOLO permission mode |
| `yolo -Sicko` | Escalate to SICKO (hooks disabled) |
| `yolo -Off` | Return to NORMAL from any level |

## Deployment Model

Configs in `configs/` are the canonical source. `deploy.ps1` creates symlinks
from target locations back to this repo. Never copy configs to target locations.

- Git config uses `[include]` — identity stays in `~/.gitconfig`, managed config
  lives here in `configs/git/gitconfig-winenv`
- Existing files are auto-backed up to `backups/` before replacement
- Deployment is idempotent — safe to run repeatedly

## Permission Modes

| Mode | Permissions | Hooks | When |
|------|-------------|-------|------|
| NORMAL | Per-tool approval | Active | Default, learning a codebase |
| YOLO | Bypass all | Active | Trusted agent workflow |
| SICKO | Bypass all | Disabled | Deep system work, you are the safety net |

The destructive command guard (`configs/claude/hooks/guard-destructive-bash.sh`)
blocks `rm -rf`, `git push --force`, `git reset --hard`, `git clean -f`,
`git branch -D`, `git checkout .`, and `DROP DATABASE/TABLE` — even in YOLO mode.
Only SICKO disables it.

## Conventions

- LF line endings everywhere — enforced by `.gitattributes`. CRLF breaks bash
  scripts and Claude hooks. This is non-negotiable.
- Configs live in `configs/`, never directly in target locations.
- Backups are auto-created before overwriting existing files.
- Tokyo Night color scheme across all tools (terminal, VS Code, starship).
- JetBrainsMono Nerd Font — required for starship icons and terminal ligatures.

## Design Invariants

1. **Single Source of Truth** — Every config lives in `configs/`. Symlinks, never copies.
2. **Idempotent Deployment** — `deploy.ps1` produces identical state on every run.
3. **Non-Destructive** — Auto-backup before replacement. `--DryRun` always available.
4. **Identity Stays Local** — `~/.gitconfig` is never fully managed. `[include]` only.
5. **Bootstrap from Nothing** — Fresh Windows 11 to full config in 3 commands.
6. **Agent-Friendly** — Single-line prompts, parseable output, no decorative noise.

## Working on This Repo

When editing configs here, remember the symlink relationship:
- Changes to files in `configs/` take effect immediately at their target locations
  (the symlink means they're the same file)
- After adding a NEW config file, `deploy.ps1` must be run to create the symlink
- Test changes in the target tool before committing
- If a config breaks something, the backup in `backups/` has the previous version
