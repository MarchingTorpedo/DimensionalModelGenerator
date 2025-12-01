"""Simple demo runner for DataModeler"""
import argparse
import os
import sys
import json
# Ensure `src` is importable when running this script directly
ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from datamodeler.langgraph_integration import run_datamodel_pipeline


def main(samples_dir, out_dir):
    print(f"Running DataModel pipeline (LangGraph) on: {samples_dir}")
    
    result = run_datamodel_pipeline(samples_dir, out_dir)
    
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return
    
    print(f"Loaded tables: {list(result['tables'].keys())}")
    print(f"Saved SQL to: {out_dir}/model.sql")
    print(f"Saved catalog to: {out_dir}/catalog.json")
    print(f"Generated ERD at: {result['erd_svg']}")
    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", default="samples", help="Samples input folder")
    parser.add_argument("--out", default="outputs", help="Output folder")
    args = parser.parse_args()
    main(args.samples, args.out)
