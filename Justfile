default: check

check: lint typecheck test

lint:
    uv run ruff check

typecheck:
    uv run pyright

test *ARGS:
    uv run pytest {{ARGS}}

test-file FILE:
    uv run pytest {{FILE}} -v

clean-install:
    rm -rf "{{justfile_directory()}}/build" "{{justfile_directory()}}/src/galleria.egg-info"
    uv run --isolated --no-project --refresh-package galleria --directory "$(mktemp -d)" --with "{{justfile_directory()}}" python "{{justfile_directory()}}/script/check_clean_install.py" "{{justfile_directory()}}/fixture/collection/manifest.json"

build:
    uv run python -m galleria build

vendor-pico VERSION:
    uv run python script/vendor_pico.py {{VERSION}}
