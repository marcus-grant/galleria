# Salvage

Modules pulled out of the build and test tree, held for a decision
rather than deleted.

Nothing here is part of Galleria.
Each module is waiting on a call about whether it holds anything worth
keeping, and where that thing belongs.
Some of it is likely useful to other projects in the ecosystem, in
particular NormPic, which does the photo processing this code was
written for.
This directory is expected to empty as those calls are made.

It is excluded from linting and type checking, and sits outside
pytest's collection path, so nothing here runs or gates a commit.

## Contents

Each entry is what the module is, and what it looks like it belongs to.
Deciding that is Marcus's call, not a matter of record here.

### src/

- `collection_stats.py` - reports camera, timestamp, and timezone stats
  over a collection. Looks like NormPic.
- `deploy.py` - S3 deploy command, CORS setup, dual-bucket handling.
  Looks like the pipeline orchestrator.
- `deployment.py` - hash comparison, upload planning, metadata-last
  ordering. Looks like the pipeline orchestrator.
- `find_samples.py` - selects representative photos from a collection.
  Looks like NormPic, possibly as an out-of-band script rather than
  suite coverage.
- `upload_photos.py` - S3 upload command with config validation and
  progress reporting. Looks like the pipeline orchestrator.

### test/

- `test_complete_metadata_pipeline.py` - processing settings,
  deployment hashes, timezone effects on hashes. Looks like NormPic.
- `test_deploy.py` - deploy command against mocked storage.
- `test_deploy_integration.py` - deploy workflows, plus six skips for
  progress reporting, confirmation, error recovery, and atomic
  operations. The skips read as a feature list.
- `test_deploy_settings_migration.py` - settings format migration and
  dual-bucket detection.
- `test_e2e_find_samples_edge_cases.py` - empty directories, odd names,
  missing EXIF.
- `test_file_processing.py` - mostly placeholders for unimplemented
  batch metadata work. Its one passing test reads a production metadata
  file from a configured path, so its result depends on machine state.
- `test_find_samples.py` - find-samples basics.
- `test_find_samples_integration.py` - directory scanning, nested
  directories, mixed media.
- `test_find_samples_json.py` - find-samples JSON output shape.
- `test_performance_real_photos.py` - benchmarks against a real
  collection, dependent on a configured path.
- `test_process_photos_performance.py` - fifty synthetic JPEGs through
  process-photos four times. 44.5 seconds on its own.
- `test_real_world_validation.py` - EXIF behavior against real photos:
  camera detection, burst sequences, timestamps.
- `test_s3_storage.py` - storage client, upload, skip-if-exists,
  against a mock storage service.
- `test_upload_photos.py` - upload command against mocked storage.

### doc/

Documentation for the modules above, moved with them.
Removed from the documentation index, so nothing in `doc/` links here.

- `deploy.md` - the deploy command's reference documentation.
- `deployment.md` - the deployment service: change detection, upload
  planning, atomic operations.
- `s3_storage.md` - the storage service: streaming uploads, CORS
  management, in-memory EXIF modification.
- `exif_modification.md` - in-memory EXIF modification with dual
  timezone handling, part of the storage service.

### prior-split/

An uncleared buffer from an earlier point in this project's history.
These modules started here and were set aside as suspected NormPic
work, before the split that produced NormPic as it now exists.

It keeps its original `src/`, `test/`, and `doc/` layout rather than
being folded into the lists above, because its contents predate them
and overlap: `s3_storage`, `file_processing`, and `exif_modification`
appear in both.

Two things are likely true of it.
It duplicates code that still lives in Galleria, and NormPic as it
exists today probably does not want what is here.
That makes it the weakest salvage candidate of the three directories,
and the most likely to be discarded outright.

### Special

The EXIF and photo-processing coverage is the most likely to be worth
moving rather than discarding: NormPic owns that work now, and these
tests encode expectations about timestamps, camera detection, and burst
sequences derived from a real collection.
The open question there is how they run without slowing a suite, since
several need a real collection and one takes 44 seconds.

The synthetic-JPEG fixtures these modules rely on may be worth
extracting on their own, independent of the tests around them.
