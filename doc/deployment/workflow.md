# Deployment Workflow

## Regular Deployment Commands

```bash
# Process 645 wedding photos with timezone corrections
uv run python manage.py process-photos

# Generate static gallery site  
uv run python manage.py build

# Deploy to production S3 bucket with CORS setup
uv run python manage.py deploy --setup-cors
```

## Command Options

### process-photos
- `--batch-size`: Memory management (default: 50 photos)
- `--resume`: Continue from interrupted processing
- `--restart`: Start fresh, removing partial files

### deploy
- `--setup-cors`: Configure bucket CORS rules for web access
- `--dry-run`: Show deployment plan without executing
- `--photos-only`: Upload only photos/metadata (skip static site)
- `--site-only`: Upload only static site files (skip photos)

## Idempotency

All commands are designed to be idempotent - running them multiple times is safe. The deploy command handles all upload operations to maintain consistency.