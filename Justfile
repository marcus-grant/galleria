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
    uv run --isolated --no-project --refresh-package galleria --directory "$(mktemp -d)" --with "{{justfile_directory()}}" python -m galleria build --help > /dev/null

serve:
    uv run python -m galleria serve --reload

build:
    uv run python -m galleria build
