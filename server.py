import json
from mcp.server.fastmcp import FastMCP
from analyzer import analyze
from schema import AnalysisInput

mcp = FastMCP("western-blot-mcp")


@mcp.tool()
def analyze_western_blot(
    image_source: str,
    antibody_target: str | None = None,
    expected_kda: float | None = None,
    lane_labels: list[str] | None = None,
    loading_control: str | None = None,
    notes: str | None = None,
) -> str:
    """
    Analyze a western blot image. Returns structured band detection, lane QC,
    image quality flags, and step-by-step reasoning so researchers can validate
    every conclusion. Powered by Gemini 2.0 Flash (requires GOOGLE_API_KEY).

    Args:
        image_source: File path, HTTP/HTTPS URL, or base64-encoded image data.
        antibody_target: Protein being probed (e.g. 'p53'). Improves accuracy.
        expected_kda: Expected molecular weight in kDa. Improves accuracy.
        lane_labels: Ordered lane names left to right (e.g. ['Control', 'Treated']).
        loading_control: Loading control protein name (e.g. 'GAPDH', 'beta-actin').
        notes: Any additional experimental context (e.g. 'hypoxia experiment').
    """
    inp = AnalysisInput(
        image_source=image_source,
        antibody_target=antibody_target,
        expected_kda=expected_kda,
        lane_labels=lane_labels,
        loading_control=loading_control,
        notes=notes,
    )
    result = analyze(inp)
    return json.dumps(result.model_dump(), indent=2)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
