cmake_minimum_required(VERSION 3.18)
project(MPRPhotoEditor LANGUAGES CXX)

# --- Debugging: Print the toolchain file path ---
# This will show the value passed from the CI environment via SKBUILD_CMAKE_ARGS.
message(STATUS "Checking for toolchain file. CMAKE_TOOLCHAIN_FILE='${CMAKE_TOOLCHAIN_FILE}'")
message(STATUS "Checking for VCPKG triplet. VCPKG_TARGET_TRIPLET='${VCPKG_TARGET_TRIPLET}'")
message(STATUS "Checking for VCPKG manifest mode. VCPKG_MANIFEST_MODE='${VCPKG_MANIFEST_MODE}'")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find Dependencies ---
# These are found at the top level so they are available to all sub-projects.

# Find Qt6 for the future C++ GUI.
find_package(Qt6 REQUIRED COMPONENTS Widgets)

# Find LibRaw for the C++ backend.
# LibRaw uses autotools, so it provides a .pc file for pkg-config.
# We use CMake's PkgConfig module to find it in a platform-agnostic way.
find_package(PkgConfig REQUIRED)
pkg_check_modules(PC_LIBRAW REQUIRED libraw)


# Find pybind11 to create Python bindings for our C++ backend.
# Assumes pybind11 is installed (e.g., via `pip install pybind11`).
# Use the modern FindPython module to satisfy policy CMP0148 and avoid warnings.
find_package(Python REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

# --- Project Structure ---
# Add subdirectories for the C++ backend and frontend.
add_subdirectory(cpp)
add_subdirectory(gui)


# Enable testing with CTest and include the tests directory.
enable_testing()
add_subdirectory(tests)

# --- Informational Messages ---
message(STATUS "--- MPR Photo Editor Build Configuration ---")
message(STATUS "Found Qt6: ${Qt6_FOUND} (Version: ${Qt6_VERSION})")
message(STATUS "Found LibRaw: ${PC_LIBRAW_FOUND} (Version: ${PC_LIBRAW_VERSION})")
message(STATUS "Found pybind11: ${pybind11_FOUND} (Version: ${pybind11_VERSION})")
