import base64
import mimetypes
from pathlib import Path

import httpx


def load_image(image_source: str) -> tuple[bytes, str]:
    """Load image bytes and mime type from a file path, URL, or base64 string."""
    # Data URI: data:image/png;base64,<data>
    if image_source.startswith("data:"):
        header, data = image_source.split(",", 1)
        mime_type = header.split(":")[1].split(";")[0]
        return base64.b64decode(data), mime_type

    # HTTP/HTTPS URL
    if image_source.startswith(("http://", "https://")):
        response = httpx.get(image_source, timeout=30, follow_redirects=True)
        response.raise_for_status()
        mime_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        return response.content, mime_type

    # Try file path first (most common for local usage)
    path = Path(image_source)
    if path.exists():
        mime_type, _ = mimetypes.guess_type(str(path))
        return path.read_bytes(), mime_type or "image/jpeg"

    # Try raw base64 (no path separators, looks like base64)
    if "/" not in image_source and "\\" not in image_source and not image_source.startswith("."):
        try:
            decoded = base64.b64decode(image_source, validate=True)
            # Detect PNG from magic bytes
            mime_type = "image/png" if decoded[:4] == b"\x89PNG" else "image/jpeg"
            return decoded, mime_type
        except Exception:
            pass

    raise FileNotFoundError(f"Image file not found: {image_source}")
