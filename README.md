# DimensionalModelGenerator — DataModeler (LangGraph-ready)

This project is a local Python tool to build a dimensional data model from CSV/JSON inputs and produce:

- SQL DDL for creating tables (saved as `.sql`)
- Automatic foreign key detection
- Column descriptions (uses a local AI model if available, otherwise falls back to heuristics)
- ERD diagram generation (Graphviz)
- JSON -> Star schema conversion helper
- CSV data catalog metadata (catalog.json)

Structure

- `src/datamodeler/` : library code
- `samples/` : sample CSV/JSON files that connect to each other
- `outputs/` : generated SQL, ERD, catalog files

Quick start (Windows PowerShell):

```pwsh
python -m pip install -r requirements.txt
python run_demo.py --samples samples --out outputs
```

Notes

- This is designed to work locally (no OpenAI API keys). If you have a local HF-compatible text generation model, configure it using the `LOCAL_LLM_MODEL` environment variable.
- There's a planned integration point for an MCP server; see comments in `src/datamodeler/`.

**MCP Server Scaffold**

We include a minimal FastAPI scaffold at `src/datamodeler/mcp_server.py` and a runner `run_mcp.py`.
Start it with:

```pwsh
python -m pip install -r requirements.txt
python run_mcp.py
```

Then POST files to `http://127.0.0.1:9000/generate` (multipart form upload) and you'll receive a ZIP with `model.sql` and `catalog.json`.

Authentication
---
If you set an environment variable `MCP_API_KEY`, the server will require a matching `x-api-key` header for uploads. Example (PowerShell):

```pwsh
$env:MCP_API_KEY = 'mysecret'
python run_mcp.py
```

Client
---
An example client is available at `run_client.py` to upload files and save the returned ZIP.

Web UI
---
Point your browser to `http://127.0.0.1:9000/ui/` to use a tiny upload form (no JS tooling required).

