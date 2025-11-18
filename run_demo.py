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

from datamodeler import core
from datamodeler import erd as erd_module


def main(samples_dir, out_dir):
    print(f"Loading inputs from: {samples_dir}")
    tables = core.load_all_inputs(samples_dir)
    print(f"Loaded tables: {list(tables.keys())}")

    profile = core.profile_tables(tables)
    pks = core.detect_primary_keys(tables)
    fks = core.detect_foreign_keys(tables)

    sql = core.build_sql(tables, pks, fks)
    os.makedirs(out_dir, exist_ok=True)
    sql_path = os.path.join(out_dir, "model.sql")
    core.save_sql(sql, sql_path)
    print(f"Saved SQL to: {sql_path}")

    catalog = core.build_catalog(profile)
    cat_path = os.path.join(out_dir, "catalog.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"Saved catalog to: {cat_path}")

    # build a tables summary for ERD
    tables_summary = {}
    for t, meta in profile.items():
        cols = []
        for c in meta["columns"]:
            cols.append({"name": c["name"], "type": c["dtype"], "pk": (pks.get(t) == c["name"])})
        tables_summary[t] = cols

    erd_path = os.path.join(out_dir, "erd")
    erd_module.generate_erd(tables_summary, fks, erd_path)
    print(f"Generated ERD at: {erd_path}.svg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", default="samples", help="Samples input folder")
    parser.add_argument("--out", default="outputs", help="Output folder")
    args = parser.parse_args()
    main(args.samples, args.out)
