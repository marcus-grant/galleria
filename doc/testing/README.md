# Testing Documentation

This directory contains documentation for the Galleria testing infrastructure and patterns.

## Testing Overview

Galleria uses pytest with a comprehensive test suite focused on:
- **Unit tests** for individual services and functions

## Key Testing Commands

```bash
# Run all tests
uv run pytest

# Run specific test file with verbose output
uv run pytest test/test_filename.py -v
```

## Test Structure

```
test/
  asset/            # The packaged gallery stylesheet
  command/          # Command layer tests
  config/           # Configuration tests
  debug/            # Debug tooling tests
  models/           # Data model tests
  services/         # Service layer tests
  template/         # Template rendering tests
  vendor/           # Pin tests for vendored files
  conftest.py       # Shared helpers
  test_fixture.py   # The committed fixture collection stays valid
```

## Fixture Collection

`fixture/collection/`, beside `test/`, is a committed six-photo
collection: a manifest and six tiny JPEGs.
`just clean-install` builds it through the installed `galleria` script,
and `test/test_fixture.py` keeps the manifest and its files in step.
It is also meant for the dev loop, as a small collection to build and
look at.

See [doc/CONTRIBUTE.md](../CONTRIBUTE.md) for development workflow and testing requirements.