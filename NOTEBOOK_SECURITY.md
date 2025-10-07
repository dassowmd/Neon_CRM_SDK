# Jupyter Notebook Security Guidelines

## 🔒 Preventing Sensitive Data Exposure

This project has multiple layers of protection to prevent accidentally committing sensitive data in Jupyter notebooks.

## Automated Protection Layers

### 1. **Pre-commit Hooks** (Automatic)
- **nbstripout**: Automatically strips all outputs, execution counts, and sensitive metadata
- **detect-secrets**: Scans for API keys, tokens, passwords, and other secrets
- **nbqa-ruff**: Applies code quality checks to notebook cells

### 2. **Git Filters** (Automatic)
- All `.ipynb` files automatically use `nbstripout` filter
- Outputs and metadata are stripped before commit
- Clean notebooks are stored in Git history

### 3. **CI/CD Scanning** (Automatic)
- TruffleHog secret detection in CI pipeline
- Security scans on every commit
- Blocks merges if secrets are detected

## Best Practices for Developers

### ✅ DO
```python
# Use environment variables for secrets
import os
api_key = os.environ.get('NEON_API_KEY')

# Use placeholder values in examples
client = NeonClient(
    org_id="your_org_id_here",
    api_key="your_api_key_here"  # pragma: allowlist secret
)

# Tag cells that should be stripped
# Add cell tag: "sensitive" or "remove"
```

### ❌ DON'T
```python
# Never hardcode real secrets
api_key = "live_key_abcd1234567890"  # ❌ BAD  # pragma: allowlist secret

# Don't include real data in examples
org_id = "12345"  # ❌ Real org ID
customer_data = {"email": "john@company.com"}  # ❌ Real data
```

## Cell Tagging for Sensitive Content

Add tags to notebook cells to control what gets stripped:

1. **In Jupyter**: View → Cell Toolbar → Tags
2. **Add these tags**:
   - `sensitive`: Will be stripped by nbstripout
   - `remove`: Will be dropped entirely
   - `example-only`: Marked as non-production code

## Verification Commands

```bash
# Check if notebooks are clean
just clean-notebooks

# Scan for secrets manually
detect-secrets scan .

# Test pre-commit hooks
pre-commit run --all-files
```

## Emergency: If You Accidentally Commit Secrets

1. **Immediately rotate the compromised credentials**
2. **Remove from Git history**:
   ```bash
   # WARNING: This rewrites history
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/notebook.ipynb' \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (coordinate with team)
4. **Update the secrets baseline**

## Configuration Files

- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `.nbstripout_config`: Notebook stripping rules
- `.gitattributes`: Git filter configuration
- `.secrets.baseline`: Known false-positive secrets

## Testing Notebook Security

```bash
# Create a test notebook with fake secrets
echo '{"cells":[{"source":["api_key=\\"fake_key_123\\""]}]}' > test.ipynb

# Run security checks
pre-commit run detect-secrets --files test.ipynb
pre-commit run nbstripout --files test.ipynb

# Clean up
rm test.ipynb
```

## Support

If you have questions about notebook security or encounter issues:
1. Check the CI logs for specific secret detection failures
2. Review the `.secrets.baseline` file for false positives
3. Contact the development team for help with complex cases
