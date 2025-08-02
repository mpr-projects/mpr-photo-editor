use std::ffi::CString;
use std::os::raw::{c_char, c_int};
use std::ptr;
use std::slice;

use image::{RgbImage, Rgb};

extern "C" {
    fn libraw_wrapper_open(path: *const c_char) -> *mut libc::c_void;
    fn libraw_wrapper_get_processed_image(
        handle: *mut libc::c_void,
        buf: *mut *const u8,
        len: *mut c_int,
        width: *mut c_int,
        height: *mut c_int,
    ) -> c_int;
    fn libraw_wrapper_get_metadata(handle: *mut libc::c_void) -> *const libraw_data_t;
    fn libraw_wrapper_close(handle: *mut libc::c_void);
}

// Exposed from bindgen
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct libraw_data_t {
    pub sizes: libraw_image_sizes_t,
    // Add more fields as needed
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct libraw_image_sizes_t {
    pub width: u16,
    pub height: u16,
    // Add more fields if needed
}

pub struct ImageResult {
    pub metadata: libraw_data_t,
    pub image: RgbImage,
}

pub fn load_image_from_raw(path: &str) -> Result<ImageResult, String> {
    let c_path = CString::new(path).map_err(|e| e.to_string())?;

    unsafe {
        // Open the RAW file
        let handle = libraw_wrapper_open(c_path.as_ptr());
        if handle.is_null() {
            return Err("Failed to open image with LibRaw".into());
        }

        // Get image data
        let mut buf: *const u8 = ptr::null();
        let mut len: c_int = 0;
        let mut width: c_int = 0;
        let mut height: c_int = 0;
        let result = libraw_wrapper_get_processed_image(
            handle,
            &mut buf,
            &mut len,
            &mut width,
            &mut height,
        );

        if result != 0 || buf.is_null() || len <= 0 {
            libraw_wrapper_close(handle);
            return Err("Failed to extract image data".into());
        }

        let slice = slice::from_raw_parts(buf, len as usize);
        let metadata = *libraw_wrapper_get_metadata(handle);

        // Copy to Vec and wrap in RgbImage
        let pixels = slice.to_vec();
        let image = RgbImage::from_raw(width as u32, height as u32, pixels)
            .ok_or_else(|| "Failed to construct image".to_string())?;

        // Free the handle
        libraw_wrapper_close(handle);

        Ok(ImageResult { metadata, image })
    }
}