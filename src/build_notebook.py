"""Generate local and Colab notebooks from the same analytical sequence."""
from pathlib import Path
import textwrap
import nbformat


LOCAL_SETUP = '''
import sys
from pathlib import Path

PROJECT = next(
    path for path in [Path.cwd(), *Path.cwd().parents]
    if (path / "src/analysis.py").is_file()
)
sys.path.insert(0, str(PROJECT / "src"))
print("Entorno local preparado.")
'''

COLAB_SETUP = '''
import importlib.metadata
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from packaging.requirements import Requirement

REPOSITORY = "https://github.com/WASD6570/CEX308-11985-4.git"
PROJECT = Path("/content/CEX308-11985-4")

if not PROJECT.exists():
    subprocess.run(["git", "clone", "--depth", "1", "--branch", "main", REPOSITORY, str(PROJECT)], check=True)
else:
    origin = subprocess.check_output(["git", "-C", str(PROJECT), "remote", "get-url", "origin"], text=True).strip()
    if origin != REPOSITORY:
        raise RuntimeError("La carpeta existente pertenece a otro repositorio.")
    changes = subprocess.check_output(["git", "-C", str(PROJECT), "status", "--porcelain"], text=True)
    if changes.strip():
        raise RuntimeError("Hay cambios locales: guardarlos antes de actualizar el repositorio.")
    subprocess.run(["git", "-C", str(PROJECT), "pull", "--ff-only", "origin", "main"], check=True)

configuration = tomllib.loads((PROJECT / "pyproject.toml").read_text())
missing_packages = []
for specification in configuration["project"]["dependencies"]:
    requirement = Requirement(specification)
    try:
        installed_version = importlib.metadata.version(requirement.name)
        compatible = requirement.specifier.contains(installed_version)
    except importlib.metadata.PackageNotFoundError:
        compatible = False
    if not compatible:
        missing_packages.append(specification)
if missing_packages:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing_packages], check=True)

sys.path.insert(0, str(PROJECT / "src"))
# Reimportar código actualizado al ejecutar nuevamente en el mismo runtime.
for module in ["analysis", "build_report"]:
    sys.modules.pop(module, None)
os.chdir(PROJECT)
print("Repositorio preparado; ejecutar las celdas siguientes en orden.")
'''

ANALYSIS_SETUP = '''
import json
import math
import re
from IPython.display import HTML, display
from analysis import analyze, opportunity_cost, value_inventory
from build_report import build_report

result = analyze(PROJECT)
report_paths = build_report(PROJECT)
report_html = report_paths["html"].read_text()
sections = re.findall(r"(<h2>.*?)(?=<h2>|</body>)", report_html, flags=re.S)
assert len(sections) == 8
sources = json.loads((PROJECT / "data/reference/sources.json").read_text())["sources"]

notebook_style = """
<style>
.tp4-output {font-family:Arial,sans-serif; font-size:15px; line-height:1.5; max-width:980px; color:#17212b; background:white; padding:18px;}
.tp4-output h2,.tp4-output h3 {color:#174f7a;}
.tp4-output table {width:100%; border-collapse:collapse; margin:16px 0;}
.tp4-output th {background:#174f7a; color:white; text-align:left;}
.tp4-output td,.tp4-output th {border:1px solid #cbd5df; padding:8px;}
.tp4-output .num {text-align:right;}
.tp4-output .equation {text-align:center; padding:12px; line-height:1.8;}
.tp4-output .note,.tp4-output .result {background:#eaf3f9; border-left:3px solid #174f7a; padding:12px; margin:12px 0;}
.tp4-output .caption {font-size:13px; color:#536273;}
.tp4-output a {color:#174f7a;}
</style>
"""

def show_section(number):
    fragment = re.sub(r"</?section\\b[^>]*>", "", sections[number - 1])
    for source in sources:
        fragment = fragment.replace(f'href="#source-{source["id"]}"', f'href="{source["url"]}"')
    display(HTML(notebook_style + '<div class="tp4-output">' + fragment + '</div>'))

print("Planilla verificada y datos históricos comparables. Cálculo sin redondeos intermedios.")
'''


def build_notebooks(root, output_dir=None):
    root = Path(root)
    output = Path(output_dir) if output_dir else root / "notebooks"
    output.mkdir(parents=True, exist_ok=True)
    markdown = nbformat.v4.new_markdown_cell
    code = lambda source: nbformat.v4.new_code_cell(textwrap.dedent(source).strip())
    common = [
        markdown("## Datos y preparación del cálculo\n\nLa planilla se verifica mediante SHA-256. Se usan datos históricos fechados, no cotizaciones actuales. Las explicaciones y tablas se generan desde la misma plantilla que el informe PDF."),
        code(ANALYSIS_SETUP),
        code('''
        # 1. Costo de adquisición por bolsa, antes de ganancia e IVA de venta.
        unit_cost_ars = result["pallet_cost_ars"] / result["pallet_bags"]
        assert math.isclose(unit_cost_ars, result["unit_cost_ars"])
        show_section(1)
        '''),
        code('''
        # 2. Conversión con el MEP fechado.
        unit_cost_usd = unit_cost_ars / result["exchange_rate"]["ars_per_usd"]
        assert math.isclose(unit_cost_usd, result["unit_cost_usd"])
        show_section(2)
        '''),
        code('''
        # 3. Media de estados corregidos, no media ponderada por días.
        corrected_balances = [row["corrected_balance"] for row in result["stock_audit"]]
        mean_stock = sum(corrected_balances) / len(corrected_balances)
        stock_value_usd = value_inventory(mean_stock, unit_cost_ars, result["exchange_rate"]["ars_per_usd"])
        assert math.isclose(stock_value_usd, result["stock_value_usd"])
        show_section(3)
        '''),
        code('''
        # 4. Misma moneda, período, fecha y base NAV para ambos fondos.
        annual_returns = {fund["ticker"]: fund["annual_return"] for fund in result["funds"]}
        show_section(4)
        '''),
        code('''
        # 5. Escenarios anuales excluyentes: no se suman.
        annual_costs = {ticker: opportunity_cost(stock_value_usd, rate) for ticker, rate in annual_returns.items()}
        for fund in result["funds"]:
            assert math.isclose(annual_costs[fund["ticker"]], fund["annual_cost_usd"])
        show_section(5)
        '''),
        code("show_section(6)"),
        markdown("## Actividad extra\n\nLa regla de inventario se presenta simbólicamente. No se fijan una cobertura empresarial ni una cantidad numérica sin validar los meses, la demanda y el plazo de entrega."),
        code("show_section(7)"),
        code("show_section(8)"),
        markdown("## Archivos generados\n\nEl PDF, el HTML y los resultados JSON se encuentran en `reports/generated/`. En Colab pueden descargarse desde el panel **Archivos**. Los cambios hechos en Colab no se guardan automáticamente en GitHub; para conservarlos se utiliza **Archivo → Guardar una copia en GitHub** o **Guardar una copia en Drive**."),
        code('''
        # En Colab se descarga el PDF; localmente se indican las rutas relativas.
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(report_paths["pdf"]))
        else:
            for path in report_paths.values():
                print(f"Archivo generado: {path.relative_to(PROJECT)}")
        ''')
    ]
    paths = {}
    for kind, setup in [("local", LOCAL_SETUP), ("colab", COLAB_SETUP)]:
        title = "# Inferencia Estadística TP4\n\n**Eduardo Nicolas Sanchez Lopez**\n\nCosto de oportunidad del inventario de bolsas de fibra de 600 gramos. Ejecutar las celdas de arriba hacia abajo. Los importes monetarios se presentan con dos decimales; los cálculos conservan su precisión original."
        if kind == "colab":
            title += "\n\nLa primera celda carga y actualiza el repositorio público. Se necesita conexión a Internet; no es necesario cargar la planilla manualmente."
        notebook = nbformat.v4.new_notebook(cells=[markdown(title), code(setup), *common])
        notebook.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
        if kind == "colab":
            notebook.metadata["colab"] = {"name": "inferencia_estadistica_tp4_colab.ipynb", "provenance": []}
        for index, cell in enumerate(notebook.cells):
            cell.id = f"tp4-{index:02d}"
        suffix = "_colab" if kind == "colab" else ""
        path = output / f"inferencia_estadistica_tp4{suffix}.ipynb"
        nbformat.write(notebook, path)
        paths[kind] = path
    return paths


if __name__ == "__main__":
    for kind, path in build_notebooks(Path(__file__).resolve().parents[1]).items():
        print(f"{kind}: {path}")
