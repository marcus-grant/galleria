# System Overview

Galleria is a photo gallery system with a Django-style command structure and functional paradigms.

### Key System Components

- **EXIF processing**: Timezone correction with dual timezone system
- **Metadata system**: Complete gallery metadata with all processing settings recorded  
- **Deployment pipeline**: Hash-based selective uploads with CORS validation
- **Test isolation**: `GALLERIA_TEST_MODE=1` prevents local settings pollution

### Core Files to Understand

- `src/models/photo.py` - PhotoMetadata structure with dual hashes
- `src/services/s3_storage.py` - modify_exif_in_memory() function and CORS management
- `src/services/file_processing.py` - Lines 258-285: deployment hash calculation
- `src/services/deployment.py` - Deployment orchestration with metadata-last upload ordering
- `settings.py` - Line 58: TARGET_TIMEZONE_OFFSET_HOURS setting

### Dual Timezone System

**TIMESTAMP_OFFSET_HOURS**: Corrects systematic camera time errors
- Example: Camera was set 2 hours fast → offset = -2 to correct

**TARGET_TIMEZONE_OFFSET_HOURS**: Sets actual timezone context for deployment
- Writes timezone info to EXIF `OffsetTimeOriginal` field per EXIF 2.31 standard
- Format: `±HH:MM` (e.g., `-05:00` for EST, `+02:00` for CET)
- Special value 13 = preserve original timezone (don't modify `OffsetTimeOriginal`)

**Combined Logic**: corrected timestamp + timezone context = complete local time information

### Commands Implemented

- `find-samples` - Photo collection analysis and edge case detection
- `upload-photos` - S3 photo upload with progress tracking  
- `process-photos` - Complete photo processing pipeline with timezone correction
- `deploy` - Full gallery deployment with CORS management

### Test Coverage

329/329 tests passing. All UX enhancement features implemented and validated.