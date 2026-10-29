"""StegoVisionAI image encoding/decoding.

Accepted input formats are the formats supported by Pillow plus HEIC/HEIF/AVIF
when pillow-heif is installed. Encoded output is always lossless PNG so the
least-significant-bit payload survives saving and re-opening.
"""
from __future__ import annotations

import base64
import hashlib
from io import BytesIO

from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageOps, UnidentifiedImageError

# Adds HEIC/HEIF/AVIF decoders when the optional plugin is installed.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

MAGIC = b"STEGOVISION1:"
MAX_MESSAGE_BYTES = 1_000_000
MAX_IMAGE_PIXELS = 100_000_000


def _fernet(passphrase: str) -> Fernet:
    if not isinstance(passphrase, str) or len(passphrase) < 8:
        raise ValueError("Passphrase must be at least 8 characters.")
    # Kept compatible with the existing StegoVisionAI v1 payload format.
    key = base64.urlsafe_b64encode(
        hashlib.sha256(("StegoVisionAI:" + passphrase).encode("utf-8")).digest()
    )
    return Fernet(key)


def _open_rgb(image_bytes: bytes) -> Image.Image:
    """Open supported raster image bytes, apply orientation, and normalize to RGB."""
    if not image_bytes:
        raise ValueError("The uploaded image is empty.")
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large to process.")
            # For animated files, Pillow opens the first frame. We embed in a
            # single-frame PNG; animated-image preservation is not supported.
            source.seek(0)
            oriented = ImageOps.exif_transpose(source)
            # Composite transparent images on white so the visible appearance
            # is retained when converting to RGB.
            if oriented.mode in ("RGBA", "LA") or (
                oriented.mode == "P" and "transparency" in oriented.info
            ):
                rgba = oriented.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                background.alpha_composite(rgba)
                return background.convert("RGB")
            return oriented.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc):
            raise
        raise ValueError(
            "Unsupported or damaged image. Try PNG, JPEG, WEBP, BMP, TIFF, GIF, "
            "or install pillow-heif for HEIC/HEIF/AVIF."
        ) from exc


def encode_png(image_bytes: bytes, message: str, passphrase: str) -> bytes:
    """Hide an encrypted message in any supported input raster image; return PNG."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Enter a message to hide.")

    payload = MAGIC + _fernet(passphrase).encrypt(message.encode("utf-8"))
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ValueError("Message is too large for this demo.")

    img = _open_rgb(image_bytes)
    pixels = bytearray(img.tobytes())
    # Four-byte big-endian payload length followed by payload.
    data = len(payload).to_bytes(4, "big") + payload
    bits = "".join(f"{byte:08b}" for byte in data)
    capacity = len(pixels)
    if len(bits) > capacity:
        raise ValueError(
            f"Image capacity is too small. Need {len(bits)} bits; "
            f"image holds {capacity} bits."
        )

    for index, bit in enumerate(bits):
        pixels[index] = (pixels[index] & 0xFE) | int(bit)

    encoded = Image.frombytes("RGB", img.size, bytes(pixels))
    buffer = BytesIO()
    encoded.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def decode_png(image_bytes: bytes, passphrase: str) -> str:
    """Decode a StegoVisionAI payload from an unmodified encoded image."""
    img = _open_rgb(image_bytes)
    pixels = img.tobytes()
    if len(pixels) < 32:
        raise ValueError("Image is too small to contain a supported payload.")

    length_bits = "".join(str(value & 1) for value in pixels[:32])
    payload_length = int(length_bits, 2)
    if payload_length < len(MAGIC) + 10 or payload_length > MAX_MESSAGE_BYTES:
        raise ValueError("No supported StegoVision payload was found.")

    end_bit = 32 + payload_length * 8
    if end_bit > len(pixels):
        raise ValueError("Payload length is invalid or image was modified.")

    payload_bits = "".join(
        str(value & 1) for value in pixels[32:end_bit]
    )
    payload = bytes(
        int(payload_bits[offset:offset + 8], 2)
        for offset in range(0, len(payload_bits), 8)
    )
    if not payload.startswith(MAGIC):
        raise ValueError("No supported StegoVision payload was found.")

    try:
        plaintext = _fernet(passphrase).decrypt(payload[len(MAGIC):])
        return plaintext.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Could not decrypt the hidden message. Check the passphrase or image integrity."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError("The hidden message is damaged or invalid.") from exc
