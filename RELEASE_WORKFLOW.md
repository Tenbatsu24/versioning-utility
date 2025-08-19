# Release Workflow

This document outlines the standardized release process for this project using the versioning tool.

## 📋 Overview

The versioning tool automates semantic versioning based on:
- Conventional commit messages
- Branch naming patterns
- Change impact analysis

## 🌿 Branch Strategy

| Branch Pattern | Purpose | Version Bump | Prerelease Label |
|----------------|---------|--------------|------------------|
| `main` | Stable releases | Automatic | None |
| `feature/*` | New features | Minor | `alpha` |
| `hotfix/*` | Critical fixes | Patch | None |
| `beta/*` | Beta testing | As needed | `beta` |
| `rc/*` | Release candidates | As needed | `rc` |

## 🚀 Release Process

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/awesome-new-feature

# Develop with conventional commits
git commit -m "feat: add awesome new feature"
git commit -m "fix: resolve edge case in new feature"
git commit -m "docs: update documentation"

# Push and create PR
git push origin feature/awesome-new-feature
```

### 2. Pull Request Process

1. Create PR from `feature/*` to `main`
2. CI automatically runs version check:
   ```bash
   python -m versioning_tool.version_manager check
   ```
3. Review suggested version bump in CI output
4. Ensure all tests pass

### 3. Merge to Main

```bash
# After PR approval, update local main
git checkout main
git pull origin main

# Merge the feature (squash recommended)
git merge --squash feature/awesome-new-feature
git commit -m "feat: add awesome new feature with edge case fixes"

# Verify changes
git log --oneline -5
```

### 4. Release Creation

```bash
# Check what version bump will be applied
python -m versioning_tool.version_manager check

# Apply the version bump (interactive)
python -m versioning_tool.version_manager bump

# Or non-interactive for CI
python -m versioning_tool.version_manager bump --yes

# Review the changes
git diff

# Commit version changes
git add pyproject.toml CHANGELOG.md README.md
git commit -m "chore: release v1.2.0"

# Create tag and push
git tag v1.2.0
git push origin main --tags
```

### 5. Hotfix Releases

```bash
# From main branch
git checkout main
git pull origin main

# Create hotfix branch
git checkout -b hotfix/critical-issue

# Make and commit fix
git commit -m "fix: resolve critical security issue"

# Push and create PR
git push origin hotfix/critical-issue

# After PR approval and merge
git checkout main
git pull origin main

# Release hotfix
python -m versioning_tool.version_manager bump --yes
git add pyproject.toml CHANGELOG.md README.md
git commit -m "chore: release v1.2.1"
git tag v1.2.1
git push origin main --tags
```

## 🏷️ Version Bump Rules

### Conventional Commits
- `feat:` → **Minor** version bump (1.2.0 → 1.3.0)
- `feat!:` → **Major** version bump (1.2.0 → 2.0.0) - Breaking change
- `fix:` → **Patch** version bump (1.2.0 → 1.2.1)
- `perf:`, `refactor:`, `build:`, `ci:` → **Patch** version bump

### Branch Overrides
- `hotfix/*` → Always **patch** version bump
- `feature/*` → **Minor** bump + `alpha` prerelease label when merged
- `beta/*` → Current version + `beta` prerelease label
- `rc/*` → Current version + `rc` prerelease label

### Ignored Changes
The following **do not** trigger version bumps:
- Documentation changes (`docs:` commits)
- Chore updates (`chore:` commits)
- Markdown file changes
- GitHub workflow changes

## 🔧 Configuration

The behavior is configured in `versioning.yaml`:

```yaml
# Branch behavior
branch_types:
  feature/*:
    prerelease: alpha
    bump: minor
  hotfix/*:
    bump: patch

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

# Ignored patterns
ignore:
  files:
    - "*.md"
    - "docs/**"
  commits:
    - "^chore:"
    - "^docs:"
```

## ✅ Quality Gates

Before releasing:
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog preview looks correct
- [ ] Version bump makes sense for changes
- [ ] No breaking changes in minor releases

## 🆘 Troubleshooting

### Version bump not suggested?
- Check if changes are in ignored files/commits
- Verify commit messages follow conventional format

### Wrong version suggested?
- Check branch naming matches patterns
- Review conventional commit messages

### Changelog not updating?
- Ensure you're on the `main` branch
- Check template file exists and is valid
