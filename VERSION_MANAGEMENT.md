# Version Management Guide

This document explains how version management works in the Neon CRM SDK project.

## Overview

The project uses [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Breaking changes that are not backward compatible
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and small improvements that are backward compatible

## Automated Version Bumping

### Automatic Patch Bumps

When code is merged to the `main` branch, the patch version is automatically bumped:

- **Trigger**: Push to `main` branch (excluding documentation and CI changes)
- **Bump Type**: Patch (e.g., `1.0.0` → `1.0.1`)
- **Actions**:
  - Updates version in source files
  - Creates git commit with `[skip ci]` to avoid infinite loops
  - Creates git tag (e.g., `v1.0.1`)
  - Updates CHANGELOG.md
  - Triggers release pipeline

### Skip Automatic Bumps

To skip automatic version bumping, include `[skip version]` in your commit message:

```bash
git commit -m "docs: update README [skip version]"
```

## Manual Version Bumping

### Using Make Commands (Recommended)

For local development and manual version management:

```bash
# Show current version
make version-show

# Bump patch version (1.0.0 → 1.0.1)
make version-patch

# Bump minor version (1.0.0 → 1.1.0)
make version-minor

# Bump major version (1.0.0 → 2.0.0)
make version-major
```

### Using GitHub Actions (For Remote)

Trigger manual version bumps via GitHub Actions:

1. **Go to Actions tab** in your GitHub repository
2. **Select "Version Bump"** workflow
3. **Click "Run workflow"**
4. **Choose**:
   - Branch: `main`
   - Bump type: `patch`, `minor`, or `major`
   - Skip tag: `false` (usually)
5. **Click "Run workflow"**

### Using bump-my-version Directly

For direct command-line usage:

```bash
# Show current version
bump-my-version show current_version

# Bump versions
bump-my-version bump patch
bump-my-version bump minor
bump-my-version bump major

# Options
bump-my-version bump minor --dry-run     # See what would happen
bump-my-version bump patch --no-commit   # Don't create git commit
bump-my-version bump major --no-tag      # Don't create git tag
```

## Version Workflow

### Development Workflow

1. **Feature Development**:
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   ```

2. **Create Pull Request**:
   - PR is reviewed and tested
   - CI/CD runs all checks
   - No version bump occurs yet

3. **Merge to Main**:
   ```bash
   git checkout main
   git merge feature/new-feature
   git push origin main
   ```

4. **Automatic Patch Bump**:
   - GitHub Action triggers
   - Version bumps from `1.0.0` to `1.0.1`
   - Git tag `v1.0.1` is created
   - Release pipeline triggers

### Minor/Major Version Workflow

For significant changes requiring minor or major version bumps:

1. **Complete Development**: Finish all features for the release

2. **Manual Version Bump**:
   ```bash
   # For new features (backward compatible)
   make version-minor

   # For breaking changes
   make version-major
   ```

3. **Push Changes**:
   ```bash
   git push origin main
   git push origin --tags
   ```

4. **Release**: The release pipeline automatically triggers when the tag is pushed

## Release Pipeline Integration

Version bumping is tightly integrated with the release pipeline:

1. **Version Bump** → Creates git tag (`v1.2.3`)
2. **Tag Creation** → Triggers release workflow
3. **Release Workflow** → Builds, tests, and publishes to TestPyPI
4. **Manual PyPI Approval** → Optional manual step to publish to PyPI
5. **GitHub Release** → Creates release with changelog

## Configuration Files

### .bumpversion.cfg

Controls how `bump-my-version` updates files:

```toml
[tool.bumpversion]
current_version = "0.1.0"
commit = true
tag = true
tag_name = "v{new_version}"
commit_args = "--no-verify"
message = "bump version: {current_version} → {new_version}"

[[tool.bumpversion.files]]
filename = "src/neon_crm/__init__.py"
search = "__version__ = \"{current_version}\""
replace = "__version__ = \"{new_version}\""

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = "version = \"{current_version}\""
replace = "version = \"{new_version}\""
```

### Version Sources

The version is stored in two places and must be kept in sync:

1. **`src/neon_crm/__init__.py`**:
   ```python
   __version__ = "1.0.0"
   ```

2. **`pyproject.toml`**:
   ```toml
   version = "1.0.0"
   ```

## Best Practices

### When to Bump What

**Patch Version (1.0.0 → 1.0.1)**:
- Bug fixes
- Documentation updates
- Performance improvements
- Internal refactoring
- Security patches

**Minor Version (1.0.0 → 1.1.0)**:
- New features
- New API endpoints
- Deprecations (with backward compatibility)
- Significant improvements

**Major Version (1.0.0 → 2.0.0)**:
- Breaking API changes
- Removed deprecated features
- Major architectural changes
- Incompatible changes

### Commit Message Convention

Use conventional commits for clarity:

```bash
# Patch-worthy changes
git commit -m "fix: resolve authentication timeout issue"
git commit -m "docs: update API examples"
git commit -m "perf: optimize pagination queries"

# Minor-worthy changes
git commit -m "feat: add webhook management support"
git commit -m "feat: add custom field filtering"

# Major-worthy changes
git commit -m "feat!: redesign client initialization API"
git commit -m "feat: remove deprecated v1 compatibility layer"
```

### Version Planning

1. **Plan Releases**: Group related changes into logical releases
2. **Communicate Changes**: Update CHANGELOG.md with detailed notes
3. **Test Thoroughly**: Ensure all tests pass before version bumps
4. **Document Breaking Changes**: Clearly document any breaking changes

## Troubleshooting

### Version Mismatch

If versions get out of sync between files:

```bash
# Check current versions
make version-show
grep version pyproject.toml

# Fix manually or use bump-my-version
bump-my-version bump patch --dry-run  # Check what would happen
```

### Failed Version Bump

If a version bump fails:

1. **Check Git Status**: Ensure working directory is clean
2. **Check Permissions**: Ensure you can create commits and tags
3. **Check Branch**: Ensure you're on the correct branch
4. **Manual Fix**: Update versions manually if needed

### Rollback Version

To rollback a version bump:

```bash
# Reset to previous commit (before version bump)
git reset --hard HEAD~1

# Delete the tag if it was created
git tag -d v1.0.1
git push origin :refs/tags/v1.0.1  # Delete remote tag
```

## Examples

### Complete Feature Release Example

```bash
# 1. Develop feature
git checkout -b feature/webhook-support
# ... make changes ...
git commit -m "feat: add webhook management endpoints"
git commit -m "test: add webhook tests"
git commit -m "docs: add webhook examples"

# 2. Create PR and merge
# ... PR review and merge to main ...
# Automatic patch bump: 1.0.0 → 1.0.1

# 3. Decide this warrants a minor version
make version-minor  # 1.0.1 → 1.1.0
git push origin main --tags

# 4. Release pipeline triggers automatically
```

### Hot Fix Example

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-bug
git commit -m "fix: resolve critical authentication bug"

# 2. Merge to main
# ... merge PR ...
# Automatic patch bump: 1.1.0 → 1.1.1

# 3. Release happens automatically
```

## PyPI Publishing Control

The release pipeline now includes manual control over PyPI publishing:

### Automatic (Tag-based)
When you push a version tag, the pipeline will:
1. Build and test the package
2. Publish to TestPyPI automatically
3. Create a GitHub release
4. **Require manual approval** to publish to PyPI

### Manual Release
You can also trigger releases manually via GitHub Actions:
1. Go to **Actions** → **Release** workflow
2. Click **"Run workflow"**
3. Enter the tag (e.g., `v1.0.0`)
4. Choose whether to publish to PyPI
5. Click **"Run workflow"**

This gives you full control over when packages go live on PyPI while still automating the build and test process.

---

This version management system ensures consistent, automated, and reliable versioning for the Neon CRM SDK while providing flexibility for different release scenarios and manual control over PyPI publishing.
