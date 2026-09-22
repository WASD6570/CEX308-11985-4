"""Generate local and Colab notebooks from the same analytical sequence."""
from pathlib import Path
import textwrap
import json
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
for module in ["analysis", "notebook_view"]:
    sys.modules.pop(module, None)
os.chdir(PROJECT)
print("Repositorio preparado; ejecutar las celdas siguientes en orden.")
'''

ANALYSIS_IMPORTS = """
import math
from IPython.display import HTML, display
from analysis import analyze, opportunity_cost, value_inventory
from notebook_view import render_answer
"""


def build_notebooks(root, output_dir=None):
    root = Path(root)
    output = Path(output_dir) if output_dir else root / "notebooks"
    output.mkdir(parents=True, exist_ok=True)
    markdown = nbformat.v4.new_markdown_cell
    code = lambda source: nbformat.v4.new_code_cell(textwrap.dedent(source).strip())
    answers = [
        code("""
        # Punto 1. Costo de adquisición: subtotal informado, sin margen de venta.
        result = analyze(PROJECT)
        unit_cost_ars = result["pallet_cost_ars"] / result["pallet_bags"]
        assert math.isclose(unit_cost_ars, result["unit_cost_ars"])
        display(HTML(render_answer(PROJECT, 1, result)))
        """),
        code("""
        # Punto 2. Conversión a USD con una cotización fechada común.
        unit_cost_usd = unit_cost_ars / result["exchange_rate"]["ars_per_usd"]
        assert math.isclose(unit_cost_usd, result["unit_cost_usd"])
        display(HTML(render_answer(PROJECT, 2, result)))
        """),
        code("""
        # Punto 3. Media de estados corregidos, no media ponderada por días.
        corrected_balances = [row["corrected_balance"] for row in result["stock_audit"]]
        mean_stock = sum(corrected_balances) / len(corrected_balances)
        stock_value_usd = value_inventory(mean_stock, unit_cost_ars, result["exchange_rate"]["ars_per_usd"])
        assert math.isclose(stock_value_usd, result["stock_value_usd"])
        display(HTML(render_answer(PROJECT, 3, result)))
        """),
        code("""
        # Punto 4. Retornos totales NAV: misma moneda, fecha y horizonte anual.
        annual_returns = {fund["ticker"]: fund["annual_return"] for fund in result["funds"]}
        display(HTML(render_answer(PROJECT, 4, result)))
        """),
        code("""
        # Punto 5. Escenarios de costo de oportunidad, no prueba de superioridad.
        annual_costs = {ticker: opportunity_cost(stock_value_usd, rate) for ticker, rate in annual_returns.items()}
        for fund in result["funds"]:
            assert math.isclose(annual_costs[fund["ticker"]], fund["annual_cost_usd"])
        display(HTML(render_answer(PROJECT, 5, result)))
        """),
        code("""
        # Actividad extra. Regla predictiva simbólica: no se inventa un stock óptimo.
        # La cobertura, la ventana mensual y la reposición requieren validación.
        display(HTML(render_answer(PROJECT, 6, result)))
        """),
    ]
    sources = json.loads((root / "data/reference/sources.json").read_text())["sources"]
    references = ["## Fuentes y datos", "",
                  "Planilla original: `data/raw/inventory.xlsx`. Se conserva el criterio de reconstrucción del TP2 y se excluye el saldo repetido de la fila 52.", "",
                  "Las tasas y el MEP son referencias históricas fechadas, no cotizaciones actuales. Consulta de fuentes: 21/09/2026.", ""]
    for source in sources:
        entry = f'- [{source["id"]}] [{source["title"]}]({source["url"]}).'
        if "archived_url" in source:
            entry += f' [Copia consultada del {source["archived_date"]}]({source["archived_url"]}).'
        references.append(entry)
    references += ["", "Los extractos factuales del emisor y los parámetros utilizados están en `data/reference/`. No se sustituyen por datos actuales al ejecutar el notebook."]
    paths = {}
    for kind, setup in [("local", LOCAL_SETUP), ("colab", COLAB_SETUP)]:
        title = "# Inferencia Estadística TP4\n\n**Eduardo Nicolas Sanchez Lopez**\n\nCosto de oportunidad del inventario de bolsas de fibra de 600 gramos. Una celda de preparación, una por cada uno de los cinco puntos y una para la actividad extra. Cada respuesta reúne resultado, método, justificación y límites. Ejecutar de arriba hacia abajo.\n\nLos importes monetarios se muestran con dos decimales; los cálculos conservan toda su precisión. No se generan archivos PDF al ejecutar este notebook."
        if kind == "colab":
            title += "\n\nLa primera celda clona o actualiza el repositorio público. No hace falta cargar la planilla manualmente. Para conservar cambios hechos aquí, usar Archivo → Guardar una copia en GitHub o en Drive; no hay sincronización automática en ambos sentidos."
        notebook = nbformat.v4.new_notebook(cells=[markdown(title), code(setup + ANALYSIS_IMPORTS), *answers, markdown("\n".join(references))])
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
