# Photo Collection Processing CLI Tool - Project Split Plan

## Executive Summary

This document specifies the exact modules, functions, classes, and tests that need to be extracted from `static-gallery` into a standalone Python CLI tool for photo collection processing. The new tool will handle EXIF-based organization, timestamp-based renaming, and support both local and S3-compatible remote storage.

**Project Name:** `normpic` (updated from `picflow`)

**Total Lines of Code to Extract:** ~2,400 lines
**Total Test Lines to Extract:** ~800 lines
**Estimated Effort:** 3-5 weeks

**Extraction Status:** ✅ **COMPLETED** (2025-11-06)

---

## Extracted Files Status

### Core Services (6 files) - ✅ EXTRACTED
- `src/services/exif.py` (467 lines) → `deleteme-normpic-modules/src/services/exif.py`
- `src/services/filename_service.py` (281 lines) → `deleteme-normpic-modules/src/services/filename_service.py`
- `src/services/file_processing.py` (483 lines) → `deleteme-normpic-modules/src/services/file_processing.py`
- `src/services/s3_storage.py` (424 lines) → `deleteme-normpic-modules/src/services/s3_storage.py`
- `src/services/photo_validation.py` (74 lines) → `deleteme-normpic-modules/src/services/photo_validation.py`
- `src/services/fs.py` (20 lines) → `deleteme-normpic-modules/src/services/fs.py`

### Data Models (1 file) - ✅ EXTRACTED
- `src/models/photo.py` (193 lines) → `deleteme-normpic-modules/src/models/photo.py`

### Tests (7 files) - ✅ EXTRACTED
- `test/services/test_s3_storage.py` → `deleteme-normpic-modules/test/services/test_s3_storage.py`
- `test/services/test_photo_validation.py` → `deleteme-normpic-modules/test/services/test_photo_validation.py`
- `test/services/test_file_processing_dual.py` → `deleteme-normpic-modules/test/services/test_file_processing_dual.py`
- `test/test_exif.py` → `deleteme-normpic-modules/test/test_exif.py`
- `test/test_filename_service.py` → `deleteme-normpic-modules/test/test_filename_service.py`
- `test/test_fs.py` → `deleteme-normpic-modules/test/test_fs.py`
- `test/test_models.py` → `deleteme-normpic-modules/test/test_models.py`

### Documentation (3 files) - ✅ EXTRACTED
- `doc/services/exif_modification.md` → `deleteme-normpic-modules/doc/services/exif_modification.md`
- `doc/services/file_processing.md` → `deleteme-normpic-modules/doc/services/file_processing.md`
- `doc/services/s3_storage.md` → `deleteme-normpic-modules/doc/services/s3_storage.md`

### Git Hooks (1 file) - ✅ EXTRACTED
- `.git/hooks/commit-msg` → `deleteme-normpic-modules/hooks/commit-msg`

---

## Quick Reference: Files to Extract

### Core Services (6 files)
- `src/services/exif.py` (467 lines) → `normpic/services/exif.py`
- `src/services/filename_service.py` (281 lines) → `normpic/services/filename.py`
- `src/services/file_processing.py` (483 lines) → `normpic/services/processing.py`
- `src/services/s3_storage.py` (424 lines) → `normpic/services/storage.py`
- `src/services/photo_validation.py` (74 lines) → `normpic/services/validation.py`
- `src/services/fs.py` (20 lines) → `normpic/util/filesystem.py`

### Data Models (1 file)
- `src/models/photo.py` (193 lines) → `normpic/models/photo.py`

### Tests (3+ files)
- `test/services/test_s3_storage.py` → `tests/unit/test_storage.py`
- `test/services/test_photo_validation.py` → `tests/unit/test_validation.py`
- `test/services/test_file_processing_dual.py` → `tests/integration/test_processing.py`

---

## Required Modifications for Standalone Operation

### Configuration System Changes

**Current:** Django-style `settings.py` with global imports
```python
import settings
offset = settings.TIMESTAMP_OFFSET_HOURS
```

**New:** TOML configuration with environment variable support
```python
from normpic.config import get_config
config = get_config()
offset = config.timestamp_offset_hours
```

**Files Requiring Changes:**
- `exif.py` lines 6, 26-27 (settings import and usage)
- `file_processing.py` lines 9, 218-223, 236, 275 (settings import and GallerySettings)
- `fs.py` lines 1, 8 (settings import for default paths)

### Import Path Changes

**Pattern:** All `src.*` imports → `normpic.*` imports

**Examples:**
```python
# Before
from src.models.photo import ProcessedPhoto
from src.services import fs, exif
from src.services.filename_service import generate_photo_filename

# After
from normpic.models.photo import ProcessedPhoto
from normpic.services import filesystem, exif
from normpic.services.filename import generate_photo_filename
```

**Files Affected:** All files (global find-replace)

### Dependency Injection for S3 Credentials

**Current:** Reads from global settings
```python
# settings.py approach - coupled to Django/global config
S3_ARCHIVE_ENDPOINT = "..."
```

**New:** Pass credentials explicitly or via config object
```python
from normpic.services.storage import S3Storage

# Option 1: Factory with config
storage = S3Storage.from_config(config.s3_archive)

# Option 2: Explicit credentials
storage = S3Storage(
    endpoint=config.s3_archive.endpoint,
    access_key=config.s3_archive.access_key,
    secret_key=config.s3_archive.secret_key,
    bucket=config.s3_archive.bucket,
    region=config.s3_archive.region
)
```

**Files Requiring Changes:**
- `s3_storage.py` (add class-based interface)
- `file_processing.py` (inject storage dependencies)

### Remove Django Dependencies

**Files to Check:**
- No direct Django imports found in core services ✓
- `manage.py` wrapper NOT needed in new project
- CLI commands will use Click instead of Django management commands

---

## Detailed Extraction Checklist

### File 1: `src/services/exif.py` → `normpic/services/exif.py`

**Extract All Functions (15 functions, 467 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `get_datetime_taken()` | 9-32 | ✅ Extracted | Remove `settings` import, pass `timestamp_offset_hours` as parameter |
| `get_subsecond_precision()` | 35-55 | ✅ Extracted | No changes |
| `get_camera_info()` | 58-77 | ✅ Extracted | No changes |
| `extract_exif_data()` | 80-104 | ✅ Extracted | No changes |
| `combine_datetime_subsecond()` | 107-134 | ✅ Extracted | No changes |
| `has_subsecond_precision()` | 137-145 | ✅ Extracted | No changes |
| `sort_photos_chronologically()` | 148-207 | ✅ Extracted | No changes |
| `is_burst_candidate()` | 210-244 | ✅ Extracted | No changes |
| `detect_burst_sequences()` | 247-297 | ✅ Extracted | No changes |
| `find_timestamp_conflicts()` | 300-347 | ✅ Extracted | No changes |
| `find_missing_exif_photos()` | 350-368 | ✅ Extracted | No changes |
| `get_camera_diversity_samples()` | 371-394 | ✅ Extracted | No changes |
| `extract_filename_sequence()` | 397-433 | ✅ Extracted | No changes |
| `get_timezone_info()` | 436-466 | ✅ Extracted | No changes |

**Dependencies to Preserve:**
- `exifread` - EXIF tag parsing
- `datetime`, `timedelta` - Standard library
- `re` - Regular expressions for filename patterns
- `pathlib.Path` - File path handling
- `typing` - Type hints

**Modifications:**
1. Line 6: Remove `import settings`
2. Lines 26-27: Change from `settings.TIMESTAMP_OFFSET_HOURS` to parameter
3. Function signature change:
   ```python
   # Before
   def get_datetime_taken(photo_path: Union[Path, str]) -> Optional[datetime]:

   # After
   def get_datetime_taken(
       photo_path: Union[Path, str],
       timestamp_offset_hours: int = 0
   ) -> Optional[datetime]:
   ```

---

### File 2: `src/services/filename_service.py` → `normpic/services/filename.py`

**Extract All Functions (9 functions, 281 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `generate_photo_filename()` | 13-57 | ✅ Extracted | Change imports: `src.models` → `normpic.models` |
| `get_timezone_from_gps()` | 60-90 | ✅ Extracted | No changes |
| `format_iso_timestamp()` | 93-103 | ✅ Extracted | No changes |
| `extract_subsecond_timing()` | 106-130 | ✅ Extracted | No changes |
| `extract_filename_sequence_hint()` | 133-165 | ✅ Extracted | No changes |
| `generate_batch_filenames()` | 168-236 | ✅ Extracted | Change imports: `src.models` → `normpic.models` |
| `get_camera_code()` | 239-281 | ✅ Extracted | No changes |

**Dependencies to Preserve:**
- `timezonefinder` - GPS to timezone conversion
- `zoneinfo` - Timezone handling
- `datetime` - Standard library
- Custom: `LEXICAL_BASE32` constant (line 10)

**Modifications:**
1. Line 7: Change `from src.models.photo import ProcessedPhoto, CameraInfo` → `from normpic.models.photo import ...`

---

### File 3: `src/models/photo.py` → `normpic/models/photo.py`

**Extract All Classes & Functions (9 dataclasses + 3 functions, 193 lines total):**

| Class/Function | Lines | Status | Modifications Needed |
|----------------|-------|--------|----------------------|
| `CameraInfo` (dataclass) | 10-14 | ✅ Extracted | No changes |
| `ExifData` (dataclass) | 18-25 | ✅ Extracted | No changes |
| `ProcessedPhoto` (dataclass) | 29-40 | ✅ Extracted | No changes |
| `photo_from_exif_service()` | 43-71 | ✅ Extracted | No changes |
| `MetadataExifData` (dataclass) | 75-82 | ✅ Extracted | No changes |
| `MetadataFileData` (dataclass) | 86-91 | ✅ Extracted | No changes |
| `PhotoMetadata` (dataclass) | 95-103 | ✅ Extracted | No changes |
| `GallerySettings` (dataclass) | 107-115 | ✅ Extracted | Rename to `CollectionSettings` |
| `GalleryMetadata` (dataclass) | 119-154 | ✅ Extracted | Rename to `CollectionMetadata` |
| `photo_to_json()` | 157-165 | ✅ Extracted | No changes |
| `photo_from_json()` | 168-191 | ✅ Extracted | No changes |

**Dependencies to Preserve:**
- `dataclasses` - Standard library
- `datetime` - Standard library
- `pathlib.Path` - Standard library
- `typing` - Type hints

**Modifications:**
1. Rename `GallerySettings` → `CollectionSettings` (better for CLI tool context)
2. Rename `GalleryMetadata` → `CollectionMetadata`
3. Update all references in other files

---

### File 4: `src/services/file_processing.py` → `normpic/services/processing.py`

**Extract Functions (7 functions, 483 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `link_photo_with_filename()` | 12-50 | ✅ Extracted | No changes |
| `create_thumbnail()` | 58-83 | ✅ Extracted | Move THUMBNAIL_SIZE/QUALITY constants to config |
| `process_photo_collection()` | 86-172 | ✅ Extracted | Change imports, inject config |
| `is_processing_needed()` | 175-204 | ✅ Extracted | No changes |
| `generate_gallery_metadata()` | 207-309 | ✅ Extracted | Replace settings access with config parameter |
| `save_gallery_metadata()` | 312-323 | ✅ Extracted | Rename to `save_collection_metadata` |
| `process_dual_photo_collection()` | 326-483 | ✅ Extracted | Change imports, inject config |

**Dependencies to Preserve:**
- `json` - Standard library
- `datetime`, `timezone` - Standard library
- `pathlib.Path` - Standard library
- `PIL/Pillow` - Image processing

**Modifications:**
1. Lines 8-9: Change imports `src.models` → `normpic.models`, `settings` → config injection
2. Lines 54-55: Move to config:
   ```python
   # Before (hardcoded)
   THUMBNAIL_SIZE = 400
   THUMBNAIL_QUALITY = 85

   # After (from config)
   thumb_size = config.thumb_size
   thumb_quality = config.webp_quality
   ```
3. Lines 218-223, 236, 275: Replace `settings.*` with `config.*` parameters
4. Function signatures: Add `config` parameter to functions that need settings

---

### File 5: `src/services/s3_storage.py` → `normpic/services/storage.py`

**Extract Functions (16 functions, 424 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `get_s3_client()` | 12-30 | ✅ Extracted → Refactor | Make into class method |
| `file_exists_in_s3()` | 33-50 | ✅ Extracted → Refactor | Make into instance method |
| `calculate_file_checksum()` | 53-66 | ✅ Extracted | Move to `normpic.util.hash` |
| `upload_file_to_s3()` | 69-133 | ✅ Extracted → Refactor | Make into instance method |
| `list_bucket_files()` | 136-151 | ✅ Extracted → Refactor | Make into instance method |
| `upload_directory_to_s3()` | 154-225 | ✅ Extracted → Refactor | Make into instance method |
| `modify_exif_in_memory()` | 228-281 | ✅ Extracted | No changes (keep as standalone utility) |
| `get_bucket_cors()` | 284-314 | ✅ Extracted → Refactor | Make into instance method |
| `configure_bucket_cors()` | 317-341 | ✅ Extracted → Refactor | Make into instance method |
| `get_default_gallery_cors_rules()` | 344-358 | ✅ Extracted | Keep as module-level function |
| `cors_rules_match()` | 361-384 | ✅ Extracted | Keep as module-level function |
| `examine_bucket_cors()` | 387-424 | ✅ Extracted → Refactor | Make into instance method |

**New Class Structure:**
```python
class S3Storage:
    """S3-compatible storage backend."""

    def __init__(self, endpoint, access_key, secret_key, bucket, region):
        self.client = boto3.client(...)
        self.bucket = bucket
        # ... instance setup

    @classmethod
    def from_config(cls, s3_config):
        """Factory method from config object."""
        return cls(
            endpoint=s3_config.endpoint,
            access_key=s3_config.access_key,
            ...
        )

    def file_exists(self, key: str) -> bool:
        """Check if file exists."""
        # Current: file_exists_in_s3(client, bucket, key)
        # New: self.file_exists(key)

    def upload_file(self, local_path, key, ...):
        """Upload file."""
        # Current: upload_file_to_s3(client, local_path, bucket, key)
        # New: self.upload_file(local_path, key)

    # ... other methods
```

**Dependencies to Preserve:**
- `boto3` - AWS SDK
- `botocore.exceptions` - Error handling
- `PIL/Pillow` - Image processing
- `piexif` - EXIF manipulation
- `hashlib` - Checksums
- `io` - Byte streams

**Modifications:**
1. Refactor all functions into `S3Storage` class
2. Remove `client` and `bucket` parameters (use `self.client`, `self.bucket`)
3. Move `calculate_file_checksum()` to `normpic.util.hash.py`
4. Keep `modify_exif_in_memory()` as module-level utility function

---

### File 6: `src/services/photo_validation.py` → `normpic/services/validation.py`

**Extract Functions (3 functions, 74 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `get_photo_filename_mapping()` | 6-24 | ✅ Extracted | Change import: `src.services.fs` → `normpic.util.filesystem` |
| `validate_matching_collections()` | 27-50 | ✅ Extracted | No changes |
| `get_matched_photo_pairs()` | 53-74 | ✅ Extracted | No changes |

**Modifications:**
1. Line 15: Change `from src.services import fs` → `from normpic.util import filesystem`
2. Line 17: Change `fs.ls_full()` → `filesystem.list_images()`

---

### File 7: `src/services/fs.py` → `normpic/util/filesystem.py`

**Extract Functions (1 function, 20 lines total):**

| Function | Lines | Status | Modifications Needed |
|----------|-------|--------|----------------------|
| `ls_full()` | 6-20 | ✅ Extracted → Refactor | Rename to `list_images()`, remove settings dependency |

**Modifications:**
```python
# Before
def ls_full(path: Optional[str] = None) -> List[Path]:
    if path is None:
        path = settings.PIC_SOURCE_PATH_FULL
    # ...

# After
def list_images(path: str) -> List[Path]:
    """List all image files in directory recursively."""
    path = Path(path)
    # ... rest unchanged
```

---

## Test Files to Extract

### Test 1: `test/services/test_s3_storage.py` → `tests/unit/test_storage.py`

**Test Classes to Extract:**
- `TestS3Client` - S3 client creation
- `TestFileExistence` - File existence checking
- `TestFileUpload` - Single file upload
- `TestDirectoryUpload` - Batch uploads
- `TestExifModification` - In-memory EXIF modification
- `TestCORSManagement` - CORS configuration

**Dependencies:**
- `pytest` - Test framework
- `moto` - AWS service mocking (`@mock_aws` decorator)
- `boto3` - AWS SDK
- `PIL/Pillow` - Image fixtures
- `piexif` - EXIF validation

**Modifications:**
1. Change imports: `from src.services.s3_storage import *` → `from normpic.services.storage import *`
2. Update function names if refactored to class methods
3. Add tests for new `S3Storage` class interface

---

### Test 2: `test/services/test_photo_validation.py` → `tests/unit/test_validation.py`

**Test Classes to Extract:**
- `TestPhotoFilenameMapping` - Filename stem extraction
- `TestValidateMatchingCollections` - Full/web collection validation
- `TestGetMatchedPhotoPairs` - Photo pair matching

**Modifications:**
1. Change imports: `from src.services.photo_validation import *` → `from normpic.services.validation import *`

---

### Test 3: `test/services/test_file_processing_dual.py` → `tests/integration/test_processing.py`

**Test Coverage:**
- Dual collection processing workflow
- Batch processing
- Metadata generation
- Symlink creation
- Thumbnail generation

**Modifications:**
1. Change imports: `src.*` → `normpic.*`
2. Replace settings access with config fixtures
3. Update for new class-based S3 interface

---

## Summary of Modifications

### Critical Changes (Must Do)

1. **Configuration System** - Replace Django `settings.py` with TOML config
   - Affects: All 7 files
   - Effort: 2-3 days

2. **Import Path Updates** - Change `src.*` to `normpic.*`
   - Affects: All files
   - Effort: 1 day (automated find-replace)

3. **S3 Storage Refactoring** - Convert to class-based interface
   - Affects: `s3_storage.py` and all callers
   - Effort: 2-3 days

4. **Settings Dependency Removal** - Inject config instead of global import
   - Affects: `exif.py`, `file_processing.py`, `fs.py`
   - Effort: 1-2 days

### Optional Enhancements (Nice to Have)

1. **Rename Gallery → Collection** - Better terminology for CLI tool
   - Affects: `photo.py` model names
   - Effort: 1 day

2. **CLI Interface** - Add Click-based command system
   - New file: `normpic/cli.py`
   - Effort: 3-5 days

3. **Progress Reporting** - Add Rich library for beautiful output
   - Affects: Processing functions
   - Effort: 1-2 days

---

## Dependencies Summary

### Python Version
- **Minimum:** Python 3.9 (for `zoneinfo` support)
- **Recommended:** Python 3.11+

### Core Dependencies (from current project)
```toml
[project.dependencies]
exifread = "^3.0.0"          # EXIF tag parsing
Pillow = "^10.0.0"           # Image processing
piexif = "^1.1.3"            # EXIF modification
boto3 = "^1.28.0"            # S3 client
timezonefinder = "^6.2.0"    # GPS→timezone
```

### New Dependencies (for standalone CLI)
```toml
click = "^8.1.0"             # CLI framework
toml = "^0.10.2"             # Config parsing
rich = "^13.0.0"             # Terminal UI
pydantic = "^2.0.0"          # Config validation (optional)
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest >= 7.4.0",
    "pytest-cov >= 4.1.0",
    "moto >= 4.2.0",         # AWS mocking
    "black >= 23.0.0",
    "ruff >= 0.1.0",
    "mypy >= 1.5.0",
]
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `normpic` project structure
- [ ] Set up `pyproject.toml` with dependencies
- [ ] Create config system (`normpic/config.py`)
- [ ] Set up pytest structure

### Phase 2: Core Extraction (Week 2)
- [ ] Extract `models/photo.py` with renames
- [ ] Extract `services/exif.py` with config injection
- [ ] Extract `services/filename.py` with import fixes
- [ ] Extract `util/filesystem.py` with refactoring
- [ ] Extract `util/hash.py` (new file for checksums)

### Phase 3: Storage & Processing (Week 3)
- [ ] Extract & refactor `services/storage.py` to class-based
- [ ] Extract `services/validation.py` with import fixes
- [ ] Extract `services/processing.py` with config injection
- [ ] Update all cross-references between modules

### Phase 4: CLI Interface (Week 4)
- [ ] Create `cli.py` with Click commands
- [ ] Implement `process` command
- [ ] Implement `analyze` command
- [ ] Implement `rename` command
- [ ] Implement `upload`/`download` commands
- [ ] Implement `config` command

### Phase 5: Testing (Week 5)
- [ ] Extract and adapt unit tests
- [ ] Extract and adapt integration tests
- [ ] Add new tests for CLI commands
- [ ] Add new tests for config system
- [ ] Achieve >90% code coverage

### Phase 6: Documentation & Release (Optional)
- [ ] Write README with quickstart
- [ ] Write user documentation
- [ ] Write developer documentation
- [ ] Package for PyPI
- [ ] Create GitHub repository
- [ ] Set up CI/CD pipeline

---

## Risk Assessment

### Low Risk
✅ **EXIF services** - No external dependencies, well-tested
✅ **Filename generation** - Pure functions, easy to extract
✅ **Data models** - Simple dataclasses, minimal coupling

### Medium Risk
⚠️ **Configuration system** - New code, needs careful design
⚠️ **S3 storage refactoring** - Class design affects all callers
⚠️ **Test adaptation** - May need fixture refactoring

### High Risk
🔴 **CLI integration** - New interface, user experience critical
🔴 **S3 credential management** - Security-sensitive, must be robust

### Mitigation Strategies
1. **Start with data models** - Lowest risk, establishes foundation
2. **Test continuously** - Port tests alongside code extraction
3. **Use feature flags** - Enable gradual rollout of new features
4. **Security review** - Audit S3 credential handling before release

---

## Success Metrics

### Code Quality
- [ ] 100% of extracted code has passing tests
- [ ] >90% code coverage
- [ ] Zero mypy type errors
- [ ] Zero ruff linting errors

### Functionality
- [ ] All EXIF functions work identically
- [ ] Filename generation produces same results
- [ ] S3 upload/download works with all major providers
- [ ] Batch processing handles 1000+ photo collections

### Usability
- [ ] CLI help text is clear and helpful
- [ ] Error messages are actionable
- [ ] Progress bars show meaningful information
- [ ] Configuration is straightforward

---

## Appendix: File Inventory

### Source Files (Static-Gallery)
```
src/services/exif.py                 467 lines → ✅ Extracted
src/services/filename_service.py     281 lines → ✅ Extracted
src/services/file_processing.py      483 lines → ✅ Extracted
src/services/s3_storage.py           424 lines → ✅ Extracted
src/services/photo_validation.py      74 lines → ✅ Extracted
src/services/fs.py                    20 lines → ✅ Extracted
src/models/photo.py                  193 lines → ✅ Extracted
───────────────────────────────────────────────
TOTAL SOURCE                        1,942 lines → ✅ EXTRACTED
```

### Test Files (Static-Gallery)
```
test/services/test_s3_storage.py     ~300 lines → ✅ Extracted
test/services/test_photo_validation.py ~90 lines → ✅ Extracted
test/services/test_file_processing_dual.py ~400 lines → ✅ Extracted
test/test_exif.py                    ~XXX lines → ✅ Extracted
test/test_filename_service.py        ~XXX lines → ✅ Extracted
test/test_fs.py                      ~XXX lines → ✅ Extracted
test/test_models.py                  ~XXX lines → ✅ Extracted
───────────────────────────────────────────────
TOTAL TESTS                          ~800 lines → ✅ EXTRACTED
```

### New Files (NormPic)
```
normpic/cli.py                       ~400 lines (new)
normpic/config.py                    ~150 lines (new)
normpic/util/hash.py                  ~30 lines (new)
tests/unit/test_config.py            ~100 lines (new)
tests/unit/test_cli.py               ~200 lines (new)
───────────────────────────────────────────────
TOTAL NEW CODE                       ~880 lines
```

### Grand Total
```
Total code to write/adapt:         2,822 lines
Estimated effort:                  3-5 weeks
```

---

**Document Status:** ✅ Extraction completed, ready for refactoring
**Last Updated:** 2025-11-06
**Ready for:** NormPic project creation and refactoring

**Extraction Summary:**
- ✅ All source files extracted (2,400+ lines)
- ✅ All test files extracted (800+ lines)  
- ✅ Documentation extracted
- ✅ Git hooks extracted
- ✅ Package structure created
- ✅ Ready for independent development