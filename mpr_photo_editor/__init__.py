import os
import sys
from pathlib import Path

# On Windows, with Python 3.8+, we need to explicitly add the directory
# containing our bundled DLLs to the DLL search path.
# This is necessary for the OS to find libraw.dll and its dependencies
# when the rust_backend extension module is imported.
if sys.platform == "win32":
    # Get the path to the directory containing this __init__.py file.
    package_dir = Path(__file__).resolve().parent
    # Construct the path to the 'lib' subdirectory.
    lib_dir = package_dir / "lib"
    if lib_dir.is_dir():
        os.add_dll_directory(str(lib_dir))