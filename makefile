.PHONY: develop install test run clean check

develop:
	maturin develop
	pyo3-stubgen mpr_photo_editor.rust_backend .

install:
	pip install .[dev]

check:
	mypy mpr_photo_editor tests
	ruff check mpr_photo_editor tests

test:
	# To prevent import path shadowing, where pytest finds the local source
	# code instead of the installed package, we rename the source directory
	# for the duration of the test run. The exit code from pytest is
	# preserved to ensure the command fails if tests fail.
	mv mpr_photo_editor mpr_photo_editor_temp; \
	PYTHONPATH=. pytest; EXIT_CODE=$$?; \
	mv mpr_photo_editor_temp mpr_photo_editor; \
	(exit $$EXIT_CODE)

run:
	PYTHONPATH=. python -m mpr_photo_editor.gui

clean:
	rm -rf build
	find . -name "*.so" -delete
	find . -name "*.pyi" -delete

wheel:
	# Ensure all dependencies are installed, including delocate for macOS.
	pip install .[dev] delocate
	# Build the wheel. On macOS, DYLD_LIBRARY_PATH must be set so that
	# delocate can find the libraw dylib to bundle into the wheel.
	# A similar approach with LD_LIBRARY_PATH is needed on Linux.
	DYLD_LIBRARY_PATH=build/libraw_dist/lib maturin build --release
	@wheel_path=$$(ls -t build/target/wheels/*.whl | head -n 1); \
	echo "Running delocate on $$wheel_path"; \
	delocate-wheel -w build/target/wheels/ $$wheel_path
