import os
from typing import Optional

def generate_column_description(name: str, series) -> str:
    """Try to generate a description for a column using a local HF model if configured.

    If no model is available, fallback to a heuristic description.
    """
    model_name = os.environ.get("LOCAL_LLM_MODEL")
    sample = None
    try:
        sample = series.dropna().astype(str).unique()[:5].tolist()
    except Exception:
        sample = None

    if model_name:
        try:
            # Lazy import to avoid requiring transformers unless configured
            from transformers import pipeline
            pipe = pipeline("text-generation", model=model_name, device=-1)
            prompt = f"Write a concise description (1 sentence) for a dataset column named '{name}'. Samples: {sample}\nDescription:"
            out = pipe(prompt, max_length=80, do_sample=False)
            text = out[0]["generated_text"]
            # strip prompt
            desc = text.split("Description:")[-1].strip()
            return desc
        except Exception:
            pass

    # Fallback heuristic
    dtype = str(getattr(series, "dtype", "object"))
    nunique = None
    try:
        nunique = int(series.nunique(dropna=True))
    except Exception:
        nunique = None

    if "id" in name.lower() or name.lower().endswith("_id"):
        return f"Identifier column; likely references another table (dtype={dtype})."
    if "date" in name.lower() or "time" in name.lower():
        return f"Timestamp-like column (dtype={dtype})."
    if nunique is not None and nunique <= 10:
        return f"Categorical column with {nunique} unique values (dtype={dtype})."
    return f"Column '{name}' of type {dtype}; sampled values: {sample[:5] if sample else 'N/A'}"
