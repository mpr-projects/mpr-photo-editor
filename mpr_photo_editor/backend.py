

try:
    # Import the C++ backend.
    # This will be a .pyd or .so file built by CMake and copied here.
    from . import cpp_backend_python_bindings  # type: ignore

    # Re-export the functions from the C++ backend
    get_libraw_version = cpp_backend_python_bindings.get_libraw_version
    load_raw_image = cpp_backend_python_bindings.load_raw_image
    release_raw_image = cpp_backend_python_bindings.release_raw_image
    get_thumbnail = cpp_backend_python_bindings.get_thumbnail
    get_metadata = cpp_backend_python_bindings.get_metadata

except ImportError as e:
    raise ImportError(
        "Could not import the 'cpp_backend_python_bindings'. Please build the project first "
        "(e.g., run 'make build-cpp').\n"
        f"Original error: {e}"
    )
