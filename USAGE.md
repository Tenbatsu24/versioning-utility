# Version Manager Tool Usage

A comprehensive tool for automated semantic versioning and changelog management.

## 📦 Installation

```bash
# Install in development mode
pip install -e .

# Or install directly
pip install git+https://github.com/your-org/your-repo.git
```

## 🎯 Quick Start

```bash
# Check what version would be applied
python -m versioning_tool.version_manager check

# Apply version bump and update files
python -m versioning_tool.version_manager bump --yes

# Update changelog only
python -m versioning_tool.version_manager changelog

# Update release graph in README
python -m versioning_tool.version_manager graph
```

## 🔧 Commands

### `check` - Preview Version Bump

Shows what the next version would be based on current changes.

```bash
python -m versioning_tool.version_manager check
```

**Output:**
```
Branch: feature/new-auth
Current: 1.2.0
Suggested: 1.3.0-alpha.1  (minor)
Reason: branch=minor, conventional=minor, prerelease=alpha
```

**Options:**
- No additional options

### `bump` - Apply Version Bump

Updates version in `pyproject.toml` and generates changelog.

```bash
# Interactive mode (prompts for confirmation)
python -m versioning_tool.version_manager bump

# Non-interactive mode (for CI)
python -m versioning_tool.version_manager bump --yes
```

**What it does:**
1. Calculates next version based on changes
2. Updates `pyproject.toml` version
3. Generates/updates `CHANGELOG.md`
4. Updates release graph in `README.md` (main branch only)

**Options:**
- `-y, --yes`: Skip confirmation prompt

### `changelog` - Update Changelog Only

Regenerates the changelog for the current version without changing the version.

```bash
python -m versioning_tool.version_manager changelog
```

**Use cases:**
- Manual version changes
- Changelog template updates
- Fixing incorrect changelog entries

### `graph` - Update Release Graph

Updates the Mermaid gitGraph section in the README.

```bash
python -m versioning_tool.version_manager graph
```

**Note:** Only works on main branch as configured

## ⚙️ Configuration

### Configuration File

Create or modify `versioning.yaml`:

```yaml
# Default branch for releases
default_branch: main

# Branch patterns and behavior
branch_types:
  feature/*:
    prerelease: alpha
    bump: minor
  hotfix/*:
    bump: patch
  beta/*:
    prerelease: beta
  rc/*:
    prerelease: rc

# Conventional commit rules
conventional_bump:
  major:
    - "BREAKING CHANGE"
    - "^feat!:"
  minor:
    - "^feat:"
  patch:
    - "^fix:"
    - "^perf:"
    - "^refactor:"

# Ignored patterns (no version bump)
ignore:
  files:
    - "*.md"
    - "docs/**"
    - ".github/**"
  commits:
    - "^chore:"
    - "^docs:"

# Changelog settings
changelog:
  main_only: true
  template: "CHANGELOG.md.j2"
  header: "Changelog"
  group_order: ["⚠️ Breaking Changes", "✨ Features", "🐛 Fixes", "🧰 Other"]

# Release graph settings
graph:
  readme_file: "README.md"
  start_after_heading: "## Release Graph"
  max_tags: 12

# Repository URL for links (optional)
repo_url: "https://github.com/your-org/your-repo"
```

### Environment Variables

```bash
# Custom config file location
export VERSIONING_CONFIG_PATH=/path/to/versioning.yaml

# Override repository URL
export REPO_URL=https://github.com/your-org/your-repo
```

## 🎨 Customization

### Custom Changelog Template

Create `CHANGELOG.md.j2`:

```jinja
# {{ header }}

{% for release in releases %}
## {{ release.version }} — {{ release.date }}
{% if release.sections %}
{% for title, items in release.sections %}
### {{ title }}
{% for line in items %}
- {{ line }}
{% endfor %}
{% endfor %}
{% else %}
_No notable changes._
{% endif %}
{% endfor %}
```

### Custom Section Rules

Modify `SECTION_RULES` in `versioning_tool/changelog.py`:

```python
SECTION_RULES = [
    ("🚀 New Features", [r"^feat:"]),
    ("🐛 Bug Fixes", [r"^fix:"]),
    ("⚡ Performance", [r"^perf:"]),
    ("♻️ Refactors", [r"^refactor:"]),
    ("📚 Documentation", [r"^docs:"]),
]
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Version Check
on: [pull_request]

jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install versioning tool
        run: pip install -e .

      - name: Check version bump
        run: python -m versioning_tool.version_manager check
```

### Release Automation

```yaml
name: Release
on:
  push:
    branches: [ main ]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Install tool
        run: pip install -e .

      - name: Bump version
        run: python -m versioning_tool.version_manager bump --yes

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v$(python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version']")
          body: |
            Automated release generated by versioning tool
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## ❓ Frequently Asked Questions

### Q: Why isn't my version bumping?
**A:** Check if:
- Changes are in ignored files (`*.md`, `docs/`)
- Commit messages match ignored patterns (`chore:`, `docs:`)
- You're on the correct branch

### Q: How do I manually set a version?
**A:** Edit `pyproject.toml` directly, then run:
```bash
python -m versioning_tool.version_manager changelog
```

### Q: Can I use this with non-Python projects?
**A:** Yes! Modify the version reading/writing functions in `version_manager.py` to work with your project's version file.

### Q: How do I handle breaking changes?
**A:** Use `feat!:` prefix or include "BREAKING CHANGE:" in commit body.

## 🐛 Troubleshooting

### Common Issues

1. **"No module named versioning_tool"**
   ```bash
   # Install in development mode
   pip install -e .
   ```

2. **"Template not found"**
   ```bash
   # Ensure template exists
   ls CHANGELOG.md.j2
   ```

3. **"Git command failed"**
   ```bash
   # Ensure git is installed and repository is initialized
   git status
   ```

### Debug Mode

For detailed debugging, add debug prints to the tool or run with:

```bash
# Enable Python debug output
python -m versioning_tool.version_manager check 2>&1 | head -20
```

## 📚 Related Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
