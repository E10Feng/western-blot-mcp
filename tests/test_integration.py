import os
import pytest
from schema import AnalysisResult, ErrorResult


# Open-access western blot figure from: "Blind spots on western blots" (PLOS ONE, 2022)
# doi: 10.1371/journal.pone.0273823
BLOT_URL = "https://journals.plos.org/plosone/article/figure/image?size=medium&id=10.1371/journal.pone.0273823.g001"


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
