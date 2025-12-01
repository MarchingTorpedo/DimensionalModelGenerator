"""Minimal FastAPI MCP-style endpoint to accept dataset files and return generated artifacts.

This is a scaffold for future MCP integration. It accepts file uploads (CSV or JSON), runs
the local datamodeler on them, and returns the generated SQL and catalog JSON in a ZIP.

Note: This server runs locally and uses the same core code; no external AI keys required.
"""
import io
import os
import json
import zipfile
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from datamodeler import core
from datamodeler import erd as erd_module
from datamodeler.langgraph_integration import run_datamodel_pipeline

app = FastAPI(title="DataModeler MCP Scaffold")

# Serve a small web UI from /ui
WEB_UI_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "..", "web_ui")
WEB_UI_DIR = os.path.abspath(WEB_UI_DIR)
if os.path.isdir(WEB_UI_DIR):
    app.mount("/ui", StaticFiles(directory=WEB_UI_DIR), name="web_ui")


def _check_api_key(x_api_key: str | None = Header(default=None)):
    """If `MCP_API_KEY` env var is set, require the header to match it."""
    required = os.environ.get("MCP_API_KEY")
    if required:
        if not x_api_key or x_api_key != required:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/generate")
async def generate_model(files: List[UploadFile] = File(...), _auth: None = Depends(_check_api_key)):
    """Accept uploaded CSV/JSON files, run the datamodeler, and return a ZIP with outputs.

    The ZIP contains `model.sql`, `catalog.json`, and (if generated) `erd.svg` and `erd.gv`.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    tmpdir = os.path.abspath("./.mcp_tmp")
    os.makedirs(tmpdir, exist_ok=True)

    # save uploaded files into tmpdir
    saved_paths = []
    for f in files:
        fname = os.path.join(tmpdir, f.filename)
        with open(fname, "wb") as out:
            content = await f.read()
            out.write(content)
        saved_paths.append(fname)

    # Run the LangGraph pipeline
    result = run_datamodel_pipeline(tmpdir, tmpdir)
    
    if result.get("error"):
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {result['error']}")
    
    sql = result["sql"]
    catalog = result["catalog"]
    erd_svg = result.get("erd_svg")
    erd_gv = result.get("erd_gv")

    # package outputs into a zip in-memory
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("model.sql", sql)
        z.writestr("catalog.json", json.dumps(catalog, indent=2))
        if erd_svg and os.path.exists(erd_svg):
            z.write(erd_svg, arcname="erd.svg")
        if erd_gv and os.path.exists(erd_gv):
            z.write(erd_gv, arcname="erd.gv")

    mem.seek(0)

    return StreamingResponse(mem, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=datamodel_outputs.zip"})
