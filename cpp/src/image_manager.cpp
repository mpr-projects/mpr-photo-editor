#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // For automatic type conversion
#include <libraw/libraw.h>

#include <string>
#include <stdexcept>
#include <mutex>
#include <atomic>
#include <unordered_map>
#include <memory>

namespace py = pybind11;

// --- Global State Management (similar to Rust's image_manager) ---

// A thread-safe, global map to store pointers to LibRaw instances.
// The key is a unique u64 ID, and the value is the raw pointer.
static std::mutex image_manager_mutex;
static std::unordered_map<uint64_t, std::unique_ptr<LibRaw>> image_manager;

// A thread-safe, global atomic counter to generate unique IDs for each image.
static std::atomic<uint64_t> next_image_id(1);

// --- Backend Functions ---

std::string get_libraw_version() {
    return libraw_version();
}

uint64_t load_raw_image(const std::string& filepath) {
    // Use a unique_ptr for exception safety during creation.
    auto processor = std::make_unique<LibRaw>();

    if (processor->open_file(filepath.c_str()) != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }
    if (processor->unpack() != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to unpack file: " + filepath);
    }

    uint64_t id = next_image_id.fetch_add(1);

    // Lock the mutex to safely insert into the map.
    std::lock_guard<std::mutex> lock(image_manager_mutex);
    // Move the unique_ptr into the map, transferring ownership.
    image_manager[id] = std::move(processor);

    return id;
}

void release_raw_image(uint64_t id) {
    std::lock_guard<std::mutex> lock(image_manager_mutex);
    // Erasing the unique_ptr from the map will automatically call its
    // destructor, which in turn deletes the managed LibRaw object.
    image_manager.erase(id);
}

py::bytes get_thumbnail(uint64_t id) {
    std::lock_guard<std::mutex> lock(image_manager_mutex);
    auto it = image_manager.find(id);
    if (it == image_manager.end()) {
        throw std::runtime_error("Invalid image ID");
    }
    LibRaw* processor = it->second.get(); // Get the raw pointer from the unique_ptr

    if (processor->unpack_thumb() != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to unpack thumbnail");
    }

    libraw_processed_image_t* thumb = processor->dcraw_make_mem_thumb();
    if (!thumb) {
        throw std::runtime_error("Failed to create memory thumbnail");
    }

    // Use a unique_ptr for exception-safe cleanup of the thumbnail data
    std::unique_ptr<libraw_processed_image_t, decltype(&libraw_dcraw_clear_mem)> thumb_ptr(thumb, &libraw_dcraw_clear_mem);

    if (thumb->type != LIBRAW_IMAGE_JPEG && thumb->type != LIBRAW_IMAGE_BITMAP) {
        throw std::runtime_error("Thumbnail is not in a recognized format (JPEG/Bitmap)");
    }

    // Create a Python bytes object by copying the data
    return py::bytes(reinterpret_cast<const char*>(thumb->data), thumb->data_size);
}

py::dict get_metadata(uint64_t id) {
    std::lock_guard<std::mutex> lock(image_manager_mutex);
    auto it = image_manager.find(id);
    if (it == image_manager.end()) {
        throw std::runtime_error("Invalid image ID");
    }
    LibRaw* processor = it->second.get(); // Get the raw pointer from the unique_ptr

    py::dict meta;
    meta["make"] = std::string(processor->imgdata.idata.make);
    meta["model"] = std::string(processor->imgdata.idata.model);
    meta["iso"] = processor->imgdata.other.iso_speed;
    meta["shutter"] = processor->imgdata.other.shutter;
    meta["aperture"] = processor->imgdata.other.aperture;
    return meta;
}

PYBIND11_MODULE(cpp_backend, m) {
    m.doc() = "C++ backend for MPR Photo Editor using LibRaw";
    m.def("get_libraw_version", &get_libraw_version, "Returns the LibRaw version string");
    m.def("load_raw_image", &load_raw_image, "Loads a raw image and returns a handle ID");
    m.def("release_raw_image", &release_raw_image, "Releases a raw image handle");
    m.def("get_thumbnail", &get_thumbnail, "Extracts the thumbnail from a raw image");
    m.def("get_metadata", &get_metadata, "Extracts metadata from a raw image");
}
