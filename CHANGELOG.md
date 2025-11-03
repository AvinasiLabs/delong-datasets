# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Additional export formats (HDF5, Arrow)
- Progress callbacks for downloads
- Caching layer for frequently accessed datasets
- Batch download API
- Dataset metadata introspection

---

## [0.1.0] - 2025-11-04

### Added
- Initial release of delong-datasets library
- TEE (Trusted Execution Environment) attestation support
- Zero-trust client architecture
- Automatic environment detection (local vs TEE)
- Column filtering for selective data access
- Pagination support with offset and limit
- Streaming mode for memory-efficient processing
- Data export to CSV, JSON, and Parquet formats
- Python API with `download_dataset()` function
- CLI interface with `download` and `export` commands
- Mock services for local testing and development
- Comprehensive documentation:
  - User Guide
  - Quick Start Guide
  - Architecture documentation
  - Migration Guide
- Complete example suite:
  - Basic usage
  - Column filtering and pagination
  - Streaming large datasets
  - Data export
  - Error handling
- End-to-end test suite
- Policy enforcement for data export limits

### Security
- Remote attestation flow implementation
- Backend-controlled authorization
- Graceful degradation (sample data in non-TEE environments)
- Export policy enforcement

### Documentation
- Complete USER_GUIDE.md with all features
- QUICKSTART.md for testing
- ARCHITECTURE.md for system design
- PUBLISHING_GUIDE.md for maintainers
- 5 runnable example scripts
- README with quick links

### Developer Experience
- Mock dataset backend (FastAPI)
- Mock attestation service
- Mock TEE attestor
- Automated startup scripts
- Environment configuration helpers

### Dependencies
- datasets >= 2.14 (HuggingFace datasets library)
- Optional: fastapi, uvicorn for mock services

---

## Version History

### Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward-compatible)
- **PATCH** version: Bug fixes (backward-compatible)

### Pre-1.0.0 Releases

During initial development (0.x.x versions):
- API may change between minor versions
- Breaking changes will be documented in CHANGELOG
- Upgrade guides provided for significant changes

---

## Migration Notes

### To 0.1.0 (Initial Release)

This is the first public release. Key design decisions:

**Removed from Initial Design:**
- Client-side environment verification (moved to backend)
- Client-side encryption (replaced with remote attestation)
- Two-phase download (replaced with single unified endpoint)
- `pycryptodome` dependency (no longer needed)

**Architecture:**
- Zero-trust client: Client does not verify TEE environment
- Backend authorization: All access decisions made server-side
- Remote attestation: Cipher obtained from remote verification service

---

## Future Roadmap

### 0.2.0 (Next Minor Release)
- [ ] Progress callbacks for large downloads
- [ ] Dataset metadata API
- [ ] Improved error messages
- [ ] Performance optimizations

### 0.3.0
- [ ] Batch download API
- [ ] Local caching layer
- [ ] Resume interrupted downloads

### 1.0.0 (Stable Release)
- [ ] Stable API
- [ ] Production hardening
- [ ] Performance benchmarks
- [ ] Comprehensive test coverage (>90%)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on proposing changes.

---

## Support

For questions or issues:
- Check [USER_GUIDE.md](USER_GUIDE.md) for documentation
- Search [existing issues](https://github.com/your-org/delong-datasets/issues)
- Open a [new issue](https://github.com/your-org/delong-datasets/issues/new)

---

[Unreleased]: https://github.com/your-org/delong-datasets/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/delong-datasets/releases/tag/v0.1.0
