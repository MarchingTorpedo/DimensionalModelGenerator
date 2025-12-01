"""LangGraph integration for DataModeler pipeline.

This module wires the existing datamodeler functions as nodes in a LangGraph graph,
enabling orchestration, visualization, and advanced execution features.
"""
import os
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from datamodeler import core
from datamodeler import erd as erd_module


class DataModelState(TypedDict):
    """State for the DataModel graph."""
    input_path: str
    output_dir: str
    tables: dict
    profile: dict
    pks: dict
    fks: list
    sql: str
    catalog: dict
    erd_svg: str
    erd_gv: str
    error: str | None


def load_inputs_node(state: DataModelState) -> DataModelState:
    """Load CSV/JSON files from input_path."""
    try:
        tables = core.load_all_inputs(state["input_path"])
        return {"tables": tables, "error": None}
    except Exception as e:
        return {"error": f"Load failed: {str(e)}"}


def profile_tables_node(state: DataModelState) -> DataModelState:
    """Profile tables: compute column metadata and descriptions."""
    try:
        profile = core.profile_tables(state["tables"])
        return {"profile": profile, "error": None}
    except Exception as e:
        return {"error": f"Profile failed: {str(e)}"}


def detect_keys_node(state: DataModelState) -> DataModelState:
    """Detect primary keys and foreign keys."""
    try:
        pks = core.detect_primary_keys(state["tables"])
        fks = core.detect_foreign_keys(state["tables"])
        return {"pks": pks, "fks": fks, "error": None}
    except Exception as e:
        return {"error": f"Key detection failed: {str(e)}"}


def build_sql_node(state: DataModelState) -> DataModelState:
    """Generate SQL DDL statements."""
    try:
        sql = core.build_sql(state["tables"], state["pks"], state["fks"])
        return {"sql": sql, "error": None}
    except Exception as e:
        return {"error": f"SQL generation failed: {str(e)}"}


def build_catalog_node(state: DataModelState) -> DataModelState:
    """Build data catalog metadata."""
    try:
        catalog = core.build_catalog(state["profile"])
        return {"catalog": catalog, "error": None}
    except Exception as e:
        return {"error": f"Catalog generation failed: {str(e)}"}


def generate_erd_node(state: DataModelState) -> DataModelState:
    """Generate ERD diagram."""
    try:
        tables_summary = {}
        for t, meta in state["profile"].items():
            cols = []
            for c in meta["columns"]:
                cols.append({
                    "name": c["name"],
                    "type": c["dtype"],
                    "pk": (state["pks"].get(t) == c["name"])
                })
            tables_summary[t] = cols

        erd_base = os.path.join(state["output_dir"], "erd")
        erd_module.generate_erd(tables_summary, state["fks"], erd_base)
        return {
            "erd_svg": erd_base + ".svg",
            "erd_gv": erd_base + ".gv",
            "error": None
        }
    except Exception as e:
        return {"error": f"ERD generation failed: {str(e)}"}


def save_outputs_node(state: DataModelState) -> DataModelState:
    """Save SQL and catalog to output_dir."""
    try:
        os.makedirs(state["output_dir"], exist_ok=True)
        
        sql_path = os.path.join(state["output_dir"], "model.sql")
        core.save_sql(state["sql"], sql_path)
        
        cat_path = os.path.join(state["output_dir"], "catalog.json")
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(state["catalog"], f, indent=2)
        
        return {"error": None}
    except Exception as e:
        return {"error": f"Save outputs failed: {str(e)}"}


def build_datamodel_graph() -> StateGraph:
    """Build and compile the DataModel LangGraph."""
    workflow = StateGraph(DataModelState)
    
    # Add nodes
    workflow.add_node("load_inputs", load_inputs_node)
    workflow.add_node("profile_tables", profile_tables_node)
    workflow.add_node("detect_keys", detect_keys_node)
    workflow.add_node("build_sql", build_sql_node)
    workflow.add_node("build_catalog", build_catalog_node)
    workflow.add_node("generate_erd", generate_erd_node)
    workflow.add_node("save_outputs", save_outputs_node)
    
    # Define edges (execution flow)
    workflow.set_entry_point("load_inputs")
    workflow.add_edge("load_inputs", "profile_tables")
    workflow.add_edge("profile_tables", "detect_keys")
    workflow.add_edge("detect_keys", "build_sql")
    workflow.add_edge("build_sql", "build_catalog")
    workflow.add_edge("build_catalog", "generate_erd")
    workflow.add_edge("generate_erd", "save_outputs")
    workflow.add_edge("save_outputs", END)
    
    return workflow.compile()


def run_datamodel_pipeline(input_path: str, output_dir: str) -> dict:
    """Execute the DataModel pipeline using LangGraph.
    
    Args:
        input_path: Path to input CSV/JSON files or directory
        output_dir: Directory to save outputs
        
    Returns:
        Final state dict with all results
    """
    graph = build_datamodel_graph()
    
    initial_state = {
        "input_path": input_path,
        "output_dir": output_dir,
        "tables": {},
        "profile": {},
        "pks": {},
        "fks": [],
        "sql": "",
        "catalog": {},
        "erd_svg": "",
        "erd_gv": "",
        "error": None
    }
    
    result = graph.invoke(initial_state)
    return result
