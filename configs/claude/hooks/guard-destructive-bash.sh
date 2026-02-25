#!/bin/bash
# Guard hook: blocks destructive Bash commands before execution.
# Registered as a PreToolUse command hook on the Bash tool.
# Exit 0 = allow, Exit 2 + stderr JSON = deny.

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || command=""

# Empty or unparseable command — nothing to guard
if [[ -z "$command" ]]; then
  exit 0
fi

# --- Destructive patterns ---

# Recursive force delete
if [[ "$command" =~ rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f|rm[[:space:]]+-[a-zA-Z]*f[a-zA-Z]*r ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: rm -rf detected. This is irreversible. Ask the user before proceeding."}' >&2
  exit 2
fi

# Force push
if [[ "$command" =~ git[[:space:]]+push[[:space:]]+--force|git[[:space:]]+push[[:space:]]+-f[[:space:]] ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: git push --force detected. This rewrites remote history. Ask the user before proceeding."}' >&2
  exit 2
fi

# Hard reset
if [[ "$command" =~ git[[:space:]]+reset[[:space:]]+--hard ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: git reset --hard detected. This discards uncommitted changes. Ask the user before proceeding."}' >&2
  exit 2
fi

# Force clean
if [[ "$command" =~ git[[:space:]]+clean[[:space:]]+-[a-zA-Z]*f ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: git clean -f detected. This removes untracked files permanently. Ask the user before proceeding."}' >&2
  exit 2
fi

# Force delete branch
if [[ "$command" =~ git[[:space:]]+branch[[:space:]]+-D ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: git branch -D detected. This force-deletes a branch. Ask the user before proceeding."}' >&2
  exit 2
fi

# Discard all working tree changes
if [[ "$command" =~ git[[:space:]]+checkout[[:space:]]+\. ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: git checkout . detected. This discards all unstaged changes. Ask the user before proceeding."}' >&2
  exit 2
fi

# Drop database (SQL)
if [[ "$command" =~ DROP[[:space:]]+DATABASE|DROP[[:space:]]+TABLE|TRUNCATE[[:space:]]+TABLE ]]; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"BLOCKED: Destructive SQL detected. Ask the user before proceeding."}' >&2
  exit 2
fi

# All clear
exit 0
