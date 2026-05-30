from typing import Literal
from pydantic import BaseModel


class AnalysisInput(BaseModel):
    image_source: str
    antibody_target: str | None = None
    expected_kda: float | None = None
    lane_labels: list[str] | None = None
    loading_control: str | None = None
    notes: str | None = None


class BandResult(BaseModel):
    lane: str
    estimated_kda: float
    intensity: Literal["faint", "moderate", "strong"]
    certainty: Literal["high", "moderate", "low"]
    notes: str | None = None


class LaneResult(BaseModel):
    label: str
    band_count: int
    loading_control_detected: bool
    quality: Literal["good", "acceptable", "poor"]


class QCFlag(BaseModel):
    type: Literal[
        "overexposure",
        "underexposure",
        "smearing",
        "background_noise",
        "unequal_loading",
        "loading_control_inappropriate",
        "loading_control_saturated",
        "ghost_band",
        "smile_effect",
        "image_integrity_note",
        "cropping_artifact",
        "other",
    ]
    severity: Literal["mild", "moderate", "severe"]
    location: str | None = None
    detail: str


class AnalysisResult(BaseModel):
    bands: list[BandResult]
    lanes: list[LaneResult]
    qc_flags: list[QCFlag]
    overall_quality: Literal["good", "acceptable", "poor"]
    reasoning_steps: list[str]
    narrative: str
    overall_interpretation: str
    certainty: Literal["high", "moderate", "low"]
    error: bool = False


class ErrorResult(BaseModel):
    error: bool = True
    error_type: Literal["image_unreadable", "not_a_blot", "api_error", "parse_error"]
    detail: str
    reasoning_steps: list[str] = []
    narrative: None = None
