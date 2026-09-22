from pathlib import Path
import json
import nbformat
from nbclient import NotebookClient


def test_local_and_colab_notebooks_share_six_answer_cells(tmp_path):
    from build_notebook import build_notebooks
    root = Path(__file__).parents[1]
    paths = build_notebooks(root, output_dir=tmp_path)
    local = nbformat.read(paths["local"], as_version=4)
    colab = nbformat.read(paths["colab"], as_version=4)
    assert [cell.source for cell in local.cells[2:]] == [cell.source for cell in colab.cells[2:]]
    assert "https://github.com/WASD6570/CEX308-11985-4.git" in colab.cells[1].source
    assert 'Path("/content/CEX308-11985-4")' in colab.cells[1].source
    assert "--ff-only" in colab.cells[1].source
    assert "reset --hard" not in colab.cells[1].source
    code_cells = [cell for cell in local.cells if cell.cell_type == "code"]
    assert len(code_cells) == 7, "One setup cell plus five answers and the optional activity"
    for number, cell in enumerate(code_cells[1:], start=1):
        assert f"render_answer(PROJECT, {number}, result)" in cell.source
    source = "\n".join(cell.source for cell in local.cells)
    for prohibited in ["build_report", "weasyprint", "files.download", "report_paths"]:
        assert prohibited not in source
    assert "annual_costs" in source
    assert "Fuentes" in local.cells[-1].source
    for notebook in [local, colab]:
        nbformat.validate(notebook)
        assert not any(cell.get("outputs") for cell in notebook.cells)


def test_six_executed_answers_have_reasoning_and_portable_outputs(tmp_path):
    from build_notebook import build_notebooks
    root = Path(__file__).parents[1]
    paths = build_notebooks(root, output_dir=tmp_path)
    notebook = nbformat.read(paths["local"], as_version=4)
    NotebookClient(notebook, timeout=180, kernel_name="python3",
                   resources={"metadata": {"path": str(root)}}).execute()
    outputs = [output for cell in notebook.cells for output in cell.get("outputs", [])]
    assert not any(output["output_type"] == "error" for output in outputs)
    assert str(root) not in json.dumps(outputs)
    assert "/home/" not in json.dumps(outputs)
    answers = [output["data"]["text/html"] for output in outputs if "text/html" in output.get("data", {})]
    assert len(answers) == 6
    for answer in answers:
        assert "Por qué" in answer
    for number, expected in enumerate(["6.011,29", "5,08", "20.883,53", "9,901322", "2.067,75", "cobertura nominal"]):
        assert expected in answers[number]
    assert "998,24" in answers[4]
    assert "No determina una cantidad óptima demostrada" in answers[5]
    assert "el límite de Student lo aproxima" not in answers[5]
    assert "1 + 1/n" in answers[5]
    assert "varianza positiva" in answers[5]
    assert "El promedio de la demanda de los meses observados" in answers[5]
    assert "mide cuánto varió la demanda entre esos meses" in answers[5]
    assert "d̄ es el pronóstico;" not in answers[5]
