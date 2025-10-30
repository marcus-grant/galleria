# Production Setup Guide

**READY TO DEPLOY**: The system is production-ready. Follow these steps for first deployment:

## Step 1: Configure Production Settings

Add to `settings.local.py`:

```python
# S3 Production Configuration  
S3_PUBLIC_ENDPOINT = "https://eu-central-1.s3.hetznerobjects.com"  # Your actual endpoint
S3_PUBLIC_BUCKET = "your-actual-bucket-name"  # From bucket setup
S3_PUBLIC_REGION = "eu-central-1"  # Your bucket region

# Photo Processing Settings
TIMESTAMP_OFFSET_HOURS = -4  # Your camera systematic correction
TARGET_TIMEZONE_OFFSET_HOURS = -5  # Target timezone (e.g., EST = -5, CET = +1)
```

## Step 2: Set Environment Variables for Secrets

```bash
export GALLERIA_S3_PUBLIC_ACCESS_KEY="your_access_key"
export GALLERIA_S3_PUBLIC_SECRET_KEY="your_secret_key"
```

## Step 3: Complete Deployment Workflow

```bash
# Process photos with timezone corrections
uv run python manage.py process-photos

# Build static site
uv run python manage.py build

# Deploy with automatic CORS setup
uv run python manage.py deploy --setup-cors
```

## What Happens

System processes photos with configured correction, applies target timezone to EXIF, generates dual hashes, validates/configures CORS, and uploads only changed photos using metadata comparison.

## Next Steps

After deployment: CDN setup using `doc/guides/bunnycdn-setup.md`