import re

def guess_sql_type(pd_dtype, sample_values=None):
    t = str(pd_dtype)
    if t.startswith("int"):
        return "INTEGER"
    if t.startswith("float"):
        return "FLOAT"
    if "datetime" in t or "date" in t:
        return "TIMESTAMP"
    # fallback to varchar with length heuristic
    maxlen = 255
    if sample_values is not None:
        try:
            maxlen = max((len(str(x)) for x in sample_values if x is not None), default=50)
            maxlen = min(max(50, maxlen), 2000)
        except Exception:
            maxlen = 255
    return f"VARCHAR({maxlen})"

def normalize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^0-9A-Za-z_]+", "", name)
    return name.lower()
