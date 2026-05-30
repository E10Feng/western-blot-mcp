import os
import pytest
from schema import AnalysisResult, ErrorResult


# Using httpbin.org as a reliable public image source
# (The specific western blot image URLs from Wikimedia were unavailable at test writing time)
BLOT_URL = "https://httpbin.org/image/png"


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping integration test",
)
def test_analyze_real_blot_returns_valid_schema():
    from analyzer import analyze
    from schema import AnalysisInput

    inp = AnalysisInput(
        image_source=BLOT_URL,
        notes="Public domain image for integration testing",
    )
    result = analyze(inp)

    assert isinstance(result, (AnalysisResult, ErrorResult)), (
        f"Expected AnalysisResult or ErrorResult, got {type(result)}"
    )

    if isinstance(result, AnalysisResult):
        assert isinstance(result.bands, list)
        assert isinstance(result.lanes, list)
        assert isinstance(result.reasoning_steps, list)
        assert len(result.reasoning_steps) > 0, "reasoning_steps must not be empty"
        assert result.overall_quality in ("good", "acceptable", "poor")
        assert result.certainty in ("high", "moderate", "low")
        assert isinstance(result.narrative, str) and len(result.narrative) > 0
    else:
        assert result.error is True
        assert result.error_type in ("image_unreadable", "not_a_blot", "api_error", "parse_error")
