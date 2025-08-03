#include "libraw_wrapper.hpp"

#include <libraw/libraw.h>
#include <cstring>

struct LibRawHandle {
    LibRaw processor;
};

extern "C" {

const char* libraw_wrapper_version() {
    return libraw_version();
}

LibRawHandle* libraw_wrapper_create() {
    return new LibRawHandle();
}

void libraw_wrapper_destroy(LibRawHandle* handle) {
    delete handle;
}

int libraw_wrapper_open(LibRawHandle* handle, const char* filename) {
    if (handle->processor.open_file(filename) != LIBRAW_SUCCESS) return -1;
    if (handle->processor.unpack() != LIBRAW_SUCCESS) return -2;
    return 0;
}

LibRawMetadata libraw_wrapper_get_metadata(LibRawHandle* handle) {
    auto& idata = handle->processor.imgdata.idata;
    auto& other = handle->processor.imgdata.other;
    LibRawMetadata meta;
    meta.make = idata.make;
    meta.model = idata.model;
    meta.iso = other.iso_speed;
    meta.shutter = other.shutter;
    meta.aperture = other.aperture;
    return meta;
}

int libraw_wrapper_get_thumbnail(LibRawHandle* handle, const char** buf, int* len) {
    if (handle->processor.unpack_thumb() != LIBRAW_SUCCESS) return -1;
    *buf = handle->processor.imgdata.thumbnail.thumb;
    *len = handle->processor.imgdata.thumbnail.tlength;
    return 0;
}

void libraw_wrapper_close(LibRawHandle* handle) {
    handle->processor.recycle();
}

}
