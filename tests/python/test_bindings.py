from mpr_photo_editor import backend


def test_get_libraw_version():
    """
    Tests that the get_libraw_version function from the C++ backend
    can be called and returns a non-empty string.
    """
    version = backend.get_libraw_version()
    assert isinstance(version, str)
    assert len(version) > 0
    assert "." in version