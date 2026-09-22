"""Render each notebook answer with its calculations, assumptions and rationale."""
from pathlib import Path
import html
import json
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup


def format_number(value, digits=2):
    return f"{float(value):,.{digits}f}".translate(str.maketrans({",": ".", ".": ","}))


def render_answer(root, point, result):
    if point not in range(1, 7):
        raise ValueError("Expected one of the five questions or the optional activity")
    root = Path(root)
    sources = json.loads((root / "data/reference/sources.json").read_text())["sources"]
    source_map = {source["id"]: source for source in sources}
    environment = Environment(loader=FileSystemLoader(root / "notebook"),
                              autoescape=True, undefined=StrictUndefined)
    environment.filters["num"] = format_number

    def cite(identifier):
        source = source_map[identifier]
        url = html.escape(source.get("archived_url", source["url"]), quote=True)
        return Markup(f'<sup class="citation"><a href="{url}" target="_blank">[{identifier}]</a></sup>')

    content = environment.get_template("answers.html").render(point=point, cite=cite, **result)
    style = (root / "notebook/style.css").read_text()
    return f'<style>{style}</style><div class="tp4-output">{content}</div>'
