# Testing Documentation

This directory contains documentation for the Galleria testing infrastructure and patterns.

## Testing Files

- [patterns.md](patterns.md) - Testing patterns and best practices (planned)

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
├── services/           # Service layer tests
│   └── test_*.py
└── command/            # Command layer tests  
    └── test_*.py
```

See [doc/CONTRIBUTE.md](../CONTRIBUTE.md) for development workflow and testing requirements.