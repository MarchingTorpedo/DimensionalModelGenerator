import os
import json
from typing import Dict, List, Tuple
import pandas as pd
from collections import defaultdict

from .utils import guess_sql_type, normalize_name
from .ai import generate_column_description


def load_file(path: str) -> pd.DataFrame:
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    if path.lower().endswith(".json"):
        # try to read as JSON lines or normal JSON
        try:
            return pd.read_json(path, lines=True)
        except ValueError:
            return pd.read_json(path)
    raise ValueError("Unsupported file type: " + path)


def load_all_inputs(input_path: str) -> Dict[str, pd.DataFrame]:
    tables = {}
    if os.path.isdir(input_path):
        for fname in os.listdir(input_path):
            if fname.lower().endswith((".csv", ".json")):
                full = os.path.join(input_path, fname)
                key = normalize_name(os.path.splitext(fname)[0])
                tables[key] = load_file(full)
    else:
        # single file
        key = normalize_name(os.path.splitext(os.path.basename(input_path))[0])
        tables[key] = load_file(input_path)
    return tables


def profile_tables(tables: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    meta = {}
    for name, df in tables.items():
        cols = []
        for c in df.columns:
            s = df[c]
            # handle unhashable values (dict/list) by stringifying for uniqueness/sample
            try:
                nunique = int(s.nunique(dropna=True))
            except TypeError:
                try:
                    nunique = int(s.dropna().astype(str).nunique())
                except Exception:
                    nunique = None

            try:
                sample_vals = s.dropna().astype(str).unique()[:5].tolist()
            except Exception:
                sample_vals = []

            try:
                description = generate_column_description(c, s)
            except Exception:
                description = None

            cols.append({
                "name": c,
                "dtype": str(s.dtype),
                "nnulls": int(s.isna().sum()),
                "nunique": nunique,
                "sample": sample_vals,
                "description": description
            })
        meta[name] = {"rows": len(df), "columns": cols}
    return meta


def detect_primary_keys(tables: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    pks = {}
    for t, df in tables.items():
        for c in df.columns:
            if df[c].is_unique and df[c].notna().all():
                pks[t] = c
                break
        # fallback heuristics
        if t not in pks:
            for c in df.columns:
                if c.lower() == "id" or c.lower().endswith("_id"):
                    pks[t] = c
                    break
    return pks


def detect_foreign_keys(tables: Dict[str, pd.DataFrame]) -> List[Dict]:
    # naive detection: if child column values are subset of parent column values
    fks = []
    names = list(tables.keys())
    for i, child_name in enumerate(names):
        child = tables[child_name]
        for col in child.columns:
            if child[col].isnull().all():
                continue
            child_vals = set(child[col].dropna().astype(str).unique())
            for parent_name in names:
                if parent_name == child_name:
                    continue
                parent = tables[parent_name]
                for pcol in parent.columns:
                    parent_vals = set(parent[pcol].dropna().astype(str).unique())
                    if not parent_vals:
                        continue
                    # ratio of child values found in parent
                    matched = sum(1 for v in child_vals if v in parent_vals)
                    if matched == 0:
                        continue
                    ratio = matched / max(1, len(child_vals))
                    # heuristic thresholds
                    if ratio > 0.6 and len(parent_vals) <= len(parent):
                        fks.append({
                            "child_table": child_name,
                            "child_col": col,
                            "parent_table": parent_name,
                            "parent_col": pcol,
                            "match_ratio": ratio
                        })
    return fks


def build_sql(tables: Dict[str, pd.DataFrame], pks: Dict[str, str], fks: List[Dict]) -> str:
    statements = []
    for tname, df in tables.items():
        lines = [f"CREATE TABLE {tname} ("]
        col_lines = []
        for c in df.columns:
            dtype = guess_sql_type(df[c].dtype, sample_values=df[c].dropna().astype(str).head(50).tolist())
            col_lines.append(f"  {c} {dtype}")
        # primary key
        pk = pks.get(tname)
        if pk:
            col_lines.append(f"  ,PRIMARY KEY ({pk})")
        lines.append(",\n".join(col_lines)
        )
        lines.append(");")
        statements.append("\n".join(lines))

    # Add FK statements
    for fk in fks:
        stmt = f"ALTER TABLE {fk['child_table']} ADD FOREIGN KEY ({fk['child_col']}) REFERENCES {fk['parent_table']}({fk['parent_col']});"
        statements.append(stmt)

    return "\n\n".join(statements)


def build_catalog(profile_meta: Dict[str, Dict]) -> Dict:
    catalog = {"tables": {}}
    for t, m in profile_meta.items():
        catalog["tables"][t] = {
            "rows": m.get("rows"),
            "columns": [{
                "name": c["name"],
                "dtype": c["dtype"],
                "nnulls": c["nnulls"],
                "nunique": c["nunique"],
                "description": c.get("description")
            } for c in m.get("columns", [])]
        }
    return catalog


def save_sql(sql: str, out_file: str):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(sql)


def json_to_star(path: str) -> Dict[str, pd.DataFrame]:
    """Convert a JSON document (possibly nested) into a simple star schema.

    This is a basic flattening: top-level objects become fact table; arrays/nested objects become dimensions.
    """
    df = pd.read_json(path, lines=True)
    # naive approach: explode nested lists into new tables
    tables = {"fact": df.copy()}
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            exploded = df[[col]].explode(col).dropna()
            exploded = pd.DataFrame(exploded[col].tolist())
            name = normalize_name(col)
            tables[name] = exploded
            # drop from fact
            tables["fact"] = tables["fact"].drop(columns=[col])
    return tables
