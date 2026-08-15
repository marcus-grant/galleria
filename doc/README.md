# Galleria Documentation

Static photo gallery system with Django-style commands and functional paradigms.

## Status Documents

- **[TODO](TODO.md)** - Current development tasks and pending work
- **[CHANGELOG](CHANGELOG.md)** - Completed features and implementation history

## Core Documentation

- **[Architecture](architecture/)** - System design and component overview
- **[Deployment](deployment/)** - Production setup and deployment workflows
- **[Guides](guides/)** - Setup guides for CDN, storage, and development
- **[Plan](plan/)** - Planning documents beyond current TODO items.

## Reference

- **[Contributing Guidelines](CONTRIBUTE.md)** - Development workflow and standards
- **[Quality Assurance](QA.md)** - How changes are verified before submission
- **[Settings System](settings.md)** - Configuration and environment variables

## Quick Start

```bash
# Complete deployment pipeline
uv run python manage.py process-photos
uv run python manage.py build  
uv run python manage.py deploy --setup-cors
```

See [deployment/production-setup.md](deployment/production-setup.md)
for detailed setup instructions.
