from schema import AnalysisInput


def test_system_prompt_contains_domain_knowledge():
    from prompts import SYSTEM_PROMPT
    assert "molecular weight ladder" in SYSTEM_PROMPT
    assert "5–20%" in SYSTEM_PROMPT
    assert "GAPDH" in SYSTEM_PROMPT
    assert "hypoxia" in SYSTEM_PROMPT
    assert "loading_control_saturated" in SYSTEM_PROMPT
    assert "image_integrity_note" in SYSTEM_PROMPT
    assert "smile" in SYSTEM_PROMPT.lower()


def test_system_prompt_contains_output_schema():
    from prompts import SYSTEM_PROMPT
    assert "reasoning_steps" in SYSTEM_PROMPT
    assert "overall_interpretation" in SYSTEM_PROMPT
    assert "overall_quality" in SYSTEM_PROMPT


def test_build_user_prompt_minimal():
    from prompts import build_user_prompt
    inp = AnalysisInput(image_source="blot.png")
    prompt = build_user_prompt(inp)
    assert "Analyze this western blot" in prompt
    assert "Antibody target" not in prompt
    assert "Expected molecular weight" not in prompt


def test_build_user_prompt_with_all_context():
    from prompts import build_user_prompt
    inp = AnalysisInput(
        image_source="blot.png",
        antibody_target="p53",
        expected_kda=53.0,
        lane_labels=["Control", "Treated"],
        loading_control="GAPDH",
        notes="Hypoxia experiment, 24h treatment",
    )
    prompt = build_user_prompt(inp)
    assert "p53" in prompt
    assert "53.0 kDa" in prompt
    assert "Control" in prompt
    assert "Treated" in prompt
    assert "GAPDH" in prompt
    assert "Hypoxia experiment" in prompt


def test_build_user_prompt_partial_context():
    from prompts import build_user_prompt
    inp = AnalysisInput(image_source="blot.png", antibody_target="Akt", expected_kda=60.0)
    prompt = build_user_prompt(inp)
    assert "Akt" in prompt
    assert "60.0 kDa" in prompt
    assert "Loading control" not in prompt
