import base64
import json
import pathlib
from unittest.mock import MagicMock

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
    import httpx as _httpx
    from analyzer import load_image
    httpx_mock.add_response(url="https://example.com/missing.png", status_code=404)
    with pytest.raises(_httpx.HTTPStatusError):
        load_image("https://example.com/missing.png")


def test_load_image_from_raw_base64_jpeg():
    from analyzer import load_image
    # JPEG magic bytes: \xFF\xD8\xFF\xE0 followed by padding
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    jpeg_b64 = base64.b64encode(jpeg_bytes).decode()
    image_bytes, mime_type = load_image(jpeg_b64)
    assert image_bytes == jpeg_bytes
    assert mime_type == "image/jpeg"


VALID_ANALYSIS_RESPONSE = {
    "bands": [
        {"lane": "Treated", "estimated_kda": 52.0, "intensity": "strong", "certainty": "high", "notes": None}
    ],
    "lanes": [
        {"label": "Treated", "band_count": 1, "loading_control_detected": True, "quality": "good"}
    ],
    "qc_flags": [],
    "overall_quality": "good",
    "reasoning_steps": ["Identified 1 lane", "Band at ~52 kDa detected"],
    "narrative": "Clear band at expected MW.",
    "overall_interpretation": "Target protein expressed.",
    "certainty": "high",
}


def _make_mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.text = json.dumps(payload)
    return mock


def test_analyze_returns_analysis_result(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, AnalysisResult

    mocker.patch("analyzer.genai.Client").return_value.models.generate_content.return_value = (
        _make_mock_response(VALID_ANALYSIS_RESPONSE)
    )
    mocker.patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})

    inp = AnalysisInput(image_source=str(FIXTURE_PATH))
    result = analyze(inp)

    assert isinstance(result, AnalysisResult)
    assert result.error is False
    assert result.certainty == "high"
    assert len(result.bands) == 1
    assert result.bands[0].lane == "Treated"


def test_analyze_returns_error_on_image_unreadable(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, ErrorResult

    mocker.patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})

    inp = AnalysisInput(image_source="/nonexistent/blot.png")
    result = analyze(inp)

    assert isinstance(result, ErrorResult)
    assert result.error_type == "image_unreadable"


def test_analyze_returns_error_on_api_failure(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, ErrorResult

    mocker.patch("analyzer.genai.Client").return_value.models.generate_content.side_effect = (
        Exception("API rate limit exceeded")
    )
    mocker.patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})

    inp = AnalysisInput(image_source=str(FIXTURE_PATH))
    result = analyze(inp)

    assert isinstance(result, ErrorResult)
    assert result.error_type == "api_error"
    assert "rate limit" in result.detail


def test_analyze_returns_error_on_malformed_response(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, ErrorResult

    bad_response = MagicMock()
    bad_response.text = "this is not json {"
    mocker.patch("analyzer.genai.Client").return_value.models.generate_content.return_value = bad_response
    mocker.patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})

    inp = AnalysisInput(image_source=str(FIXTURE_PATH))
    result = analyze(inp)

    assert isinstance(result, ErrorResult)
    assert result.error_type == "parse_error"


def test_analyze_handles_not_a_blot_response(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, ErrorResult

    not_blot_response = {
        "error": True,
        "error_type": "not_a_blot",
        "detail": "Image appears to be a photograph, not a western blot.",
        "reasoning_steps": [],
        "narrative": None,
    }
    mocker.patch("analyzer.genai.Client").return_value.models.generate_content.return_value = (
        _make_mock_response(not_blot_response)
    )
    mocker.patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})

    inp = AnalysisInput(image_source=str(FIXTURE_PATH))
    result = analyze(inp)

    assert isinstance(result, ErrorResult)
    assert result.error_type == "not_a_blot"


def test_analyze_returns_error_on_missing_api_key(mocker):
    from analyzer import analyze
    from schema import AnalysisInput, ErrorResult

    mocker.patch.dict("os.environ", {}, clear=True)

    inp = AnalysisInput(image_source=str(FIXTURE_PATH))
    result = analyze(inp)

    assert isinstance(result, ErrorResult)
    assert result.error_type == "api_error"
    assert "GOOGLE_API_KEY" in result.detail
