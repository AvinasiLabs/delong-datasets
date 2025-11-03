# Publishing to PyPI Guide

Step-by-step guide to publishing the delong-datasets package to PyPI (Python Package Index).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Configuration](#project-configuration)
3. [Pre-Publication Checklist](#pre-publication-checklist)
4. [Building the Package](#building-the-package)
5. [Testing on TestPyPI](#testing-on-testpypi)
6. [Publishing to PyPI](#publishing-to-pypi)
7. [Post-Publication](#post-publication)
8. [Automation with GitHub Actions](#automation-with-github-actions)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Create PyPI Accounts

**PyPI (Production)**
1. Visit https://pypi.org/account/register/
2. Create an account
3. Verify your email

**TestPyPI (Testing)**
1. Visit https://test.pypi.org/account/register/
2. Create a separate account
3. Verify your email

**Note**: TestPyPI and PyPI are separate - you need accounts on both.

### 2. Enable Two-Factor Authentication (Recommended)

1. Go to Account Settings on both PyPI and TestPyPI
2. Enable 2FA using an authenticator app
3. Save recovery codes

### 3. Create API Tokens

**For PyPI:**
1. Log into https://pypi.org
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Set scope to "Entire account" (or specific project if exists)
5. Copy and save the token (starts with `pypi-`)

**For TestPyPI:**
1. Log into https://test.pypi.org
2. Repeat the same process
3. Save the token separately

**Security Note**: Never commit tokens to git!

### 4. Install Publishing Tools

```bash
pip install --upgrade pip
pip install build twine
```

---

## Project Configuration

### 1. Review `pyproject.toml`

Ensure all metadata is correct:

```toml
[project]
name = "delong-datasets"
version = "0.1.0"
description = "Life science datasets helper library with secure env policies"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "Apache-2.0"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["datasets", "life-sciences", "tee", "security", "healthcare"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
    "Topic :: Security",
]
dependencies = [
    "datasets>=2.14",
]

[project.optional-dependencies]
mock = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.22",
]

[project.urls]
Homepage = "https://github.com/your-org/delong-datasets"
Documentation = "https://github.com/your-org/delong-datasets#documentation"
Repository = "https://github.com/your-org/delong-datasets"
Issues = "https://github.com/your-org/delong-datasets/issues"

[project.scripts]
delong-datasets = "delong_datasets.cli:main"
```

### 2. Create/Update `LICENSE`

Make sure you have a LICENSE file (Apache 2.0 is already specified).

### 3. Update Version Number

For releases, update version in `pyproject.toml`:

```toml
version = "0.1.0"  # Semantic versioning: MAJOR.MINOR.PATCH
```

**Versioning Guidelines:**
- `0.1.0` - Initial release
- `0.1.1` - Bug fixes
- `0.2.0` - New features (backward compatible)
- `1.0.0` - Stable API

### 4. Create `MANIFEST.in` (Optional)

If you need to include additional files:

```
include README.md
include LICENSE
include QUICKSTART.md
include ARCHITECTURE.md
include USER_GUIDE.md
recursive-include examples *.py
recursive-include docs *.md
```

---

## Pre-Publication Checklist

Before publishing, verify:

- [ ] **Version number** updated in `pyproject.toml`
- [ ] **README.md** is complete and accurate
- [ ] **LICENSE** file exists
- [ ] **All tests pass**: `bash scripts/test_e2e.sh`
- [ ] **Documentation** is up to date
- [ ] **No sensitive data** in code (tokens, passwords, etc.)
- [ ] **Dependencies** are correctly specified
- [ ] **Git repository** is clean and pushed
- [ ] **Tag the release** (optional but recommended)

### Tag the Release (Recommended)

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/
rm -rf build/
rm -rf *.egg-info/
```

### 2. Build the Package

```bash
python -m build
```

This creates two files in `dist/`:
- `delong_datasets-0.1.0.tar.gz` (source distribution)
- `delong_datasets-0.1.0-py3-none-any.whl` (wheel)

### 3. Verify Build Contents

```bash
# Check what's in the wheel
unzip -l dist/delong_datasets-0.1.0-py3-none-any.whl

# Check what's in the source distribution
tar -tzf dist/delong_datasets-0.1.0.tar.gz
```

**Verify:**
- Source code is included
- No sensitive files (credentials, private keys)
- LICENSE and README are included

---

## Testing on TestPyPI

**Always test on TestPyPI before publishing to production PyPI!**

### 1. Configure TestPyPI Credentials

**Option A: Using Token (Recommended)**

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your TestPyPI token

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your PyPI token
```

**Security**: Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

**Option B: Use Environment Variables**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...  # Your token
```

### 2. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

**Expected output:**
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading delong_datasets-0.1.0-py3-none-any.whl
Uploading delong_datasets-0.1.0.tar.gz
```

### 3. Test Installation from TestPyPI

```bash
# Create a fresh virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    delong-datasets

# Test the package
python -c "from delong_datasets import download_dataset; print('Import successful!')"

# Deactivate and remove test environment
deactivate
rm -rf test-env
```

**Note**: `--extra-index-url` is needed because dependencies are on PyPI, not TestPyPI.

### 4. View on TestPyPI

Visit: https://test.pypi.org/project/delong-datasets/

**Check:**
- Description renders correctly
- Links work
- Version is correct
- Dependencies are listed

---

## Publishing to PyPI

### 1. Final Checks

- [ ] Package tested on TestPyPI
- [ ] Installation works from TestPyPI
- [ ] All documentation is correct
- [ ] Version number is final

### 2. Upload to PyPI

```bash
# Using .pypirc configuration
python -m twine upload dist/*

# Or with token directly
python -m twine upload -u __token__ -p pypi-AgEI... dist/*
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading delong_datasets-0.1.0-py3-none-any.whl
Uploading delong_datasets-0.1.0.tar.gz

View at:
https://pypi.org/project/delong-datasets/0.1.0/
```

### 3. Verify Publication

```bash
# Wait a few minutes, then install
pip install delong-datasets

# Test
python -c "from delong_datasets import download_dataset; print('Success!')"
```

### 4. View on PyPI

Visit: https://pypi.org/project/delong-datasets/

---

## Post-Publication

### 1. Create GitHub Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select the tag (e.g., `v0.1.0`)
4. Title: "Release 0.1.0"
5. Description: Copy from CHANGELOG or write release notes
6. Attach the distribution files (optional)
7. Click "Publish release"

### 2. Update Documentation

Add installation instructions to README:

```markdown
## Installation

```bash
pip install delong-datasets
```
```

### 3. Announce the Release

Consider announcing on:
- GitHub Discussions
- Project mailing list
- Social media
- Relevant communities

### 4. Monitor Issues

Watch for:
- Installation issues
- Bug reports
- Feature requests

---

## Automation with GitHub Actions

### Create `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to TestPyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
      run: |
        python -m twine upload --repository testpypi dist/*

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        python -m twine upload dist/*
```

### Setup GitHub Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `PYPI_API_TOKEN` - Your PyPI token
   - `TEST_PYPI_API_TOKEN` - Your TestPyPI token

### Usage

```bash
# Create and push a tag
git tag v0.1.0
git push origin v0.1.0

# Create a GitHub release
# This triggers the workflow automatically
```

---

## Troubleshooting

### Error: "File already exists"

**Problem**: Trying to upload a version that already exists.

**Solution**:
- PyPI doesn't allow re-uploading the same version
- Increment version number in `pyproject.toml`
- Rebuild and upload

### Error: "Invalid or non-existent authentication"

**Problem**: Token is incorrect or expired.

**Solution**:
- Verify token is copied completely
- Regenerate token on PyPI
- Check you're using the right token (TestPyPI vs PyPI)

### Error: "Package name already taken"

**Problem**: Package name is already used by another project.

**Solution**:
- Choose a different name
- Add a prefix/suffix (e.g., `delong-datasets-core`)
- Contact PyPI support if you believe you own the name

### Wheel Building Errors

**Problem**: Build fails with errors.

**Solution**:
```bash
# Check for syntax errors
python -m py_compile src/delong_datasets/*.py

# Verify project structure
tree src/

# Check dependencies
pip install -e .
```

### README Not Rendering on PyPI

**Problem**: README doesn't display correctly.

**Solution**:
- Ensure `readme = "README.md"` in `pyproject.toml`
- Verify README is valid Markdown
- Check for relative links (use absolute URLs for PyPI)
- Test locally: `python -m build` and check the wheel

### Import Errors After Installation

**Problem**: Package installs but imports fail.

**Solution**:
- Verify package structure: `src/delong_datasets/`
- Check `__init__.py` exists
- Test in clean environment
- Review `pyproject.toml` `packages.find` settings

---

## Version Update Workflow

For subsequent releases:

### 1. Update Version

```bash
# In pyproject.toml
version = "0.1.1"  # or 0.2.0, 1.0.0, etc.
```

### 2. Update CHANGELOG

Create `CHANGELOG.md` if it doesn't exist:

```markdown
# Changelog

## [0.1.1] - 2025-11-05

### Added
- New feature X

### Fixed
- Bug in Y component

### Changed
- Updated Z behavior

## [0.1.0] - 2025-11-04

- Initial release
```

### 3. Commit and Tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main v0.1.1
```

### 4. Build and Publish

```bash
rm -rf dist/
python -m build
python -m twine upload --repository testpypi dist/*
# Test installation
python -m twine upload dist/*
```

---

## Security Best Practices

### 1. Protect API Tokens

```bash
# Never commit .pypirc
echo ".pypirc" >> .gitignore

# Use environment variables
export TWINE_PASSWORD=pypi-...

# Or use keyring
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__
```

### 2. Sign Releases (Optional)

```bash
# Generate GPG key if needed
gpg --full-generate-key

# Sign the distribution
gpg --detach-sign -a dist/delong_datasets-0.1.0.tar.gz

# Upload signature
python -m twine upload dist/* --sign
```

### 3. Verify Downloads

Users can verify with:

```bash
pip download delong-datasets --no-deps
pip hash delong_datasets-0.1.0-py3-none-any.whl
```

---

## Quick Reference

### Complete Publication Checklist

```bash
# 1. Prepare
□ Update version in pyproject.toml
□ Update CHANGELOG.md
□ Run tests
□ Commit and push

# 2. Build
rm -rf dist/
python -m build

# 3. Test on TestPyPI
python -m twine upload --repository testpypi dist/*
# Test installation from TestPyPI

# 4. Publish to PyPI
python -m twine upload dist/*

# 5. Tag release
git tag v0.1.0
git push origin v0.1.0

# 6. Create GitHub Release
# Via web interface

# 7. Verify
pip install delong-datasets
python -c "from delong_datasets import download_dataset"
```

---

## Resources

### Official Documentation
- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Python Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/

### Tools
- `build`: https://pypa-build.readthedocs.io/
- `twine`: https://twine.readthedocs.io/
- `setuptools`: https://setuptools.pypa.io/

### Standards
- PEP 517: Build system
- PEP 518: `pyproject.toml`
- PEP 621: Project metadata

---

## Support

If you encounter issues:
1. Check PyPI status: https://status.python.org/
2. Review Python Packaging Guide
3. Ask on Python Packaging Discourse
4. Open an issue on the packaging tools

---

**Good luck with your publication!** 🚀
