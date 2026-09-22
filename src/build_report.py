"""Build the executive report from verified local evidence."""
from pathlib import Path
import csv
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from weasyprint import HTML
from analysis import analyze


def format_number(value, digits=2):
    return f"{float(value):,.{digits}f}".translate(str.maketrans({",": ".", ".": ","}))


def build_report(root, output_dir=None):
    root = Path(root)
    output = Path(output_dir) if output_dir else root / "reports/generated"
    output.mkdir(parents=True, exist_ok=True)
    result = analyze(root)
    sources = json.loads((root / "data/reference/sources.json").read_text())["sources"]
    source_map = {item["id"]: item for item in sources}
    environment = Environment(loader=FileSystemLoader(root / "report"), autoescape=select_autoescape(["html"]))
    environment.filters["num"] = format_number
    def cite(identifier):
        if identifier not in source_map:
            raise ValueError(f"Unknown source {identifier}")
        return Markup(f'<sup class="citation"><a href="#source-{identifier}">[{identifier}]</a></sup>')
    template = environment.get_template("report_template.html")
    html = template.render(**result, sources=sources, cite=cite)
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<style>' + (root / "report/style.css").read_text() + '</style>')
    html_path = output / "TP4_Inferencia_Estadistica.html"
    pdf_path = output / "TP4_Inferencia_Estadistica.pdf"
    html_path.write_text(html)
    HTML(string=html, base_url=str(root / "report")).write_pdf(pdf_path)
    (output / "tp4_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    with (output / "inventory_audit.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result["stock_audit"][0]))
        writer.writeheader()
        writer.writerows(result["stock_audit"])
    return {"html": html_path, "pdf": pdf_path}


if __name__ == "__main__":
    for kind, path in build_report(Path(__file__).resolve().parents[1]).items():
        print(f"{kind}: {path}")
