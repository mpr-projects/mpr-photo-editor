use std::env;
use std::path::PathBuf;
use std::process::Command;

// use which::which;

fn windows_link_libraw_pkg_config() -> String {
    // This function is for Windows only. It finds the vcpkg-installed libraw and
    // and links against it. On Windows with MSVC, the C++ standard library
    // is linked automatically.
    let lib = pkg_config::Config::new()
        .statik(false) // We want dynamic linking
        .probe("libraw")
        .expect("Could not find libraw. Make sure vcpkg has installed it and PKG_CONFIG_PATH is set correctly.");

    for path in &lib.link_paths {
        println!("cargo:rustc-link-search=native={}", path.display());
    }
    println!("cargo:rustc-link-lib=dylib=raw");

    lib.include_paths[0]
        .display()
        .to_string()
}

fn unix_build_libraw() -> String {
    // Ensure the libraw source directory is clean before attempting to build.
    // This prevents errors if a previous build was done in-tree. We ignore
    // the result because this command will fail if the directory has never
    let _ = Command::new("make")
        .arg("distclean")
        .current_dir("external/libraw")
        .output();

    let dist_dir = PathBuf::from("../build/libraw_dist");
    std::fs::create_dir_all(&dist_dir).expect("Failed to create libraw_dist directory");

    let dst = autotools::Config::new("external/libraw")
        // The `configure` script is not checked into git, so we must generate it
        // using `autoreconf`. This is necessary for CI environments and for the
        // first build on a clean checkout.
        .reconf("-ivf")
        // We specify an explicit output directory for the installed artifacts.
        .out_dir(dist_dir.canonicalize().unwrap().as_path())
        .disable("static", None)
        .enable("shared", None)
        .disable("examples", None)
        .disable("openmp", None)
        .disable("lcms", None)
        .disable("demosaic-pack-gpl2", None)
        .disable("demosaic-pack-gpl3", None)
        .cflag("-fPIC")
        .build();

    // 2. Tell cargo where to find the compiled libraw.
    // The `autotools` crate installs into `$dst/lib`.
    println!("cargo:rustc-link-search=native={}/lib", dst.display());
    println!("cargo:rustc-link-lib=dylib=raw"); // Link against libraw.so/dylib

    // On macOS and Linux, we need to set an rpath to the build directory
    // so that delocate/auditwheel can find the shared library. This is more
    // robust than relying on DYLD_LIBRARY_PATH.
    if cfg!(target_os = "macos") || cfg!(target_os = "linux") {
        println!("cargo:rustc-link-arg=-Wl,-rpath,{}", dst.join("lib").display());
    }

    // 3. Link against the C++ standard library on macOS and Linux.
    if cfg!(target_os = "macos") {
      println!("cargo:rustc-link-lib=c++");
    } else if cfg!(target_os = "linux") {
      println!("cargo:rustc-link-lib=stdc++");
    }

    println!("cargo:rerun-if-changed=external/libraw/libraw/libraw.h");
    // "external/libraw/libraw/libraw.h".to_string()
    "external/libraw/".to_string()
}

fn generate_bindings(header_path: &str) {
    // Use an allowlist to only generate bindings for the functions and types
    // we actually use. This is more robust than a blocklist and avoids
    // FFI warnings and platform-specific compilation errors.
    let bindings = bindgen::Builder::default()
        .header(header_path)
        .allowlist_function("libraw_.*") // Allow all C-API functions
        .allowlist_type("libraw_data_t")
        .allowlist_type("libraw_processed_image_t")
        .allowlist_type("LibRaw_errors")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_dir.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}

fn compile_libraw_wrapper(header_path: &str) {
    // Tell cargo to rebuild if the wrapper changes
    println!("cargo:rerun-if-changed=ffi/libraw_wrapper.hpp");

    // Compile C++ wrapper
    cc::Build::new()
        .cpp(true)
        .file("ffi/libraw_wrapper.cpp")
        .include(header_path)
        .include("ffi/")
        .flag_if_supported("-std=c++11")
        .compile("libraw_wrapper");

    // Generate Rust bindings from the header
    let bindings = bindgen::Builder::default()
        .header("ffi/libraw_wrapper.hpp")
        .clang_arg("-Iextern/libraw/") // Include LibRaw headers
        .clang_arg("-Iffi/")           // Include our wrapper header
        .generate()
        .expect("Unable to generate bindings");

    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}

fn main() {
    let header_path = if cfg!(target_os = "windows") {
        // On Windows, we use vcpkg to find libraw (because compiling
        // it on Windows is not as straight forward)
        // The CI environment is set up to ensure pkg-config finds it.
        // If it's not found, something is wrong with the environment.
        windows_link_libraw_pkg_config()
    } else {
        // On Unix-based systems we build a minimal libraw
        unix_build_libraw()
    };

    // generate_bindings(&header_path);
    compile_libraw_wrapper(&header_path);
}