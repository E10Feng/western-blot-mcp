import pytest
from pydantic import ValidationError


def test_analysis_input_requires_image_source():
    from schema import AnalysisInput
    with pytest.raises(ValidationError):
        AnalysisInput()


def test_analysis_input_minimal():
    from schema import AnalysisInput
    inp = AnalysisInput(image_source="path/to/blot.png")
    assert inp.image_source == "path/to/blot.png"
    assert inp.antibody_target is None
    assert inp.expected_kda is None
    assert inp.lane_labels is None
    assert inp.loading_control is None
    assert inp.notes is None


def test_analysis_input_full():
    from schema import AnalysisInput
    inp = AnalysisInput(
        image_source="http://example.com/blot.png",
        antibody_target="p53",
        expected_kda=53.0,
        lane_labels=["Control", "Treated"],
        loading_control="GAPDH",
        notes="Hypoxia experiment",
    )
    assert inp.antibody_target == "p53"
    assert inp.expected_kda == 53.0
    assert inp.lane_labels == ["Control", "Treated"]


def test_band_result_valid():
    from schema import BandResult
    band = BandResult(lane="Treated", estimated_kda=52.0, intensity="strong", certainty="high")
    assert band.intensity == "strong"
    assert band.certainty == "high"
    assert band.notes is None


def test_band_result_invalid_intensity():
    from schema import BandResult
    with pytest.raises(ValidationError):
        BandResult(lane="Treated", estimated_kda=52.0, intensity="huge", certainty="high")


def test_band_result_invalid_certainty():
    from schema import BandResult
    with pytest.raises(ValidationError):
        BandResult(lane="Treated", estimated_kda=52.0, intensity="strong", certainty="very_sure")


def test_lane_result_valid():
    from schema import LaneResult
    lane = LaneResult(label="Control", band_count=1, loading_control_detected=True, quality="good")
    assert lane.quality == "good"


def test_qc_flag_valid():
    from schema import QCFlag
    flag = QCFlag(type="overexposure", severity="mild", detail="Bands saturated in lane 2")
    assert flag.location is None


def test_qc_flag_invalid_type():
    from schema import QCFlag
    with pytest.raises(ValidationError):
        QCFlag(type="bad_type", severity="mild", detail="...")


def test_analysis_result_valid():
    from schema import AnalysisResult, BandResult, LaneResult, QCFlag
    result = AnalysisResult(
        bands=[BandResult(lane="L1", estimated_kda=50.0, intensity="strong", certainty="high")],
        lanes=[LaneResult(label="L1", band_count=1, loading_control_detected=True, quality="good")],
        qc_flags=[],
        overall_quality="good",
        reasoning_steps=["Identified 1 lane", "Band at 50 kDa detected"],
        narrative="Clear band at expected MW.",
        overall_interpretation="Target protein expressed.",
        certainty="high",
    )
    assert result.error is False


def test_error_result_valid():
    from schema import ErrorResult
    err = ErrorResult(error_type="image_unreadable", detail="File not found")
    assert err.error is True
    assert err.reasoning_steps == []
    assert err.narrative is None


def test_error_result_invalid_type():
    from schema import ErrorResult
    with pytest.raises(ValidationError):
        ErrorResult(error_type="unknown_error", detail="...")
