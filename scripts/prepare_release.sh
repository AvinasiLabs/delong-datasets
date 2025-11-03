#!/usr/bin/env bash
set -euo pipefail

# Prepare package for PyPI release
# Usage: bash scripts/prepare_release.sh [version]

VERSION="${1:-}"

echo "==========================================="
echo "delong-datasets Release Preparation"
echo "==========================================="
echo ""

# Check if version provided
if [ -z "$VERSION" ]; then
    CURRENT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
    echo "Current version: $CURRENT_VERSION"
    echo ""
    echo "Usage: bash scripts/prepare_release.sh <version>"
    echo "Example: bash scripts/prepare_release.sh 0.1.0"
    exit 1
fi

echo "Target version: $VERSION"
echo ""

# Step 1: Check git status
echo "Step 1: Checking git status..."
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: Uncommitted changes detected"
    echo "   Please commit or stash changes before release"
    exit 1
fi
echo "✓ Git working directory is clean"
echo ""

# Step 2: Update version in pyproject.toml
echo "Step 2: Updating version in pyproject.toml..."
sed -i.bak "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak 2>/dev/null || true
echo "✓ Version updated to $VERSION"
echo ""

# Step 3: Run tests
echo "Step 3: Running tests..."
if [ -f "scripts/test_e2e.sh" ]; then
    echo "Starting mock services..."
    bash scripts/start_mock_services.sh > /dev/null 2>&1 || true
    sleep 3

    echo "Running test suite..."
    source set-env.sh > /dev/null 2>&1
    if bash scripts/test_e2e.sh > /tmp/test_output.log 2>&1; then
        echo "✓ All tests passed"
    else
        echo "✗ Tests failed. See /tmp/test_output.log for details"
        tail -50 /tmp/test_output.log
        exit 1
    fi
else
    echo "⚠️  Test script not found, skipping tests"
fi
echo ""

# Step 4: Clean previous builds
echo "Step 4: Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
echo "✓ Build artifacts cleaned"
echo ""

# Step 5: Build package
echo "Step 5: Building package..."
if ! python -m build; then
    echo "✗ Build failed"
    exit 1
fi
echo "✓ Package built successfully"
echo ""

# Step 6: Verify build contents
echo "Step 6: Verifying build contents..."
echo ""
echo "Distribution files:"
ls -lh dist/
echo ""

# Check wheel contents
WHEEL_FILE=$(ls dist/*.whl | head -1)
echo "Wheel contents (first 20 files):"
unzip -l "$WHEEL_FILE" | head -25
echo ""

# Check source distribution
TAR_FILE=$(ls dist/*.tar.gz | head -1)
echo "Source distribution contents (first 20 files):"
tar -tzf "$TAR_FILE" | head -20
echo ""

# Step 7: Check package metadata
echo "Step 7: Checking package with twine..."
if command -v twine &> /dev/null; then
    python -m twine check dist/*
    echo "✓ Package check passed"
else
    echo "⚠️  twine not installed, skipping package check"
    echo "   Install with: pip install twine"
fi
echo ""

# Step 8: Summary
echo "==========================================="
echo "Release Preparation Complete!"
echo "==========================================="
echo ""
echo "Version: $VERSION"
echo "Files created:"
ls -1 dist/
echo ""
echo "Next steps:"
echo ""
echo "1. Review CHANGELOG.md and update if needed"
echo "2. Test on TestPyPI:"
echo "   python -m twine upload --repository testpypi dist/*"
echo ""
echo "3. Test installation from TestPyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ \\"
echo "       --extra-index-url https://pypi.org/simple/ delong-datasets"
echo ""
echo "4. If tests pass, publish to PyPI:"
echo "   python -m twine upload dist/*"
echo ""
echo "5. Tag the release:"
echo "   git add pyproject.toml CHANGELOG.md"
echo "   git commit -m \"Release version $VERSION\""
echo "   git tag -a v$VERSION -m \"Release version $VERSION\""
echo "   git push origin main v$VERSION"
echo ""
echo "6. Create GitHub release at:"
echo "   https://github.com/your-org/delong-datasets/releases/new"
echo ""
echo "For detailed instructions, see PUBLISHING_GUIDE.md"
echo ""
