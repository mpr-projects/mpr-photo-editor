try:
    from . import rust_backend # type: ignore

except ImportError:
    raise ImportError("Rust backend not compiled. Run `maturin develop` first.")

def get_libraw_version() -> str:
    """Retrieves the LibRaw version string from the Rust backend."""
    return rust_backend.get_libraw_version()


def load_raw_image(filepath: str) -> int:
    """Loads a raw image and returns a unique ID."""
    return rust_backend.load_raw_image(filepath)


def release_raw_image(image_id: int):
    """Releases the resources for a given image ID."""
    rust_backend.release_raw_image(image_id)


def get_thumbnail(image_id: int) -> bytes:
    """Gets the thumbnail data for a given image ID."""
    return rust_backend.get_thumbnail(image_id)


def get_metadata(image_id: int) -> dict[str, str]:
    """Gets the metadata for a given image ID."""
    return rust_backend.get_metadata(image_id)
