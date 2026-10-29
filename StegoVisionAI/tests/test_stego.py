from io import BytesIO

import pytest
from PIL import Image

from app.stego import encode_png, decode_png


PASSWORD = "Correct-Horse-123"
MESSAGE = "Hidden message: StegoVisionAI test ✓"


def make_image(fmt: str, size=(240, 240)) -> bytes:
    image = Image.new("RGB", size, (120, 180, 90))
    stream = BytesIO()
    save_kwargs = {"quality": 95} if fmt == "JPEG" else {}
    image.save(stream, format=fmt, **save_kwargs)
    return stream.getvalue()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP", "BMP", "TIFF", "GIF"])
def test_supported_input_formats_encode_to_png_and_decode(fmt):
    source = make_image(fmt)
    encoded = encode_png(source, MESSAGE, PASSWORD)
    with Image.open(BytesIO(encoded)) as result:
        assert result.format == "PNG"
    assert decode_png(encoded, PASSWORD) == MESSAGE


def test_wrong_password_fails():
    encoded = encode_png(make_image("PNG"), MESSAGE, PASSWORD)
    with pytest.raises(ValueError, match="Could not decrypt"):
        decode_png(encoded, "Another-Password-456")


def test_empty_message_fails():
    with pytest.raises(ValueError, match="Enter a message"):
        encode_png(make_image("PNG"), "  ", PASSWORD)


def test_invalid_image_fails_cleanly():
    with pytest.raises(ValueError, match="Unsupported or damaged image"):
        encode_png(b"not an image", MESSAGE, PASSWORD)


def test_saved_png_round_trip_repeated_messages():
    # Exercise independent payloads through real PNG serialization repeatedly.
    cover = make_image("PNG", size=(320, 320))
    cases = [
        "Simple ASCII test",
        "Punctuation: !?.,;: @#$%^&*()",
        "Unicode: Telugu నమస్కారం ✓ 🔐",
        "First line\nSecond line\nThird line",
    ]
    for message in cases:
        encoded = encode_png(cover, message, PASSWORD)
        # Re-open and re-save as bytes without changing pixels, matching the API upload path.
        with Image.open(BytesIO(encoded)) as im:
            reopened = BytesIO()
            im.save(reopened, format="PNG", optimize=False)
        assert decode_png(reopened.getvalue(), PASSWORD) == message


def test_original_cover_image_reports_no_payload():
    with pytest.raises(ValueError, match="No supported StegoVision payload"):
        decode_png(make_image("PNG"), PASSWORD)
