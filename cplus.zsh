#!/usr/bin/env zsh
# cplus - Prompt composition tool for Claude CLI
# See cplus_contract.md for specification

set -e

# Determine script location and prompts directory
# When installed: ~/.config/cplus/cplus.zsh with prompts at ~/.config/cplus/prompts/
# When in repo: scripts/cplus.zsh with prompts at ../prompts/
SCRIPT_DIR="${0:A:h}"

# Look for prompts in script directory first (installed location)
if [ -d "$SCRIPT_DIR/prompts" ]; then
    PROMPTS_DIR="$SCRIPT_DIR/prompts"
else
    # Fallback to parent directory (repo location)
    PROMPTS_DIR="${SCRIPT_DIR:h}/prompts"
fi

# Print help text
show_help() {
  cat << 'EOF'
cplus - Prompt composition tool for Claude CLI

SYNOPSIS
  cplus [operation] [prompt_selector] [options] [extras...]

OPERATIONS
  run (default)  Build a composed prompt and pipe it to claude
  pick           Force interactive selection of action prompt, then run
  ls             List available prompts and roles
  role           Resolve roles to files and print them
  help           Print this usage information

EXAMPLES
  cplus                                    # Interactive: pick action + roles
  cplus plan --roles arch                  # Use 'plan' action with 'arch' role
  cplus pick --roles review notes/DECISIONS.md
  cplus tasks/123/task.md --roles arch,impl "be strict"
  cplus ls actions                         # List available actions
  cplus ls roles                           # List available roles
  cplus role --roles arch,review           # Print resolved role files

OPTIONS
  --roles <role1,role2,...>  Specify roles (comma-separated or repeated)
  --no-roles                 Skip roles entirely (use when action defines its own)
  --dry-run                  Preview composition without sending to claude
  --help, -h                 Show this help message

For full specification, see cplus_contract.md
EOF
}

# Main entry point
main() {
  local operation=""
  local prompt_selector=""
  local -a roles_array
  local -a extras_array

  # Parse operation (first arg if it's a known operation)
  if [[ $# -gt 0 ]]; then
    case "$1" in
      run|pick|ls|role|help|--help|-h)
        operation="$1"
        shift
        ;;
      *)
        operation="run"
        ;;
    esac
  else
    operation="run"
  fi

  # Handle help
  if [[ "$operation" == "help" || "$operation" == "--help" || "$operation" == "-h" ]]; then
    show_help
    exit 0
  fi

  # Handle ls operation
  if [[ "$operation" == "ls" ]]; then
    handle_ls "$@"
    exit 0
  fi

  # Handle role operation
  if [[ "$operation" == "role" ]]; then
    handle_role "$@"
    exit 0
  fi

  # For run and pick operations, parse arguments
  local -a roles_array
  local -a extras_array
  local dry_run=false
  local no_roles=false

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        dry_run=true
        shift
        ;;
      --no-roles)
        no_roles=true
        shift
        ;;
      --roles)
        shift
        if [[ $# -eq 0 ]]; then
          echo "Error: --roles requires an argument" >&2
          exit 1
        fi
        # Split comma-separated roles
        IFS=',' read -rA role_parts <<< "$1"
        roles_array+=("${role_parts[@]}")
        shift
        ;;
      --roles=*)
        # Handle --roles=arch,impl format
        local roles_value="${1#--roles=}"
        IFS=',' read -rA role_parts <<< "$roles_value"
        roles_array+=("${role_parts[@]}")
        shift
        ;;
      -*)
        echo "Error: Unknown option $1" >&2
        exit 1
        ;;
      *)
        # First non-option arg is prompt_selector (if not pick operation)
        if [[ "$operation" == "pick" ]]; then
          # For pick, all remaining args are extras
          extras_array+=("$1")
        elif [[ -z "$prompt_selector" ]]; then
          prompt_selector="$1"
        else
          extras_array+=("$1")
        fi
        shift
        ;;
    esac
  done

  # Handle run and pick operations
  if [[ "$operation" == "run" || "$operation" == "pick" ]]; then
    handle_run_or_pick "$operation" "$prompt_selector" "$dry_run" "$no_roles" "$roles_array[@]" -- "${extras_array[@]}"
    exit 0
  fi

  # Should never reach here
  echo "Unknown operation: $operation" >&2
  exit 1
}

# List available prompts
list_actions() {
  local actions_dir="$PROMPTS_DIR/actions"
  if [[ ! -d "$actions_dir" ]]; then
    echo "No actions directory found at $actions_dir" >&2
    return 1
  fi

  echo "Available actions:"
  find "$actions_dir" -type f -name "*.md" | while read -r file; do
    local rel_path="${file#$actions_dir/}"
    local name="${rel_path%.md}"
    echo "  $name"
  done | sort
}

list_roles() {
  local roles_dir="$PROMPTS_DIR/roles"
  if [[ ! -d "$roles_dir" ]]; then
    echo "No roles directory found at $roles_dir" >&2
    return 1
  fi

  echo "Available roles:"
  find "$roles_dir" -type f -name "*.md" | while read -r file; do
    local rel_path="${file#$roles_dir/}"
    local name="${rel_path%.md}"
    echo "  $name"
  done | sort
}

# Check if fzf is available
check_fzf() {
  if ! command -v fzf &> /dev/null; then
    echo "Error: fzf is required for interactive selection" >&2
    echo "Install with: brew install fzf" >&2
    exit 1
  fi
}

# Interactive selection of an action prompt
# Returns: selected file path or exits on error
interactive_select_action() {
  check_fzf

  local actions_dir="$PROMPTS_DIR/actions"
  local -a action_files
  action_files=($(find "$actions_dir" -type f -name "*.md" | sort))

  if [[ ${#action_files[@]} -eq 0 ]]; then
    echo "No action prompts found in $actions_dir" >&2
    exit 1
  fi

  local selected
  selected=$(printf '%s\n' "${action_files[@]}" | \
    sed "s|^$actions_dir/||; s|\.md$||" | \
    fzf --prompt="Select action: " --height=40% --reverse)

  if [[ -z "$selected" ]]; then
    echo "No action selected" >&2
    exit 1
  fi

  echo "$actions_dir/$selected.md"
}

# Interactive multi-selection of role prompts
# Returns: space-separated list of file paths (may be empty)
interactive_select_roles() {
  check_fzf

  local roles_dir="$PROMPTS_DIR/roles"
  local -a role_files
  role_files=($(find "$roles_dir" -type f -name "*.md" | sort))

  if [[ ${#role_files[@]} -eq 0 ]]; then
    # No roles available, return empty
    return 0
  fi

  local selected
  selected=$(printf '%s\n' "${role_files[@]}" | \
    sed "s|^$roles_dir/||; s|\.md$||" | \
    fzf --multi --prompt="Select roles (tab to select multiple, enter to confirm): " \
        --height=40% --reverse)

  # Empty selection is valid (user can skip roles)
  if [[ -z "$selected" ]]; then
    return 0
  fi

  # Convert selected names back to file paths
  echo "$selected" | while read -r name; do
    echo "$roles_dir/$name.md"
  done | tr '\n' ' '
}

# Fuzzy match a prompt in a directory
# Args: $1 = type (actions|roles), $2 = selector
# Returns: file path or empty string on failure
fuzzy_match_prompt() {
  local type="$1"
  local selector="$2"
  local dir="$PROMPTS_DIR/$type"

  if [[ -z "$selector" ]]; then
    return 1
  fi

  # Check if selector is an existing file path
  if [[ -f "$selector" ]]; then
    echo "$selector"
    return 0
  fi

  # Try exact match by basename (without extension)
  local exact_match="$dir/$selector.md"
  if [[ -f "$exact_match" ]]; then
    echo "$exact_match"
    return 0
  fi

  # Try fuzzy match: find files containing the selector string
  local -a matches
  matches=($(find "$dir" -type f -name "*.md" | while read -r file; do
    local basename="${file##*/}"
    local name="${basename%.md}"
    if [[ "$name" == *"$selector"* ]]; then
      echo "$file"
    fi
  done))

  if [[ ${#matches[@]} -eq 1 ]]; then
    echo "${matches[1]}"
    return 0
  elif [[ ${#matches[@]} -gt 1 ]]; then
    echo "Ambiguous selector '$selector' matches multiple files:" >&2
    printf '%s\n' "${matches[@]}" >&2
    return 1
  else
    # No matches found
    return 1
  fi
}

# Resolve base prompt according to contract section 3.2
# Args: $1 = prompt_selector (may be empty)
# Returns: file path or exits on error
resolve_base_prompt() {
  local selector="$1"
  local matched

  # If selector is an existing file path, use it
  if [[ -n "$selector" && -f "$selector" ]]; then
    echo "$selector"
    return 0
  fi

  # If selector provided and non-empty, try fuzzy match in actions
  if [[ -n "$selector" ]]; then
    matched=$(fuzzy_match_prompt "actions" "$selector")
    if [[ -n "$matched" ]]; then
      echo "$matched"
      return 0
    else
      echo "Error: Could not resolve action prompt '$selector'" >&2
      exit 1
    fi
  fi

  # No selector provided, interactive select
  interactive_select_action
}

# Resolve roles from --roles option or interactive selection
# Args: $@ = array of role selectors (may be empty)
# Returns: space-separated list of file paths
resolve_roles() {
  local -a role_selectors=("$@")

  # If no roles specified, interactive select
  if [[ ${#role_selectors[@]} -eq 0 ]]; then
    interactive_select_roles
    return 0
  fi

  # Resolve each role selector with fuzzy matching
  local -a resolved_roles
  local matched
  for selector in "${role_selectors[@]}"; do
    matched=$(fuzzy_match_prompt "roles" "$selector")
    if [[ -n "$matched" ]]; then
      resolved_roles+=("$matched")
    else
      echo "Error: Could not resolve role '$selector'" >&2
      exit 1
    fi
  done

  # Return space-separated paths
  local result=""
  for role in "${resolved_roles[@]}"; do
    if [[ -n "$result" ]]; then
      result="$result $role"
    else
      result="$role"
    fi
  done
  echo "$result"
}

# Process extras (remaining positional args)
# Args: $@ = extras array
# Prints extra blocks to stdout
process_extras() {
  local -a extras=("$@")

  if [[ ${#extras[@]} -eq 0 ]]; then
    return 0
  fi

  echo ""
  echo "### Additional Instructions"

  for extra in "${extras[@]}"; do
    if [[ -f "$extra" ]]; then
      # It's a file, inline its content
      echo "#### file: $extra"
      cat "$extra"
    else
      # It's plain text
      echo "#### text"
      echo "$extra"
    fi
    echo ""
  done
}

# Compose the full prompt
# Args: $1 = base_prompt_file, $2 = roles (space-separated file paths), $@ = extras
compose_prompt() {
  local base_prompt="$1"
  shift
  local roles_str="$1"
  shift
  local -a extras=("$@")

  # Output base prompt
  cat "$base_prompt"

  # Output roles section if any roles
  if [[ -n "$roles_str" ]]; then
    local -a role_files
    read -rA role_files <<< "$roles_str"

    if [[ ${#role_files[@]} -gt 0 ]]; then
      echo ""
      echo "### Roles"

      for role_file in "${role_files[@]}"; do
        if [[ -f "$role_file" ]]; then
          local role_name="${role_file##*/}"
          role_name="${role_name%.md}"
          echo "#### $role_name"
          cat "$role_file"
          echo ""
        fi
      done
    fi
  fi

  # Output extras section if any
  process_extras "${extras[@]}"
}

# Handle ls operation
handle_ls() {
  local subcommand="${1:-}"

  case "$subcommand" in
    actions)
      list_actions
      ;;
    roles)
      list_roles
      ;;
    "")
      list_actions
      echo ""
      list_roles
      ;;
    *)
      echo "Unknown ls subcommand: $subcommand" >&2
      echo "Usage: cplus ls [actions|roles]" >&2
      exit 1
      ;;
  esac
}

# Handle role operation
handle_role() {
  local -a roles_array

  # Parse --roles option
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --roles)
        shift
        if [[ $# -eq 0 ]]; then
          echo "Error: --roles requires an argument" >&2
          exit 1
        fi
        IFS=',' read -rA role_parts <<< "$1"
        roles_array+=("${role_parts[@]}")
        shift
        ;;
      --roles=*)
        local roles_value="${1#--roles=}"
        IFS=',' read -rA role_parts <<< "$roles_value"
        roles_array+=("${role_parts[@]}")
        shift
        ;;
      *)
        echo "Error: Unknown argument for role operation: $1" >&2
        exit 1
        ;;
    esac
  done

  # Resolve roles
  local resolved_roles
  resolved_roles=$(resolve_roles "${roles_array[@]}")

  # Print resolved roles
  if [[ -n "$resolved_roles" ]]; then
    echo "Resolved roles:"
    local -a role_files
    read -rA role_files <<< "$resolved_roles"
    for role_file in "${role_files[@]}"; do
      echo "  $role_file"
    done
  else
    echo "No roles selected"
  fi
}

# Handle run or pick operation
handle_run_or_pick() {
  local operation="$1"
  shift
  local prompt_selector="$1"
  shift
  local dry_run="$1"
  shift
  local no_roles="$1"
  shift

  # Collect roles (up to --)
  local -a roles_array
  while [[ $# -gt 0 && "$1" != "--" ]]; do
    roles_array+=("$1")
    shift
  done

  # Skip the -- separator
  if [[ "$1" == "--" ]]; then
    shift
  fi

  # Remaining args are extras
  local -a extras_array=("$@")

  # Check that claude command exists (unless dry-run)
  if [[ "$dry_run" != "true" ]] && ! command -v claude &> /dev/null; then
    echo "Error: 'claude' command not found in PATH" >&2
    echo "Please ensure Claude CLI is installed and available" >&2
    exit 1
  fi

  # Resolve base prompt (pick operation ignores selector)
  local base_prompt
  if [[ "$operation" == "pick" ]]; then
    base_prompt=$(resolve_base_prompt "")
  else
    base_prompt=$(resolve_base_prompt "$prompt_selector")
  fi

  # Resolve roles (skip if --no-roles)
  local resolved_roles=""
  if [[ "$no_roles" != "true" ]]; then
    resolved_roles=$(resolve_roles "${roles_array[@]}")
  fi

  # Compose and either output or pipe to claude
  if [[ "$dry_run" == "true" ]]; then
    compose_prompt "$base_prompt" "$resolved_roles" "${extras_array[@]}"
  else
    compose_prompt "$base_prompt" "$resolved_roles" "${extras_array[@]}" | claude
  fi
}

main "$@"
