default: check

check: lint typecheck test

lint:
    uv run ruff check

typecheck:
    uv run pyright

test:
    uv run pytest

test-file FILE:
    uv run pytest {{FILE}} -v

serve:
    uv run python manage.py serve --reload

build:
    uv run python manage.py build