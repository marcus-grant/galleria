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

serve:
    uv run python -m galleria serve --reload

build:
    uv run python -m galleria build
