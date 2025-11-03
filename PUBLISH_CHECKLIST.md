# PyPI Publication Checklist

Quick reference checklist for publishing delong-datasets to PyPI.

---

## One-Time Setup (First Publication)

### 1. Create Accounts
- [ ] Create PyPI account: https://pypi.org/account/register/
- [ ] Create TestPyPI account: https://test.pypi.org/account/register/
- [ ] Verify both email addresses
- [ ] Enable 2FA on both accounts

### 2. Generate API Tokens
- [ ] Create PyPI API token (save as `PYPI_TOKEN`)
- [ ] Create TestPyPI API token (save as `TEST_PYPI_TOKEN`)
- [ ] Store tokens securely (password manager)

### 3. Install Tools
```bash
pip install --upgrade pip build twine
```

### 4. Configure Credentials

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <TEST_PYPI_TOKEN>

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <PYPI_TOKEN>
```

```bash
chmod 600 ~/.pypirc
```

---

## Pre-Release Checklist

### Code Quality
- [ ] All tests pass: `bash scripts/test_e2e.sh`
- [ ] Examples run successfully
- [ ] No lint errors: `ruff check src/`
- [ ] Documentation is up to date

### Version & Metadata
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Update `README.md` if needed
- [ ] Verify all URLs in `pyproject.toml` are correct
- [ ] Check author information

### Files
- [ ] `LICENSE` file exists
- [ ] `README.md` is complete
- [ ] No sensitive data in code (tokens, keys, passwords)
- [ ] `.gitignore` includes build artifacts

### Git
- [ ] All changes committed
- [ ] Repository pushed to GitHub
- [ ] Branch is `main` or `master`

---

## Build Process

### 1. Clean Previous Builds
```bash
rm -rf dist/ build/ *.egg-info/
```

### 2. Build Package
```bash
python -m build
```

### 3. Verify Build
```bash
ls -lh dist/
# Should see:
# - delong_datasets-X.Y.Z.tar.gz
# - delong_datasets-X.Y.Z-py3-none-any.whl
```

### 4. Check Contents
```bash
tar -tzf dist/delong_datasets-*.tar.gz | head -20
unzip -l dist/delong_datasets-*.whl | head -20
```

**Verify:**
- [ ] Source files are included
- [ ] `LICENSE` and `README.md` are included
- [ ] No `.pyc` or `__pycache__` files
- [ ] No sensitive files

---

## Test on TestPyPI

### 1. Upload to TestPyPI
```bash
python -m twine upload --repository testpypi dist/*
```

**Expected output:**
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading delong_datasets-X.Y.Z-py3-none-any.whl
Uploading delong_datasets-X.Y.Z.tar.gz
View at: https://test.pypi.org/project/delong-datasets/X.Y.Z/
```

- [ ] Upload successful

### 2. View on TestPyPI
Visit: https://test.pypi.org/project/delong-datasets/

**Check:**
- [ ] README displays correctly
- [ ] Version number is correct
- [ ] Description is correct
- [ ] Links work
- [ ] Classifiers are appropriate

### 3. Test Installation
```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    delong-datasets

# Test import
python -c "from delong_datasets import download_dataset; print('✓ Import works')"

# Test CLI
python -m delong_datasets --help

# Cleanup
deactivate
rm -rf test-env
```

- [ ] Installation successful
- [ ] Import works
- [ ] CLI works

---

## Publish to PyPI

### 1. Final Checks
- [ ] Tested on TestPyPI
- [ ] All links work
- [ ] Version is correct
- [ ] README renders properly

### 2. Upload to PyPI
```bash
python -m twine upload dist/*
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading delong_datasets-X.Y.Z-py3-none-any.whl
Uploading delong_datasets-X.Y.Z.tar.gz
View at: https://pypi.org/project/delong-datasets/X.Y.Z/
```

- [ ] Upload successful

### 3. Verify on PyPI
Visit: https://pypi.org/project/delong-datasets/

- [ ] Package page looks correct
- [ ] README displays properly
- [ ] All metadata is correct

### 4. Test Installation from PyPI
```bash
pip install delong-datasets
python -c "from delong_datasets import download_dataset; print('✓ Works!')"
```

- [ ] Installation successful
- [ ] Package works correctly

---

## Post-Publication

### 1. Tag Release
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

- [ ] Tag created and pushed

### 2. Create GitHub Release
1. Go to: https://github.com/your-org/delong-datasets/releases
2. Click "Create a new release"
3. Select tag: `v0.1.0`
4. Title: "Release 0.1.0"
5. Copy description from `CHANGELOG.md`
6. Attach dist files (optional)
7. Click "Publish release"

- [ ] GitHub release created

### 3. Update Documentation
- [ ] Verify installation instructions in README
- [ ] Update version badge if applicable
- [ ] Announce on project channels

### 4. Monitor
- [ ] Watch for installation issues
- [ ] Respond to bug reports
- [ ] Monitor download statistics

---

## Troubleshooting

### "File already exists"
- Can't re-upload same version to PyPI
- Increment version number
- Rebuild and upload

### "Invalid authentication"
- Check token is correct
- Regenerate token if needed
- Verify using correct token (TestPyPI vs PyPI)

### Build fails
```bash
# Check syntax
python -m py_compile src/delong_datasets/*.py

# Verify structure
tree src/

# Test installation
pip install -e .
```

### README doesn't render
- Check `readme = "README.md"` in `pyproject.toml`
- Ensure README is valid Markdown
- Use absolute URLs for images

---

## Quick Commands

```bash
# Complete workflow
rm -rf dist/ build/ *.egg-info/
python -m build
python -m twine upload --repository testpypi dist/*
# Test installation...
python -m twine upload dist/*
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

## Next Release Checklist

For version 0.1.1, 0.2.0, etc.:

1. [ ] Update version in `pyproject.toml`
2. [ ] Update `CHANGELOG.md`
3. [ ] Commit changes
4. [ ] Follow "Build Process" above
5. [ ] Follow "Test on TestPyPI" above
6. [ ] Follow "Publish to PyPI" above
7. [ ] Follow "Post-Publication" above

---

## Resources

- **Full Guide**: `PUBLISHING_GUIDE.md`
- **PyPI**: https://pypi.org/project/delong-datasets/
- **TestPyPI**: https://test.pypi.org/project/delong-datasets/
- **GitHub**: https://github.com/your-org/delong-datasets

---

**Status: Ready for Publication** ✅

Version 0.1.0 is ready to publish when you are!
