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

It is excluded from linting and is outside pytest's collection path,
so nothing here runs or gates a commit.

## Contents

### test/

Test modules removed because they dominated suite runtime, together
accounting for roughly 64 of the 85 seconds the suite took before the
move.

- `test_process_photos_performance.py`
  Builds 50 synthetic JPEGs and runs process-photos four times.
  44.5 seconds on its own.
- `test_real_world_validation.py`
  EXIF behavior against a real photo collection.
  Depends on a configured collection path and skips when absent.
- `test_performance_real_photos.py`
  Performance benchmarks against a real photo collection.
  Same dependency and skip behavior.
- `test_s3_storage.py`
  Object-storage client behavior against a mock AWS service.
  Storage and deployment belong to the pipeline orchestrator, not
  here.
- `test_file_processing.py`
  Mostly placeholders for unimplemented batch-metadata work.
  Its one passing test reads a production metadata file from a
  configured path, so its result depends on machine state.

The EXIF and photo-processing coverage is the most likely candidate to
be worth moving rather than discarding: NormPic now owns that work, and
these tests encode expectations about timestamps, camera detection, and
burst sequences that were derived from a real collection.

The synthetic-JPEG fixtures these modules rely on may also be worth
extracting on their own, independent of the tests around them.