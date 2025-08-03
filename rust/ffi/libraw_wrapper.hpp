#ifndef LIBRAW_WRAPPER_H
#define LIBRAW_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

struct LibRawMetadata {
    const char* make;
    const char* model;
    float iso;
    float shutter;
    float aperture;
};

typedef struct LibRawHandle LibRawHandle;

const char* libraw_wrapper_version();

LibRawHandle* libraw_wrapper_create();
void libraw_wrapper_destroy(LibRawHandle* handle);

int libraw_wrapper_open(LibRawHandle* handle, const char* filename);
LibRawMetadata libraw_wrapper_get_metadata(LibRawHandle* handle);
int libraw_wrapper_get_thumbnail(LibRawHandle* handle, const char** buf, int* len);
void libraw_wrapper_close(LibRawHandle* handle);

#ifdef __cplusplus
}
#endif

#endif // LIBRAW_WRAPPER_H
