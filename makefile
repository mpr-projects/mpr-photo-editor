.PHONY: develop install test run clean

install:
	pip install .[dev]

develop:
	maturin develop
	pyo3-stubgen mpr_photo_editor.rust_backend .

check:
	mypy mpr_photo_editor tests
	ruff check mpr_photo_editor tests

test:
	PYTHONPATH=. pytest

run:
	PYTHONPATH=. python -m mpr_photo_editor.gui

clean:
	rm -rf target
	find . -name "*.so" -delete
	find . -name "*.pyi" -delete
