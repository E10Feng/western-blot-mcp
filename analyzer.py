import base64
import mimetypes
from pathlib import Path

import httpx


def load_image(image_source: str) -> tuple[bytes, str]:
    """Load image bytes and mime type from a file path, URL, or base64 string."""
    # Data URI: data:image/png;base64,<data>
    if image_source.startswith("data:"):
        header, data = image_source.split(",", 1)
        if ";base64" not in header:
            raise ValueError(f"Unsupported data URI encoding (expected base64): {header}")
        mime_type = header.split(":")[1].split(";")[0]
        return base64.b64decode(data), mime_type

    # HTTP/HTTPS URL
    if image_source.startswith(("http://", "https://")):
        response = httpx.get(image_source, timeout=30, follow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
        return response.content, content_type

    # File path (check existence first — fast syscall)
    path = Path(image_source)
    if path.exists():
        mime_type, _ = mimetypes.guess_type(str(path))
        return path.read_bytes(), mime_type or "image/jpeg"

    # Raw base64 fallback — try decoding whatever's left
    try:
        decoded = base64.b64decode(image_source, validate=True)
        if len(decoded) > 10:
            return decoded, _detect_mime_from_magic(decoded)
    except Exception:
        pass

    raise FileNotFoundError(f"Image file not found: {image_source}")


def _detect_mime_from_magic(data: bytes) -> str:
    """Detect image mime type from magic bytes."""
    if data[:4] == b"\x89PNG":
        return "image/png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if len(data) >= 12 and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    return "image/jpeg"
