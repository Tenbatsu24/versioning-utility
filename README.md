# Python Versioning and Changelog Utility


[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit Hooks](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)[![Semantic Versioning](https://img.shields.io/badge/semantic%20versioning-2.0.0-green.svg)](https://semver.org/)
[![Semantic Versioning](https://img.shields.io/badge/semantic%20versioning-2.0.0-green.svg)](https://semver.org/)
[![Conventional Commits](https://img.shields.io/badge/conventional%20commits-1.0.0-lightgrey.svg)](https://www.conventionalcommits.org/)

This repository includes a pre-push hook utility to ensure your Python package version is **properly bumped** before pushing to `main` or other important branches.
Having generated the version bump, it will also generate a changelog entry in `CHANGELOG.md` with the current date and the new version.

---

## Branch & Versioning Strategy

Our recommended workflow follows **semantic versioning** with pre-release identifiers:

- `feature/*` → `alpha` pre-release
- `beta/*` → `beta` pre-release
- `rc/*` → `rc` pre-release
- `main` → production release

### 1️⃣ Feature Development

- Create a `feature/*` branch for each new feature.
- Work and commit as usual.
- **Versioning:** Auto-increment `alpha` pre-release (e.g., `1.0.0-alpha.1 → 1.0.0-alpha.2`).
- Merge completed features into the corresponding `beta/*` branch when ready for integration testing.

### 2️⃣ Beta Integration

- Create a `beta/*` branch (e.g., `beta/1.0.0`) if it doesn’t exist.
- Merge all completed feature branches.
- **Versioning:** Auto-increment `beta` pre-release (e.g., `1.0.0-beta.1 → 1.0.0-beta.2`).
- Use this branch for **integration testing** and catching issues that only appear when multiple features interact.

### 3️⃣ Release Candidate (RC)

**Purpose:** Even after beta, merging multiple features can introduce subtle regressions or last-minute fixes. RC ensures a **final verification stage** before production.

- Create an `rc/*` branch (e.g., `rc/1.0.0-rc.1`) from the latest beta.
- Apply only **critical fixes** to the RC branch.
- **Versioning:** Auto-increment `rc` pre-release (e.g., `1.0.0-rc.1 → 1.0.0-rc.2`).
- Use RC for QA and final sign-off.

### 4️⃣ Production Release

- Merge the RC branch into `main`.
- Ensure `pyproject.toml` has a **final version** (no pre-release suffix).
- Push to production.

**Versioning:** Final release, e.g., `1.0.0`.

### 5️⃣ Optional Hotfixes

- If a critical bug is found after production release:
  - Create a `hotfix/*` branch from `main`.
  - Apply fix, update version (patch bump).
  - Merge back into `main` and `develop`/`beta` branches as needed.

---

## Visual Branch Flow

### Mermaid Diagram

```mermaid
gitGraph
   commit id: "Initial commit"
   branch feature/login
   commit id: "Add login form (alpha)"
   commit id: "Add login validation (alpha)"
   checkout main
   branch feature/diary
   commit id: "Add bird diary page (alpha)"
   branch beta/1.0.0
   checkout beta/1.0.0
   merge feature/login
   merge feature/diary
   commit id: "Integration testing (beta)"
    branch rc/1.0.0-rc.1
   checkout rc/1.0.0-rc.1
   commit id: "Fix minor bugs (rc)"
   checkout main
   merge rc/1.0.0-rc.1
   commit id: "Release 1.0.0"
````

### ASCII Tree Example

```
main
└─ rc/1.0.0-rc.1
   └─ beta/1.0.0
      ├─ feature/login (alpha)
      │   ├─ Add login form
      │   └─ Add login validation
      └─ feature/diary (alpha)
          └─ Add bird diary page
```

**Flow Summary:**

```
feature/* (alpha) → beta/* (beta) → rc/* (rc) → main (final release)
```

**Notes:**

* Pre-release types: `alpha` → `beta` → `rc`.
* Version bumping is **not** automated by the utility (yet).
* RC ensures stability after beta testing and before production.

---

## Release Workflow

This section outlines the release workflow using the versioning tool and changelog generator.
* [Release Workflow](RELEASE_WORKFLOW.md) for detailed steps on releasing new versions.

---

## Usage

* [Usage instructions](USAGE.md) for the versioning tool and changelog generation.
---

## Tips

* Use **feature branches** for small, incremental changes.
* Use **beta branches** to consolidate multiple features and test integration.
* Use **RC branches** for last-minute fixes and QA before production.
* Use **hotfix branches** for urgent patches to main releases.
* The utility can **auto-bump versions**, but manual bumps are allowed for final releases.

---

This ensures every version bump includes a clear summary of changes.

### Tips

* Follow **conventional commits** for commit messages to ensure proper categorization.
* Use feature branches (`feature/`) to keep changes organized.
* Use pre-release branches (`beta/`, `rc/`) to test changes before merging into `main`.
* Branch summaries help track which branch introduced which changes, useful for larger projects or multiple contributors.


---
## License
This project is licensed under Apache 2.0 - see the [LICENSE](LICENSE) file for details.
