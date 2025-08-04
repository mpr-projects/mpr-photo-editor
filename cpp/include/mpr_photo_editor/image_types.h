#ifndef MPR_IMAGE_TYPES_H
#define MPR_IMAGE_TYPES_H

#include <string>
#include <vector>

struct ThumbnailData {
    std::vector<char> data;
};

struct Metadata {
    std::string make;
    std::string model;
    float iso_speed = 0.0f;
    float shutter = 0.0f;
    float aperture = 0.0f;
};

#endif // MPR_IMAGE_TYPES_H