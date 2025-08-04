#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // For automatic type conversion
#include "mpr_photo_editor/image_manager.h" // The new core logic header

namespace py = pybind11;

// --- Wrapper Functions ---
// These functions act as the bridge between the C++ ImageManager and Python.
// They handle the conversion of C++ types (like structs) to Python types (like dicts).

std::string get_libraw_version_wrapper() {
    return ImageManager::instance().get_libraw_version();
}

uint64_t load_raw_image_wrapper(const std::string& filepath) {
    return ImageManager::instance().load_raw_image(filepath);
}

void release_raw_image_wrapper(uint64_t id) {
    ImageManager::instance().release_raw_image(id);
}

py::bytes get_thumbnail_wrapper(uint64_t id) {
    ThumbnailData thumb_data = ImageManager::instance().get_thumbnail(id);
    return py::bytes(thumb_data.data.data(), thumb_data.data.size());
}

py::dict get_metadata_wrapper(uint64_t id) {
    Metadata meta_data = ImageManager::instance().get_metadata(id);
    py::dict meta;
    meta["make"] = meta_data.make;
    meta["model"] = meta_data.model;
    meta["iso"] = meta_data.iso_speed;
    meta["shutter"] = meta_data.shutter;
    meta["aperture"] = meta_data.aperture;
    return meta;
}


PYBIND11_MODULE(cpp_backend_python_bindings, m) {
    m.doc() = "C++ backend for MPR Photo Editor using LibRaw";
    m.def("get_libraw_version", &get_libraw_version_wrapper, "Returns the LibRaw version string");
    m.def("load_raw_image", &load_raw_image_wrapper, "Loads a raw image and returns a handle ID");
    m.def("release_raw_image", &release_raw_image_wrapper, "Releases a raw image handle");
    m.def("get_thumbnail", &get_thumbnail_wrapper, "Extracts the thumbnail from a raw image");
    m.def("get_metadata", &get_metadata_wrapper, "Extracts metadata from a raw image");
}
