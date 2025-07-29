use pyo3::prelude::*;
use ndarray::Array2;

/// Simple function to invert grayscale image pixels
#[pyfunction]
fn invert_image(image: Vec<u8>, width: usize, height: usize) -> Vec<u8> {
    let mut arr = Array2::from_shape_vec((height, width), image).unwrap();
    arr.par_mapv_inplace(|v| 255 - v);
    arr.into_raw_vec()
}

/// Python module definition
#[pymodule]
fn rust_backend(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(invert_image, m)?)?;
    Ok(())
}