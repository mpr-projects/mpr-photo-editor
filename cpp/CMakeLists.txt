# Create the Python module from our C++ source files.
# The name 'cpp_backend' here defines the name of the resulting .pyd/.so file.
pybind11_add_module(cpp_backend
    src/image_manager.cpp
)

# Link our backend against LibRaw
# Use the variables set by PkgConfig in the parent scope.
# We use PC_LIBRAW_LINK_LIBRARIES instead of PC_LIBRAW_LIBRARIES because it
# provides the full, absolute path to the library file, which is more robust
# for the linker.
target_link_libraries(cpp_backend PRIVATE ${PC_LIBRAW_LINK_LIBRARIES})

# Add the include directory for our own headers
target_include_directories(cpp_backend PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
    # Also add the include directories for LibRaw
    ${PC_LIBRAW_INCLUDE_DIRS}
)

# --- Installation ---
# This command tells scikit-build-core where to place the compiled module
# within the final Python wheel. It will be installed into the
# `mpr_photo_editor` package directory.
install(TARGETS cpp_backend
    LIBRARY DESTINATION mpr_photo_editor
)
