from mpr_photo_editor.backend import invert_image

def test_invert_image():
    original = [0, 128, 255]
    expected = [255, 127, 0]
    result = invert_image(original, 1, 3)
    assert result == expected