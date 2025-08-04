# Makefile for simplifying common development tasks.

# --- Variables ---
# Find the python interpreter. This is tricky because `make` runs in a non-interactive
# shell that may not have the `pyenv` shims in its PATH.
# We first check if `pyenv` is an available command. If so, we use `pyenv which python`
# as it's the most reliable way to get the correct interpreter.
# If not, we fall back to a standard PATH search.
ifeq ($(shell command -v pyenv 2>/dev/null),)
	PYTHON ?= $(shell command -v python || command -v python3)
else
	PYTHON ?= $(shell pyenv which python)
endif


# --- Targets ---
.PHONY: help setup run build-gui test check clean check-env build-bindings

help:
	@echo "Available commands:"
	@echo "  setup        - Set up the Python environment and build the C++ backend"
	@echo "  run          - Run the Python GUI application"
	@echo "  build-gui    - Build the native C++ GUI executable (found in build/gui/)"
	@echo "  build-bindings - Build the C++ Python module (found in build/cpp/)"
	@echo "  test         - Run python tests"
	@echo "  check        - Run static analysis (mypy, ruff)"
	@echo "  clean        - Remove all build artifacts and caches"
	@echo "  check-env    - Check the environment variables and paths seen by make"

setup:
	@echo "Installing Python dependencies and building C++ backend via scikit-build-core..."
	$(PYTHON) -m pip install -v -e .[dev]
	@echo "Development environment is ready."

run:
	@echo "Running the Python GUI application (C++ backend)..."
	$(PYTHON) -m mpr_photo_editor.gui

build-bindings:
	@echo "Configuring and building the Python C++ module..."
	cmake -B build -S .
	cmake --build build --target cpp_backend_python_bindings --verbose
	@echo "Python module is available in the build directory (e.g., build/cpp/)."

build-gui:
	@echo "Configuring and building the native C++ GUI..."
	cmake -B build -S .
	cmake --build build --target PhotoEditor
	@echo "C++ GUI executable is available at build/gui/PhotoEditor"

test:
	@echo "Running python tests..."
	$(PYTHON) -m pytest tests/python

check:
	@echo "Running static analysis..."
	@echo "--- MyPy ---"
	$(PYTHON) -m mypy mpr_photo_editor tests/python
	@echo "--- Ruff ---"
	$(PYTHON) -m ruff check mpr_photo_editor tests/python


clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info mpr_photo_editor/*.so mpr_photo_editor/*.pyd .pytest_cache/ .mypy_cache/ .ruff_cache/ _skbuild/
	@echo "Done."

check-env:
	@echo "--- Environment Check ---"
	@echo "Make's default shell: $(SHELL)"
	@echo "Python interpreter command: '$(PYTHON)'"
	@echo "Full path to interpreter: '$(shell command -v $(PYTHON))'"
	@echo "Python version: '$($(PYTHON) --version)'"
	@echo "-----------------------"