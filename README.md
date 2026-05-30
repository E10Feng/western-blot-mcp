# western-blot-mcp

An MCP server that gives AI agents the ability to read and interpret western blot images. Every interpretation includes a step-by-step reasoning chain so researchers can validate, challenge, or trust each conclusion.

Powered by **Gemini** (cheapest capable multimodal model). You bring your own API key — no hosted service, no data leaves your machine except the image sent to Gemini.

---

## Features

- **Structured output** — bands, lanes, QC flags, and reasoning always returned in the same JSON schema, ready for downstream tools or lab notebooks
- **Auditable reasoning** — every conclusion has a `reasoning_steps` array you can validate step by step
- **Deep QC analysis** — detects overexposure, loading control problems, ghost bands, smile effect, image integrity issues, and more
- **Domain-aware prompting** — built-in knowledge of common pitfalls: GAPDH invalidity in hypoxia/aging/metabolic studies, loading control saturation, MW discrepancies from post-translational modifications
- **Qualitative certainty** — `high / moderate / low` certainty per band and overall, no fake numeric confidence scores
- **Flexible image input** — file path, URL, or base64-encoded image

---

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager — installs Python automatically)
- A Google API key with Gemini access — free tier works: https://aistudio.google.com/apikey
- Claude Desktop

---

## Installation

```bash
git clone https://github.com/E10Feng/western-blot-mcp.git
cd western-blot-mcp
uv sync
```

That's it. `uv sync` installs all dependencies into an isolated virtual environment.

---

## Configure Claude Desktop

Open your Claude Desktop config file:

| OS | Path |
|---|---|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

Add the `mcpServers` block (replace the directory path with where you cloned the repo):

```json
{
  "mcpServers": {
    "western-blot": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/western-blot-mcp", "python", "server.py"],
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here"
      }
    }
  }
}
```

> **Windows note:** Use the full path to `uv.exe` (e.g. `C:\\Users\\you\\.local\\bin\\uv.exe`) and double-backslashes in the directory path, since Claude Desktop on Windows may not inherit your shell PATH.

Restart Claude Desktop. You should see the western-blot server in the tools menu.

---

## Usage

Once configured, describe what you want to Claude and it will call the tool automatically. For best results, provide as much experimental context as you have — the more context, the more precise the reasoning.

**Example prompts:**

> Analyze this western blot: https://example.com/blot.jpg — I'm probing for SIRT1 knockdown vs NT-siRNA control. Loading control is Actin. Lanes are: NT-siRNA 1, NT-siRNA 2, NT-siRNA 3, SIRT1-siRNA 1, SIRT1-siRNA 2, SIRT1-siRNA 3.

> Use the western blot tool on the attached image. It's a p53 blot at 53 kDa with GAPDH loading control, comparing vehicle vs drug treatment.

**Passing a local image file:**

The server runs on your host OS, not in Claude's Linux environment. If you're uploading a file through Claude Desktop, tell Claude to encode it first:

```
Encode the uploaded image as base64 and pass it to analyze_western_blot as image_source.
```

---

## Output

Every call returns a JSON object with two sections:

**Structured data** (for downstream processing):
```json
{
  "bands": [
    { "lane": "Treated", "estimated_kda": 52, "intensity": "strong", "certainty": "high", "notes": null }
  ],
  "lanes": [
    { "label": "Control", "band_count": 1, "loading_control_detected": true, "quality": "good" }
  ],
  "qc_flags": [
    { "type": "overexposure", "severity": "mild", "location": "lane 3", "detail": "Band saturation visible — intensity comparison unreliable" }
  ],
  "overall_quality": "acceptable"
}
```

**Reasoning and narrative** (for researcher validation):
```json
{
  "reasoning_steps": [
    "Identified 4 lanes based on vertical banding structure",
    "Lane 1 (Treated) shows a band at ~52 kDa, consistent with expected p53 at 53 kDa",
    "GAPDH loading control bands are uniform — equal loading confirmed",
    "Mild overexposure in lane 3 — intensity comparison with lane 4 may be unreliable"
  ],
  "narrative": "The western blot shows clear p53 expression in the treated condition...",
  "overall_interpretation": "p53 upregulation confirmed. Results qualitatively valid.",
  "certainty": "moderate"
}
```

**QC flag types:** `overexposure` · `underexposure` · `smearing` · `background_noise` · `unequal_loading` · `loading_control_inappropriate` · `loading_control_saturated` · `ghost_band` · `smile_effect` · `image_integrity_note` · `cropping_artifact` · `other`

---

## Configuration options

| Environment variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | *(required)* | Your Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Any Gemini model with vision support |

To use a different model, add `GEMINI_MODEL` to the `env` block in your Claude Desktop config:

```json
"env": {
  "GOOGLE_API_KEY": "your-key",
  "GEMINI_MODEL": "gemini-2.0-flash"
}
```

---

## Running tests

```bash
# Unit tests (no API key needed)
uv run pytest --ignore=tests/test_integration.py

# Integration test (calls real Gemini API)
# macOS/Linux:
GOOGLE_API_KEY=your-key uv run pytest tests/test_integration.py -v -s
# Windows PowerShell:
$env:GOOGLE_API_KEY = "your-key"
uv run pytest tests/test_integration.py -v -s
```

---

## Why use this instead of uploading to ChatGPT?

Uploading a blot to ChatGPT gives you a prose response that varies every time. This server gives you:

- A **consistent JSON schema** every time — pipe results into a spreadsheet, lab notebook, or analysis pipeline
- **Batch processing** — an agent can call the tool across hundreds of images automatically
- **Reproducibility** — same image + same context = same structured output format across your whole lab
- **Auditable reasoning** — the `reasoning_steps` array lets you agree or disagree with each inference individually, not just the final verdict
