# Galleria

Static photo gallery system with Django-style commands, timezone-corrected EXIF processing, and S3 deployment pipeline.

## Quick Start

```bash
# Complete deployment pipeline  
uv run python manage.py process-photos
uv run python manage.py build
uv run python manage.py deploy --setup-cors
```

## Documentation

### Essential Documents

Read these in small sections as they can be long:

- **[TODO](doc/TODO.md)** - Current development tasks and pending work
- **[CHANGELOG](doc/CHANGELOG.md)** - Implementation history and completed features  
- **[System Overview](doc/architecture/overview.md)** - Core architecture and components

### Setup & Deployment

- **[Production Setup](doc/deployment/production-setup.md)** - First-time deployment configuration
- **[Deployment Workflow](doc/deployment/workflow.md)** - Regular deployment commands
- **[Documentation Index](doc/README.md)** - Complete documentation overview

### Development

- **[Contributing Guidelines](doc/CONTRIBUTE.md)** - Development workflow and standards
- **[Settings System](doc/settings.md)** - Configuration and environment variables

## Architecture

Django-style command structure with:
- **Photo Processing**: EXIF timezone correction with dual timezone system
- **Static Site Generation**: Custom generator with Jinja2 templates  
- **Deployment Pipeline**: Hash-based selective uploads with CORS management
- **Storage**: Hetzner S3 with BunnyCDN for global distribution