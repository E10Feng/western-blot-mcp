# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (also creates .venv automatically)
uv sync --extra dev

# Run all unit tests
uv run pytest --ignore=tests/test_integration.py

# Run a single test
uv run pytest tests/test_analyzer.py::test_analyze_returns_analysis_result -v

# Run integration test (requires API key)
$env:GOOGLE_API_KEY = "your-key"   # PowerShell
uv run pytest tests/test_integration.py -v -s

# Start the MCP server manually (blocks on stdio)
uv run python server.py
```

All commands use `uv run` — there is no globally installed Python. The project uses `[tool.uv] package = false` (flat layout, no wheel build).

## Architecture

Five files, one-way dependency chain:

```
schema.py → prompts.py → analyzer.py → server.py
```

**`schema.py`** — Pydantic models only. `AnalysisInput` (tool inputs), `AnalysisResult` (success), `ErrorResult` (failure). All enum fields use `Literal` types. `ErrorResult.narrative` is typed as `None` (not `str | None`) — intentional, error results never carry a narrative.

**`prompts.py`** — `SYSTEM_PROMPT` constant (the bulk of the domain knowledge) and `build_user_prompt(inp)`. The system prompt embeds peer-reviewed western blot knowledge directly: MW tolerance (5–20% for PTMs), GAPDH invalidity contexts (hypoxia, aging, metabolic stress), loading control saturation, smile effect, image integrity language. This is where scientific accuracy lives — changes here affect output quality.

**`analyzer.py`** — Two concerns: `load_image()` (handles file path / URL / data URI / raw base64 with magic-byte MIME detection) and `analyze()` (calls LiteLLM, returns `AnalysisResult | ErrorResult`). Never raises — all errors are returned as `ErrorResult`. `GOOGLE_API_KEY` is aliased to `GEMINI_API_KEY` for backward compatibility before the LiteLLM call.

**`server.py`** — FastMCP wrapper. Registers one tool (`analyze_western_blot`), calls `analyze()`, serializes the result as JSON. The tool docstring is visible to calling agents — it includes the base64 workaround for Linux environments.

## Provider configuration

Model is set via `MODEL` env var as `provider/model-name` (LiteLLM format). Default: `gemini/gemini-3.1-flash-lite`. API keys follow LiteLLM conventions: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), `DEEPSEEK_API_KEY`. The model must support vision/image inputs.

## Testing patterns

- Unit tests mock `analyzer.litellm.completion` (not the Gemini SDK — that was replaced).
- Mock responses must use OpenAI-style shape: `mock.choices[0].message.content = json.dumps(payload)`.
- `test_analyze_returns_error_on_image_unreadable` needs no API key mock — image loading fails before the LiteLLM call.
- The integration test (`tests/test_integration.py`) is skipped automatically without `GOOGLE_API_KEY`.

## Claude Desktop deployment

The server runs as a stdio MCP server. On Windows with the Store version of Claude Desktop, the config lives at:
`%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

Use the full path to `uv.exe` (e.g. `C:\Users\<user>\.local\bin\uv.exe`) since Store apps don't inherit PATH. Claude's Linux environment cannot access Windows file paths — callers should pass images as base64.
