# --- Define Core Logic Sources and Includes ---
# These variables are passed to the parent scope to be used by other targets,
# such as the C++ GUI, creating a single source of truth for our core files.
set(mpo_core_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/src/image_manager.cpp)

set(mpo_core_includes
    ${CMAKE_CURRENT_SOURCE_DIR}/include)

set(MPO_CORE_LOGIC_SOURCES ${mpo_core_sources} PARENT_SCOPE)
set(MPO_CORE_LOGIC_INCLUDE_DIRS ${mpo_core_includes} PARENT_SCOPE)

# --- Python Bindings (Conditional) ---
# Only build the Python module if the option is enabled.
if(MPO_BUILD_PYTHON_BINDINGS)
    # Create the Python module directly from the binding code and core logic sources.
    pybind11_add_module(cpp_backend_python_bindings
        bindings/python_bindings.cpp
        ${mpo_core_sources}
    )

    # The Python module needs to link against LibRaw.
    target_link_libraries(cpp_backend_python_bindings PRIVATE ${PC_LIBRAW_LINK_LIBRARIES})

    # The Python module needs access to the core logic and LibRaw headers.
    target_include_directories(cpp_backend_python_bindings PRIVATE
        $<BUILD_INTERFACE:${mpo_core_includes}>
        $<INSTALL_INTERFACE:include>
        ${PC_LIBRAW_INCLUDE_DIRS}
    )

    # --- Installation ---
    # This command tells scikit-build-core where to place the compiled module
    # within the final Python wheel.
    install(TARGETS cpp_backend_python_bindings LIBRARY DESTINATION mpr_photo_editor)
endif()