from pathlib import Path
import importlib.util


def test_local_and_colab_notebooks_share_analysis(tmp_path):
    assert importlib.util.find_spec("build_notebook") is not None, "Notebook builder not implemented"
    import nbformat
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
    assert len([cell for cell in local.cells if cell.cell_type == "code"]) >= 8
    source = "\n".join(cell.source for cell in local.cells)
    assert "monthly_target" not in source, "No uncalibrated numerical inventory target"
    assert "annual_costs" in source
    for section in range(1, 9):
        assert f"show_section({section})" in source
    for notebook in [local, colab]:
        nbformat.validate(notebook)
        assert not any(cell.get("outputs") for cell in notebook.cells)


def test_executed_local_notebook_outputs_are_portable(tmp_path):
    import json
    import nbformat
    from nbclient import NotebookClient
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
