#include "mpr_photo_editor/image_manager.h"
#include <libraw/libraw.h>
#include <stdexcept>
#include <mutex>
#include <atomic>
#include <unordered_map>
#include <memory>

// --- PIMPL (Pointer to Implementation) ---
// This hides the private members of ImageManager from the public header,
// reducing compile times and separating interface from implementation.
class ImageManager::Impl {
public:
    std::mutex image_manager_mutex;
    std::unordered_map<uint64_t, std::unique_ptr<LibRaw>> image_manager;
    std::atomic<uint64_t> next_image_id{1};
};

// --- ImageManager Methods ---

ImageManager::ImageManager() : pimpl(std::make_unique<Impl>()) {}
ImageManager::~ImageManager() = default;

ImageManager& ImageManager::instance() {
    static ImageManager inst;
    return inst;
}

std::string ImageManager::get_libraw_version() {
    return libraw_version();
}

uint64_t ImageManager::load_raw_image(const std::string& filepath) {
    auto processor = std::make_unique<LibRaw>();

    if (processor->open_file(filepath.c_str()) != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }
    if (processor->unpack() != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to unpack file: " + filepath);
    }

    uint64_t id = pimpl->next_image_id.fetch_add(1);

    std::lock_guard<std::mutex> lock(pimpl->image_manager_mutex);
    pimpl->image_manager[id] = std::move(processor);

    return id;
}

void ImageManager::release_raw_image(uint64_t id) {
    std::lock_guard<std::mutex> lock(pimpl->image_manager_mutex);
    pimpl->image_manager.erase(id);
}

ThumbnailData ImageManager::get_thumbnail(uint64_t id) {
    std::lock_guard<std::mutex> lock(pimpl->image_manager_mutex);
    auto it = pimpl->image_manager.find(id);
    if (it == pimpl->image_manager.end()) {
        throw std::runtime_error("Invalid image ID");
    }
    LibRaw* processor = it->second.get();

    if (processor->unpack_thumb() != LIBRAW_SUCCESS) {
        throw std::runtime_error("Failed to unpack thumbnail");
    }

    libraw_processed_image_t* thumb = processor->dcraw_make_mem_thumb();
    if (!thumb) {
        throw std::runtime_error("Failed to create memory thumbnail");
    }

    std::unique_ptr<libraw_processed_image_t, decltype(&libraw_dcraw_clear_mem)> thumb_ptr(thumb, &libraw_dcraw_clear_mem);

    ThumbnailData result;
    result.data.assign(reinterpret_cast<char*>(thumb->data), reinterpret_cast<char*>(thumb->data) + thumb->data_size);
    return result;
}

Metadata ImageManager::get_metadata(uint64_t id) {
    std::lock_guard<std::mutex> lock(pimpl->image_manager_mutex);
    auto it = pimpl->image_manager.find(id);
    if (it == pimpl->image_manager.end()) {
        throw std::runtime_error("Invalid image ID");
    }
    LibRaw* processor = it->second.get();

    Metadata meta;
    meta.make = std::string(processor->imgdata.idata.make);
    meta.model = std::string(processor->imgdata.idata.model);
    meta.iso_speed = processor->imgdata.other.iso_speed;
    meta.shutter = processor->imgdata.other.shutter;
    meta.aperture = processor->imgdata.other.aperture;
    return meta;
}