# WINENV Git Bash interactive config
# Deployed via symlink from WINENV/configs/git-bash/.bashrc

# --- Winpty wrapper (Windows terminal compatibility) ---
# Wraps commands that need a proper TTY on Windows
for cmd in python ipython node php psql mysql; do
    alias $cmd="winpty $cmd"
done

# --- Git aliases ---
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline -20'
alias gd='git diff'
alias gco='git checkout'
alias gb='git branch'

# --- Navigation ---
alias proj='cd /c/Users/doubl/projects'
alias apps='cd /c/Users/doubl/projects/apps'

# --- WINENV tools ---
alias new-project='/c/Users/doubl/projects/apps/WINENV/scripts/new-project'
alias yolo='pwsh /c/Users/doubl/projects/apps/WINENV/scripts/yolo.ps1'
alias ll='ls -la --color=auto'
alias la='ls -A --color=auto'

# --- GitHub ---
export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"

# --- Path ---
export PATH="$HOME/anaconda3:$HOME/anaconda3/Scripts:$HOME/.local/bin:$PATH"

# --- Zoxide ---
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init bash)"
fi

# --- Starship prompt (must be last) ---
if command -v starship &> /dev/null; then
    eval "$(starship init bash)"
fi
