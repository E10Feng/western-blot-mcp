# Installation

## Requirements

- Python 3.11 or later (managed automatically by uv)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- A Google API key with Gemini access (free tier works): https://aistudio.google.com/apikey

## Install

Clone or download this repository, then install dependencies:

```bash
uv sync
```

## Configure Claude Desktop

Open your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following entry (replace `/path/to/plot_mcp` with the actual path to this directory):

```json
{
  "mcpServers": {
    "western-blot": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/plot_mcp", "python", "server.py"],
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. The `analyze_western_blot` tool will now be available.

## Optional: Change the model

By default, `gemini-2.0-flash` is used (cheapest capable multimodal model). To use a different model:

```json
"env": {
  "GOOGLE_API_KEY": "your-key",
  "GEMINI_MODEL": "gemini-1.5-pro"
}
```

## Usage example

Once configured in Claude Desktop, you can say:

> Analyze this western blot: /path/to/blot.png — I'm probing for p53 (expected 53 kDa), with GAPDH as loading control. Lanes are: Control, Treated 1h, Treated 24h.

Or with a URL:

> Use the western blot tool on this image: https://example.com/blot.jpg

## Why use this instead of just uploading to ChatGPT?

- **Automation**: Agents can call `analyze_western_blot` in a loop across hundreds of images without manual intervention
- **Structured output**: Results are always the same JSON schema — band positions, QC flags, reasoning steps — consumable by other tools
- **Auditable reasoning**: Every conclusion includes `reasoning_steps` you can validate or challenge step by step
- **Reproducibility**: Same image + same parameters always returns the same structured format across your entire lab

## Running tests

```bash
# Unit tests only
uv run pytest --ignore=tests/test_integration.py

# Integration test (requires GOOGLE_API_KEY)
$env:GOOGLE_API_KEY = "your-key"   # Windows PowerShell
uv run pytest tests/test_integration.py -v -s
```
