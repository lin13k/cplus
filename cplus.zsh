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

# ============================================================================
# Project Context Detection
# ============================================================================

# Find project root by walking up directory tree
# Returns: path to project root or empty string
find_project_root() {
  local current_dir="$PWD"

  while [[ "$current_dir" != "/" ]]; do
    # Check for project markers
    if [[ -f "$current_dir/.cplus.yml" ]] || \
       [[ -f "$current_dir/.git/config" ]] || \
       [[ -f "$current_dir/package.json" ]] || \
       [[ -f "$current_dir/Makefile" ]] || \
       [[ -f "$current_dir/go.mod" ]] || \
       [[ -f "$current_dir/Cargo.toml" ]]; then
      echo "$current_dir"
      return 0
    fi
    current_dir="${current_dir:h}"
  done

  # No project root found
  return 1
}

# Parse .cplus.yml config file
# Args: $1 = config file path
# Prints: YAML content parsed as key-value pairs
parse_cplus_yml() {
  local config_file="$1"

  if [[ ! -f "$config_file" ]]; then
    return 1
  fi

  # Simple YAML parser (handles basic format)
  # Full YAML parser would need yq, but we'll keep it simple
  cat "$config_file"
}

# Parse package.json scripts
# Args: $1 = package.json path
# Prints: commands in format "name: command"
parse_package_json() {
  local pkg_file="$1"

  if [[ ! -f "$pkg_file" ]]; then
    return 1
  fi

  if ! command -v jq &> /dev/null; then
    # jq not available, skip
    return 1
  fi

  # Extract scripts
  jq -r '.scripts | to_entries | .[] | "\(.key): \(.value)"' "$pkg_file" 2>/dev/null
}

# Parse Makefile targets
# Args: $1 = Makefile path
# Prints: targets in format "name: (make target)"
parse_makefile() {
  local makefile="$1"

  if [[ ! -f "$makefile" ]]; then
    return 1
  fi

  # Extract target names (lines ending with :)
  grep -E '^[a-zA-Z0-9_-]+:' "$makefile" | sed 's/:.*//' | while read -r target; do
    echo "$target: make $target"
  done
}

# Load project context
# Returns: project context as formatted text
load_project_context() {
  local project_root
  project_root=$(find_project_root)

  if [[ -z "$project_root" ]]; then
    return 1
  fi

  local output=""
  local has_content=false

  # Try .cplus.yml first
  if [[ -f "$project_root/.cplus.yml" ]]; then
    output=$(cat "$project_root/.cplus.yml")
    has_content=true
  # Try package.json
  elif [[ -f "$project_root/package.json" ]]; then
    local scripts
    scripts=$(parse_package_json "$project_root/package.json")
    if [[ -n "$scripts" ]]; then
      output="project:\n  name: $(basename "$project_root")\n\ncommands:\n"
      output+=$(echo "$scripts" | sed 's/^/  /')
      has_content=true
    fi
  # Try Makefile
  elif [[ -f "$project_root/Makefile" ]]; then
    local targets
    targets=$(parse_makefile "$project_root/Makefile")
    if [[ -n "$targets" ]]; then
      output="project:\n  name: $(basename "$project_root")\n\ncommands:\n"
      output+=$(echo "$targets" | sed 's/^/  /')
      has_content=true
    fi
  fi

  if [[ "$has_content" == "true" ]]; then
    echo -e "$output"
    return 0
  fi

  return 1
}

# Format project context for prompt injection
# Returns: formatted markdown section
format_project_context() {
  local config
  config=$(load_project_context)

  if [[ -z "$config" ]]; then
    return 0
  fi

  echo ""
  echo "### Project Context"
  echo ""

  # Parse and format the config
  local in_section=""
  local project_name=""

  while IFS= read -r line; do
    # Skip empty lines
    [[ -z "$line" ]] && continue

    # Detect sections
    if [[ "$line" =~ ^project: ]]; then
      in_section="project"
      continue
    elif [[ "$line" =~ ^commands: ]]; then
      in_section="commands"
      echo "**Commands**:"
      continue
    elif [[ "$line" =~ ^paths: ]]; then
      in_section="paths"
      echo ""
      echo "**Paths**:"
      continue
    elif [[ "$line" =~ ^conventions: ]]; then
      in_section="conventions"
      echo ""
      echo "**Conventions**:"
      continue
    fi

    # Process line based on section
    if [[ "$in_section" == "project" ]]; then
      if [[ "$line" =~ name: ]]; then
        # Extract name value, removing quotes if present
        project_name="${line#*name:}"
        project_name="${project_name# }"  # Remove leading space
        project_name="${project_name#\"}"  # Remove leading quote
        project_name="${project_name%\"}"  # Remove trailing quote
        echo "**Project**: $project_name"
        echo ""
      fi
    elif [[ "$in_section" == "commands" ]]; then
      # Format: "  name: command" -> "- name: `command`"
      local cmd_line="${line#"${line%%[![:space:]]*}"}"  # Strip leading spaces
      if [[ "$cmd_line" =~ : ]]; then
        local name="${cmd_line%%:*}"
        local cmd="${cmd_line#*: }"
        # Remove quotes if present
        cmd="${cmd#\"}"
        cmd="${cmd%\"}"
        echo "- $name: \`$cmd\`"
      fi
    elif [[ "$in_section" == "paths" ]]; then
      local path_line="${line#"${line%%[![:space:]]*}"}"  # Strip leading spaces
      if [[ "$path_line" =~ : ]]; then
        local name="${path_line%%:*}"
        local pathval="${path_line#*: }"
        # Remove quotes if present
        pathval="${pathval#\"}"
        pathval="${pathval%\"}"
        echo "- $name: \`$pathval\`"
      fi
    elif [[ "$in_section" == "conventions" ]]; then
      # Strip leading spaces and dash
      local conv="${line#"${line%%[![:space:]]*}"}"  # Strip leading spaces
      conv="${conv#- }"  # Remove leading dash and space
      # Remove quotes if present
      conv="${conv#\"}"
      conv="${conv%\"}"
      [[ -n "$conv" ]] && echo "- $conv"
    fi
  done <<< "$config"
}

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
  project        Manage project configuration (show, init, validate)
  develop-v3     Automated multi-session pipeline (architect→setup→implement→verify→review→cleanup)
  help           Print this usage information

EXAMPLES
  cplus                                    # Interactive: pick action (no roles)
  cplus spec                               # Use 'spec' action (no roles)
  cplus develop --roles architect          # Use 'develop' with 'architect' role
  cplus pick --roles reviewer notes/DECISIONS.md
  cplus tasks/123/task.md "be strict"      # Use task file (no roles)
  cplus ls actions                         # List available actions
  cplus ls roles                           # List available roles
  cplus role --roles arch,review           # Print resolved role files
  cplus project show                       # Show detected project context
  cplus project init                       # Create .cplus.yml template
  cplus develop-v3 .cplus/specs/0001.md   # Run automated pipeline
  cplus develop-v3 spec.md --from verify  # Resume from verify phase

OPTIONS
  --roles <role1,role2,...>  Inject roles (comma-separated or repeated)
  --dry-run                  Preview composition without sending to claude
  -p, --print                Non-interactive mode: pipe to claude -p and print output
  --help, -h                 Show this help message

NOTE
  By default, NO roles are injected. Use --roles to explicitly add role definitions.

For full specification, see cplus_contract.md
EOF
}

# ============================================================================
# develop-v3: Shell-orchestrated multi-session pipeline
# ============================================================================

# Run a single phase subprocess via cplus -p
# Args: phase_name role_file task_dir [context_files...]
_dv3_run_phase() {
  local phase="$1"
  local role_file="$2"
  local task_dir="$3"
  shift 3
  local -a context_files=("$@")

  local start_time=$SECONDS
  echo ""
  echo "[${phase}] starting..."

  # Remove stale BLOCKED file from previous run
  rm -f "$task_dir/BLOCKED"

  # Check role file exists
  if [[ ! -f "$role_file" ]]; then
    echo "Error: role file not found: $role_file" >&2
    exit 1
  fi

  # Run cplus -p with role file + context files (streams output live)
  local exit_code
  cplus -p "$role_file" "${context_files[@]}"
  exit_code=$?

  # Check for BLOCKED file written by the role
  if [[ -f "$task_dir/BLOCKED" ]]; then
    local reason
    reason=$(cat "$task_dir/BLOCKED")
    echo ""
    echo "[BLOCKED] $reason" >&2
    exit 1
  fi

  if [[ $exit_code -ne 0 ]]; then
    echo ""
    echo "[${phase}] FAILED (exit code $exit_code)" >&2
    exit 1
  fi

  local elapsed=$((SECONDS - start_time))
  echo "[${phase}] done (${elapsed}s)"
}

# Commit all changes after a phase
# Args: phase task_id project_root
_dv3_git_commit() {
  local phase="$1"
  local task_id="$2"
  local project_root="$3"

  (
    cd "$project_root" || exit 1
    git add -A
    if git diff --staged --quiet; then
      echo "[git] nothing to commit for ${phase}"
    else
      git commit -m "cplus(${phase}): ${task_id}"
    fi
  )
}

# Parse checkpoint blocks from plan.md
# Populates global _DV3_CHECKPOINTS array with one element per checkpoint block
# Args: plan_file
_dv3_parse_checkpoints() {
  local plan_file="$1"
  _DV3_CHECKPOINTS=()

  local current_block=""
  local in_checkpoint=false

  while IFS= read -r line; do
    if [[ "$line" =~ ^"## Checkpoint "[0-9]+: ]]; then
      if [[ "$in_checkpoint" == "true" && -n "$current_block" ]]; then
        _DV3_CHECKPOINTS+=("$current_block")
      fi
      current_block="$line"$'\n'
      in_checkpoint=true
    elif [[ "$in_checkpoint" == "true" ]]; then
      # Stop at next level-2 heading that is not a Checkpoint
      if [[ "$line" =~ ^"## " && ! "$line" =~ ^"## Checkpoint " ]]; then
        _DV3_CHECKPOINTS+=("$current_block")
        current_block=""
        in_checkpoint=false
      else
        current_block+="$line"$'\n'
      fi
    fi
  done < "$plan_file"

  # Flush last block
  if [[ "$in_checkpoint" == "true" && -n "$current_block" ]]; then
    _DV3_CHECKPOINTS+=("$current_block")
  fi
}

# Warn if a phase commit already exists for this task
# Args: phase task_id project_root
_dv3_check_already_committed() {
  local phase="$1"
  local task_id="$2"
  local project_root="$3"
  local commit_msg="cplus(${phase}): ${task_id}"

  if git -C "$project_root" log --oneline --grep="^${commit_msg}$" | grep -q .; then
    echo "Warning: ${phase} phase already committed for ${task_id}." >&2
    echo "  Use --from to skip already-done phases, or git reset to redo." >&2
  fi
}

# Handle develop-v3 operation
handle_develop_v3() {
  local spec_file=""
  local from_phase=""
  local from_checkpoint=0

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from)
        shift
        if [[ $# -eq 0 ]]; then
          echo "Error: --from requires a phase name" >&2
          echo "Valid values: architect, setup, implement, checkpoint-N, verify, review, cleanup" >&2
          exit 1
        fi
        from_phase="$1"
        shift
        ;;
      --from=*)
        from_phase="${1#--from=}"
        shift
        ;;
      -*)
        echo "Error: Unknown option $1" >&2
        exit 1
        ;;
      *)
        if [[ -z "$spec_file" ]]; then
          spec_file="$1"
        fi
        shift
        ;;
    esac
  done

  # Validate spec file
  if [[ -z "$spec_file" ]]; then
    echo "Error: spec file required" >&2
    echo "Usage: cplus develop-v3 <spec-file> [--from <phase>]" >&2
    exit 1
  fi
  if [[ ! -f "$spec_file" ]]; then
    echo "Error: spec file not found: $spec_file" >&2
    exit 1
  fi

  # Derive task_id from spec filename (basename without .md)
  local task_id
  task_id="${spec_file##*/}"
  task_id="${task_id%.md}"

  # Locate project root and task workspace
  local project_root
  project_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
  local task_dir="$project_root/.cplus/tasks/$task_id"
  mkdir -p "$task_dir"

  # Role files directory
  local roles_v3_dir="$PROMPTS_DIR/roles/develop-v3"

  # Validate --from value
  if [[ -n "$from_phase" ]]; then
    case "$from_phase" in
      architect|setup|implement|verify|review|cleanup)
        ;;
      checkpoint-*)
        local cp_num="${from_phase#checkpoint-}"
        if ! [[ "$cp_num" =~ ^[0-9]+$ ]]; then
          echo "Error: invalid --from value: $from_phase" >&2
          echo "Valid values: architect, setup, implement, checkpoint-N, verify, review, cleanup" >&2
          exit 1
        fi
        from_checkpoint=$cp_num
        from_phase="implement"
        ;;
      *)
        echo "Error: invalid --from value: $from_phase" >&2
        echo "Valid values: architect, setup, implement, checkpoint-N, verify, review, cleanup" >&2
        exit 1
        ;;
    esac
  fi

  # Phase execution order
  local -a phase_order=(architect setup implement verify review cleanup)

  # Determine start index from --from phase
  local start_idx=0
  if [[ -n "$from_phase" ]]; then
    local _i=0
    for _p in "${phase_order[@]}"; do
      if [[ "$_p" == "$from_phase" ]]; then
        start_idx=$_i
        break
      fi
      _i=$(( _i + 1 ))
    done
  fi

  echo "develop-v3: $task_id"
  if [[ -n "$from_phase" ]]; then
    if [[ $from_checkpoint -gt 0 ]]; then
      echo "Resuming from: checkpoint-$from_checkpoint"
    else
      echo "Resuming from: $from_phase"
    fi
  fi

  # Run each phase
  local _phase_idx=0
  for _phase in "${phase_order[@]}"; do
    if [[ $_phase_idx -lt $start_idx ]]; then
      _phase_idx=$(( _phase_idx + 1 ))
      continue
    fi

    case "$_phase" in
      architect)
        _dv3_check_already_committed "architect" "$task_id" "$project_root"
        _dv3_run_phase "architect" \
          "$roles_v3_dir/architect.md" \
          "$task_dir" \
          "$spec_file" "$task_dir"
        _dv3_git_commit "architect" "$task_id" "$project_root"
        ;;

      setup)
        _dv3_check_already_committed "setup" "$task_id" "$project_root"
        _dv3_run_phase "setup" \
          "$roles_v3_dir/setup.md" \
          "$task_dir" \
          "$task_dir/plan.md" "$task_dir/state.md"
        _dv3_git_commit "setup" "$task_id" "$project_root"
        ;;

      implement)
        local plan_file="$task_dir/plan.md"
        if [[ ! -f "$plan_file" ]]; then
          echo "Error: plan.md not found — did architect phase run?" >&2
          exit 1
        fi

        _dv3_parse_checkpoints "$plan_file"
        local total_checkpoints=${#_DV3_CHECKPOINTS[@]}

        if [[ $total_checkpoints -eq 0 ]]; then
          echo "Warning: no checkpoints found in plan.md — skipping implement phase"
        fi

        local cp_idx=1
        for _cp_content in "${_DV3_CHECKPOINTS[@]}"; do
          if [[ $cp_idx -lt $from_checkpoint ]]; then
            echo "[checkpoint-$cp_idx] skipped (--from checkpoint-$from_checkpoint)"
            cp_idx=$(( cp_idx + 1 ))
            continue
          fi

          local tmpchk
          tmpchk=$(mktemp)
          printf '%s' "$_cp_content" > "$tmpchk"

          _dv3_run_phase "checkpoint-$cp_idx" \
            "$roles_v3_dir/implement.md" \
            "$task_dir" \
            "$task_dir/state.md" "$tmpchk"
          rm -f "$tmpchk"

          _dv3_git_commit "checkpoint-$cp_idx" "$task_id" "$project_root"
          cp_idx=$(( cp_idx + 1 ))
        done
        ;;

      verify)
        _dv3_check_already_committed "verify" "$task_id" "$project_root"
        _dv3_run_phase "verify" \
          "$roles_v3_dir/verify.md" \
          "$task_dir" \
          "$task_dir/state.md" "$task_dir/plan.md"
        _dv3_git_commit "verify" "$task_id" "$project_root"
        ;;

      review)
        _dv3_check_already_committed "review" "$task_id" "$project_root"
        _dv3_run_phase "review" \
          "$roles_v3_dir/review.md" \
          "$task_dir" \
          "$task_dir/report.md"
        _dv3_git_commit "review" "$task_id" "$project_root"
        ;;

      cleanup)
        _dv3_check_already_committed "cleanup" "$task_id" "$project_root"
        _dv3_run_phase "cleanup" \
          "$roles_v3_dir/cleanup.md" \
          "$task_dir" \
          "$task_dir/state.md"
        _dv3_git_commit "cleanup" "$task_id" "$project_root"
        ;;
    esac

    _phase_idx=$(( _phase_idx + 1 ))
  done

  echo ""
  echo "develop-v3 complete: $task_id"
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
      run|pick|ls|role|project|develop-v3|help|--help|-h)
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

  # Handle project operation
  if [[ "$operation" == "project" ]]; then
    handle_project "$@"
    exit 0
  fi

  # Handle develop-v3 operation
  if [[ "$operation" == "develop-v3" ]]; then
    handle_develop_v3 "$@"
    exit 0
  fi

  # For run and pick operations, parse arguments
  local -a roles_array
  local -a extras_array
  local dry_run=false
  local print_mode=false
  local inject_roles=false  # Default: no role injection

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        dry_run=true
        shift
        ;;
      -p|--print)
        print_mode=true
        shift
        ;;
      --roles)
        inject_roles=true
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
        inject_roles=true
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
    handle_run_or_pick "$operation" "$prompt_selector" "$dry_run" "$print_mode" "$inject_roles" "$roles_array[@]" -- "${extras_array[@]}"
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

  # Output project context if available
  format_project_context

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

# Handle project operation
handle_project() {
  local subcommand="${1:-show}"

  case "$subcommand" in
    show)
      # Show detected project context
      local project_root
      project_root=$(find_project_root)

      if [[ -z "$project_root" ]]; then
        echo "No project detected in current directory or parents"
        echo ""
        echo "Looked for: .cplus.yml, .git/, package.json, Makefile, go.mod, Cargo.toml"
        echo ""
        echo "Run 'cplus project init' to create a .cplus.yml config"
        exit 1
      fi

      echo "Project root: $project_root"
      echo ""

      # Show which config file was found
      if [[ -f "$project_root/.cplus.yml" ]]; then
        echo "Config: .cplus.yml (explicit config)"
        echo ""
        cat "$project_root/.cplus.yml"
      elif [[ -f "$project_root/package.json" ]]; then
        echo "Config: package.json (auto-detected)"
        echo ""
        echo "Commands (from package.json scripts):"
        parse_package_json "$project_root/package.json" | sed 's/^/  /'
      elif [[ -f "$project_root/Makefile" ]]; then
        echo "Config: Makefile (auto-detected)"
        echo ""
        echo "Commands (from Makefile targets):"
        parse_makefile "$project_root/Makefile" | sed 's/^/  /'
      else
        echo "Project detected but no recognized config file"
      fi
      ;;

    init)
      # Create .cplus.yml template
      if [[ -f ".cplus.yml" ]]; then
        echo "Error: .cplus.yml already exists in current directory" >&2
        exit 1
      fi

      cat > .cplus.yml << 'EOF'
# cplus project configuration
project:
  name: "my-project"
  description: "Project description"

commands:
  # Testing
  test: "npm test"
  test_file: "npm test --"

  # Build & Type Check
  build: "npm run build"
  type_check: "npm run type-check"
  lint: "npm run lint"

  # Development
  dev: "npm run dev"
  install: "npm install"

paths:
  src: "src/"
  tests: "tests/"
  config: "./"

conventions:
  - "Add your project-specific conventions here"
  - "These will be shown to Claude when composing prompts"
EOF

      echo "✓ Created .cplus.yml"
      echo ""
      echo "Edit .cplus.yml to customize for your project."
      echo "Run 'cplus project show' to see the detected config."
      ;;

    validate)
      # Validate project config
      local project_root
      project_root=$(find_project_root)

      if [[ -z "$project_root" ]]; then
        echo "❌ No project detected"
        exit 1
      fi

      echo "✓ Project root found: $project_root"

      if [[ -f "$project_root/.cplus.yml" ]]; then
        echo "✓ .cplus.yml found"

        # Basic validation (check if it's valid YAML-ish)
        if grep -q "project:" "$project_root/.cplus.yml" && \
           grep -q "commands:" "$project_root/.cplus.yml"; then
          echo "✓ Config structure looks valid"
        else
          echo "⚠️  Config may be malformed (missing project: or commands: section)"
        fi
      elif [[ -f "$project_root/package.json" ]]; then
        echo "✓ package.json found (auto-detected)"
      elif [[ -f "$project_root/Makefile" ]]; then
        echo "✓ Makefile found (auto-detected)"
      fi

      echo ""
      echo "Project context will be injected into prompts automatically."
      ;;

    *)
      echo "Unknown project subcommand: $subcommand" >&2
      echo "Usage: cplus project [show|init|validate]" >&2
      exit 1
      ;;
  esac
}

# Handle run or pick operation
handle_run_or_pick() {
  local operation="$1"
  shift
  local prompt_selector="$1"
  shift
  local dry_run="$1"
  shift
  local print_mode="$1"
  shift
  local inject_roles="$1"
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

  # Resolve roles (only if --roles was specified)
  local resolved_roles=""
  if [[ "$inject_roles" == "true" ]]; then
    resolved_roles=$(resolve_roles "${roles_array[@]}")
  fi

  # Compose and either output or pipe to claude
  if [[ "$dry_run" == "true" ]]; then
    compose_prompt "$base_prompt" "$resolved_roles" "${extras_array[@]}"
  elif [[ "$print_mode" == "true" ]]; then
    compose_prompt "$base_prompt" "$resolved_roles" "${extras_array[@]}" | claude -p
  else
    compose_prompt "$base_prompt" "$resolved_roles" "${extras_array[@]}" | claude
  fi
}

main "$@"
