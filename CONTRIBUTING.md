# Contributing to cplus

Thank you for your interest in contributing to cplus! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug:
1. Check if it's already reported in [Issues](https://github.com/yourusername/cplus/issues)
2. If not, open a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, zsh version, Claude CLI version)

### Suggesting Features

Have an idea? Open an issue with:
- Clear description of the feature
- Use cases (why is it useful?)
- Proposed implementation (if you have one)

### Submitting Code

1. **Fork and clone**
   ```bash
   git clone https://github.com/yourusername/cplus.git
   cd cplus
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Test your changes thoroughly
   - Update documentation if needed

4. **Test installation**
   ```bash
   ./install.sh
   cplus ls
   cplus --dry-run plan --roles architect
   ./uninstall.sh
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Describe what you changed and why
   - Link related issues
   - Add examples if applicable

## Sharing Prompts

Have useful action or role prompts to share?

### Option 1: Submit as Example

Add to `prompts/examples/` directory:
```bash
prompts/examples/
├── actions/
│   └── your-action.md
└── roles/
    └── your-role.md
```

Include:
- Clear description at the top
- Use cases
- Example invocation

### Option 2: Submit to Core

For prompts that should be in the standard library:
1. Add to `prompts/actions/` or `prompts/roles/`
2. Document in README.md
3. Explain why it's broadly useful

## Code Style

### Shell Scripts

- Use `set -e` for error handling
- Add comments for non-obvious logic
- Use descriptive variable names
- Follow existing formatting

```bash
# Good
PROMPTS_DIR="$SCRIPT_DIR/prompts"
if [[ ! -d "$PROMPTS_DIR" ]]; then
    echo "Error: Prompts directory not found" >&2
    exit 1
fi

# Not ideal
dir=$1
[ ! -d $dir ] && exit 1
```

### Markdown (Prompts)

- Use clear headers (`#`, `##`, `###`)
- Add examples where helpful
- Keep prompts focused and concise
- Use bullet points for lists

## Testing

Before submitting a PR, test:

1. **Installation**
   ```bash
   ./install.sh
   ```

2. **Basic operations**
   ```bash
   cplus help
   cplus ls
   cplus ls actions
   cplus ls roles
   ```

3. **Dry run**
   ```bash
   cplus --dry-run plan --roles architect
   ```

4. **Interactive selection** (requires fzf)
   ```bash
   cplus pick
   ```

5. **Uninstallation**
   ```bash
   ./uninstall.sh
   ```

## Documentation

Update documentation for:
- New features → README.md
- New actions/roles → Add to examples in README.md
- Breaking changes → Migration guide in PR description
- Bug fixes → Mention in commit message

## Commit Messages

Follow conventional commits:

```
feat: add new action for debugging
fix: resolve fuzzy matching ambiguity
docs: update installation instructions
refactor: simplify role resolution logic
test: add test for sync-prompts.sh
```

## Questions?

- Open an issue for questions
- Tag with `question` label
- We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🚀
