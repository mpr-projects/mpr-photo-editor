#ifndef MPR_IMAGE_MANAGER_H
#define MPR_IMAGE_MANAGER_H

#include "image_types.h"
#include <string>
#include <cstdint>
#include <memory>

class ImageManager {
public:
    static ImageManager& instance();

    ImageManager(const ImageManager&) = delete;
    void operator=(const ImageManager&) = delete;

    std::string get_libraw_version();
    uint64_t load_raw_image(const std::string& filepath);
    void release_raw_image(uint64_t id);
    ThumbnailData get_thumbnail(uint64_t id);
    Metadata get_metadata(uint64_t id);

private:
    ImageManager();
    ~ImageManager();

    class Impl;
    std::unique_ptr<Impl> pimpl;
};
#endif // MPR_IMAGE_MANAGER_H