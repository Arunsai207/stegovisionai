from io import BytesIO
from PIL import Image, UnidentifiedImageError
import hashlib, math

def inspect_image(filename: str, data: bytes) -> dict:
    if len(data) > 20 * 1024 * 1024:
        raise ValueError("Maximum upload size is 20 MB.")
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data))
    except (UnidentifiedImageError, OSError):
        raise ValueError("File is not a supported, valid image.")
    width, height = image.size
    fmt = image.format or "Unknown"
    mode = image.mode
    entropy = None
    try:
        hist = image.convert("RGB").histogram()
        total = sum(hist)
        entropy = round(-sum((n/total)*math.log2(n/total) for n in hist if n), 4)
    except Exception:
        pass
    findings = [
        {"level":"info","title":"File parsed successfully","detail":"The uploaded file was recognized as an image."},
        {"level":"info","title":"Cryptographic hash generated","detail":"SHA-256 can help identify exact byte-for-byte matches."}
    ]
    if fmt.upper() not in ("PNG", "BMP", "TIFF"):
        findings.append({"level":"notice","title":"Lossy or format-specific processing","detail":"Some formats and later conversions may alter pixel data and destroy simple LSB payloads."})
    if image.info:
        findings.append({"level":"notice","title":"Embedded metadata present","detail":"Image contains metadata fields. Their presence alone is not evidence of steganography."})
    findings.append({"level":"caution","title":"No definitive steganography verdict","detail":"This starter uses metadata and basic image statistics, not a validated trained detector. Absence of indicators does not prove an image is clean."})
    return {
        "filename": filename[:200], "format": fmt, "width": width, "height": height,
        "mode": mode, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "entropy": entropy, "metadata_keys": sorted(list(image.info.keys()))[:40],
        "findings": findings, "verdict": "Needs further analysis"
    }
