from graphviz import Digraph
from graphviz.backend.execute import ExecutableNotFound
from typing import Dict, List

def generate_erd(tables: Dict[str, List[Dict]], fks: List[Dict], out_path: str):
    """Generate an ERD diagram using Graphviz.

    - tables: {table_name: [{name, type, pk(bool)}]}
    - fks: list of {child_table, child_col, parent_table, parent_col}
    """
    g = Digraph("erd", format="svg")
    g.attr(rankdir="LR")

    for tname, cols in tables.items():
        label_lines = [f"<b>{tname}</b>"]
        label_lines.append("<TABLE BORDER='0' CELLBORDER='1' CELLSPACING='0'>")
        for c in cols:
            pk = " (PK)" if c.get("pk") else ""
            label_lines.append(f"<TR><TD ALIGN='LEFT'>{c['name']}{pk}: {c.get('type','')}</TD></TR>")
        label_lines.append("</TABLE>")
        label = "\n".join(label_lines)
        g.node(tname, label=f"<<{label}>>", shape="plain")

    for fk in fks:
        g.edge(fk["child_table"], fk["parent_table"], label=f"{fk['child_col']} -> {fk['parent_col']}")

    try:
        g.render(out_path, cleanup=True)
    except ExecutableNotFound:
        # Graphviz `dot` not available on PATH. Save DOT source as fallback.
        gv_path = out_path + ".gv"
        with open(gv_path, "w", encoding="utf-8") as f:
            f.write(g.source)
        # Also save an SVG-like placeholder text to inform the user
        svg_path = out_path + ".svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write("<!-- Graphviz 'dot' executable not found. DOT source saved alongside. -->\n")
            f.write("<!-- DOT file: {} -->\n".format(gv_path))
        return
