"""Run the local MCP-style FastAPI server for DataModeler"""
import os
import uvicorn

if __name__ == "__main__":
    # Run the FastAPI app in datamodeler.mcp_server
    uvicorn.run("datamodeler.mcp_server:app", host="127.0.0.1", port=9000, reload=False)
