# CI/CD Pipeline Setup Guide

This document explains how to set up and configure the professional-grade CI/CD pipeline for the Neon CRM Python SDK.

## Overview

The CI/CD pipeline includes:

- **Continuous Integration**: Automated testing, code quality checks, and security scanning
- **Continuous Deployment**: Automated publishing to PyPI
- **Security**: Comprehensive security scanning and vulnerability management
- **Documentation**: Automated documentation generation and deployment
- **Quality Assurance**: Code coverage, dependency management, and compliance checks

## Required Setup Steps

### 1. GitHub Repository Setup

1. **Create Repository**: Push your code to GitHub
2. **Enable GitHub Pages**: Go to Settings → Pages → Source: GitHub Actions
3. **Set Branch Protection**: Protect main/develop branches

### 2. PyPI Publishing Setup

#### Option A: Trusted Publishing (Recommended)

1. **Go to PyPI**: https://pypi.org/manage/account/publishing/
2. **Add Trusted Publisher**:
   - PyPI project name: `neon-crm-sdk`
   - Owner: `mdassow`
   - Repository name: `neon-crm-python-sdk`
   - Workflow name: `release.yml`
   - Environment name: `pypi`

3. **Add TestPyPI Trusted Publisher**:
   - Go to: https://test.pypi.org/manage/account/publishing/
   - Use same settings as above but environment name: `testpypi`

#### Option B: API Tokens (Alternative)

If you prefer API tokens:

1. **Generate PyPI Token**: https://pypi.org/manage/account/token/
2. **Add GitHub Secrets**:
   ```
   PYPI_API_TOKEN: your-pypi-token
   TEST_PYPI_API_TOKEN: your-test-pypi-token
   ```

### 3. GitHub Secrets Configuration

Add these secrets in GitHub Settings → Secrets and variables → Actions:

#### Required Secrets:
```bash
# For integration tests (optional)
NEON_ORG_ID: your-neon-org-id
NEON_API_KEY: your-neon-api-key

# For security notifications (optional)
SECURITY_EMAIL: security@your-domain.com
```

#### Environment Setup:
Create these environments in GitHub Settings → Environments:

1. **testpypi**:
   - Required reviewers: yourself
   - Deployment protection rules: enabled

2. **pypi**:
   - Required reviewers: yourself
   - Deployment protection rules: enabled

### 4. Codecov Setup (Optional)

1. **Sign up**: https://codecov.io/ with your GitHub account
2. **Add Repository**: Add your repository to Codecov
3. **Get Token**: Copy your repository upload token
4. **Add Secret**: Add `CODECOV_TOKEN` to GitHub secrets

### 5. Security Scanning Setup

The pipeline includes automatic security scanning:

- **CodeQL**: GitHub's semantic code analysis
- **Dependency Review**: Automated dependency vulnerability scanning
- **Secret Scanning**: Detection of leaked secrets
- **OSSF Scorecard**: Open source security scorecard
- **Trivy**: Container vulnerability scanning

No additional setup required - these are automatically configured.

## Workflow Files

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to main/develop, Pull requests
**Features**:
- Multi-platform testing (Ubuntu, Windows, macOS)
- Multi-Python version testing (3.9-3.13)
- Pre-commit hooks validation
- Unit testing with coverage
- Security scanning
- Build verification

### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers**: Version tags (v*.*.*)
**Features**:
- Version validation
- Full test suite execution
- Security checks
- TestPyPI deployment
- PyPI deployment
- GitHub release creation
- Changelog generation

### 3. Security Workflow (`.github/workflows/security.yml`)

**Triggers**: Daily schedule, Push to main, Pull requests
**Features**:
- CodeQL analysis
- Dependency vulnerability scanning
- Secret detection
- License compliance checking
- Container security scanning
- SBOM generation

### 4. Documentation Workflow (`.github/workflows/docs.yml`)

**Triggers**: Push to main, Documentation changes
**Features**:
- Automatic documentation generation
- API reference creation
- GitHub Pages deployment
- MkDocs-based documentation

## Release Process

### 1. Prepare Release

1. **Update Version**: Update version in `src/neon_crm/__init__.py`
2. **Update Changelog**: Add release notes to `CHANGELOG.md`
3. **Create PR**: Create pull request with changes
4. **Review & Merge**: Get review and merge to main

### 2. Create Release

1. **Create Tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Automatic Process**:
   - CI/CD pipeline triggers automatically
   - Tests run on all platforms
   - Security checks execute
   - Package builds and validates
   - Publishes to TestPyPI first
   - Tests installation from TestPyPI
   - Publishes to PyPI
   - Creates GitHub release

### 3. Post-Release

- GitHub release created automatically
- Documentation updated
- Package available on PyPI
- Release notifications sent

## Monitoring and Maintenance

### 1. Dependabot

Configured in `.github/dependabot.yml`:
- Weekly dependency updates
- Security vulnerability alerts
- Automatic pull requests for updates

### 2. Security Monitoring

- Daily security scans
- Vulnerability alerts
- Dependency review on PRs
- Secret scanning

### 3. Quality Metrics

- Code coverage tracking
- Performance monitoring
- Security scorecard
- License compliance

## Troubleshooting

### Common Issues

1. **Release Fails**:
   - Check version consistency in `pyproject.toml` and `__init__.py`
   - Verify tag format matches `v*.*.* `pattern
   - Check PyPI trusted publishing setup

2. **Tests Fail**:
   - Check Python version compatibility
   - Verify all dependencies are specified
   - Check for platform-specific issues

3. **Security Scan Failures**:
   - Review security alerts in GitHub
   - Update vulnerable dependencies
   - Fix code security issues

4. **Documentation Build Fails**:
   - Check MkDocs configuration
   - Verify all referenced files exist
   - Check for broken links

### Getting Help

1. **Check Workflow Logs**: View detailed logs in GitHub Actions
2. **Review Documentation**: Check this guide and inline comments
3. **Security Issues**: Follow security policy in `.github/SECURITY.md`
4. **Bug Reports**: Use issue templates in `.github/ISSUE_TEMPLATE/`

## Best Practices

### Development Workflow

1. **Use Feature Branches**: Create feature branches for development
2. **Write Tests**: Add tests for all new functionality
3. **Security First**: Run security checks locally
4. **Documentation**: Update docs with changes
5. **Version Management**: Follow semantic versioning

### Release Management

1. **Test Thoroughly**: Always test in trial environment first
2. **Version Tags**: Use semantic version tags
3. **Changelog**: Maintain detailed changelog
4. **Communication**: Notify users of breaking changes

### Security

1. **Regular Updates**: Keep dependencies updated
2. **Scan Regularly**: Review security scan results
3. **Secret Management**: Never commit secrets
4. **Principle of Least Privilege**: Minimize permissions

## Configuration Files

- **CI/CD**: `.github/workflows/*.yml`
- **Dependencies**: `.github/dependabot.yml`
- **Security**: `.github/SECURITY.md`
- **Coverage**: `codecov.yml`
- **Pre-commit**: `.pre-commit-config.yaml`
- **Project**: `pyproject.toml`

This comprehensive CI/CD pipeline ensures your Neon CRM SDK maintains high quality, security, and reliability standards throughout its development lifecycle.
