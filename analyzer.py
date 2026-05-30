import base64
import json
import mimetypes
import os
from pathlib import Path

import httpx
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT, build_user_prompt
from schema import AnalysisInput, AnalysisResult, ErrorResult


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


def analyze(inp: AnalysisInput) -> AnalysisResult | ErrorResult:
    """Call Gemini to analyze a western blot image and return structured results."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return ErrorResult(error_type="api_error", detail="GOOGLE_API_KEY environment variable is not set")

    try:
        image_bytes, mime_type = load_image(inp.image_source)
    except Exception as e:
        return ErrorResult(error_type="image_unreadable", detail=str(e))

    client = genai.Client(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=build_user_prompt(inp)),
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
    except Exception as e:
        return ErrorResult(error_type="api_error", detail=str(e))

    if not response.text:
        return ErrorResult(error_type="api_error", detail="Gemini returned an empty response (possible safety filter or content block)")

    try:
        raw = json.loads(response.text)
        if raw.get("error"):
            return ErrorResult(**raw)
        return AnalysisResult(**raw)
    except Exception as e:
        return ErrorResult(
            error_type="parse_error",
            detail=f"Could not parse LLM response: {e}",
        )
