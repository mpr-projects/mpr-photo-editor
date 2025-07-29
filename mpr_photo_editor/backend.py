try:
    from . import rust_backend # type: ignore

except ImportError:
    raise ImportError("Rust backend not compiled. Run `maturin develop` first.")

def invert_image(image: list[int], width: int, height: int) -> list[int]:
    return rust_backend.invert_image(image, width, height)
