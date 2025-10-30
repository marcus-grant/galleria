# Deployment Documentation

This directory contains deployment guides and procedures for Galleria.

## Guides

- **[Production Setup](production-setup.md)** - First-time production deployment configuration
- **[Workflow](workflow.md)** - Regular deployment workflow and commands
- **[Troubleshooting](troubleshooting.md)** - Common deployment issues and solutions

## Quick Reference

```bash
# Complete deployment pipeline
uv run python manage.py process-photos
uv run python manage.py build
uv run python manage.py deploy --setup-cors
```

For detailed setup instructions, see [production-setup.md](production-setup.md).