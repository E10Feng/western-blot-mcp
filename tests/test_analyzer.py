import base64
import pathlib
import pytest


MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_BYTES = base64.b64decode(MINIMAL_PNG_B64)
FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "minimal.png"


def test_load_image_from_file_path():
    from analyzer import load_image
    image_bytes, mime_type = load_image(str(FIXTURE_PATH))
    assert image_bytes == MINIMAL_PNG_BYTES
    assert mime_type == "image/png"


def test_load_image_from_data_uri():
    from analyzer import load_image
    data_uri = f"data:image/png;base64,{MINIMAL_PNG_B64}"
    image_bytes, mime_type = load_image(data_uri)
    assert image_bytes == MINIMAL_PNG_BYTES
    assert mime_type == "image/png"


def test_load_image_from_raw_base64():
    from analyzer import load_image
    image_bytes, mime_type = load_image(MINIMAL_PNG_B64)
    assert image_bytes == MINIMAL_PNG_BYTES
    assert mime_type == "image/png"


def test_load_image_from_url(httpx_mock):
    from analyzer import load_image
    httpx_mock.add_response(
        url="https://example.com/blot.png",
        content=MINIMAL_PNG_BYTES,
        headers={"content-type": "image/png"},
    )
    image_bytes, mime_type = load_image("https://example.com/blot.png")
    assert image_bytes == MINIMAL_PNG_BYTES
    assert mime_type == "image/png"


def test_load_image_file_not_found():
    from analyzer import load_image
    with pytest.raises(FileNotFoundError, match="not found"):
        load_image("/nonexistent/path/blot.png")


def test_load_image_url_error(httpx_mock):
    from analyzer import load_image
    httpx_mock.add_response(url="https://example.com/missing.png", status_code=404)
    with pytest.raises(Exception):
        load_image("https://example.com/missing.png")


def test_load_image_from_raw_base64_jpeg():
    from analyzer import load_image
    # JPEG magic bytes: \xFF\xD8\xFF\xE0 followed by padding
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    jpeg_b64 = base64.b64encode(jpeg_bytes).decode()
    image_bytes, mime_type = load_image(jpeg_b64)
    assert image_bytes == jpeg_bytes
    assert mime_type == "image/jpeg"
