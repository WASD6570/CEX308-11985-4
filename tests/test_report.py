from pathlib import Path
import importlib.util
import shutil


def test_report_builds_from_public_inputs_only(tmp_path):
    from build_report import build_report
    root = Path(__file__).parents[1]
    for directory in ["report", "data/reference"]:
        assert (root / directory).is_dir(), f"Missing public inputs: {directory}"
        shutil.copytree(root / directory, tmp_path / directory)
    (tmp_path / "data/raw").mkdir(parents=True)
    shutil.copy2(root / "data/raw/inventory.xlsx", tmp_path / "data/raw/inventory.xlsx")
    paths = build_report(tmp_path)
    assert paths["pdf"].is_file()
    assert not (tmp_path / "docs").exists()


def test_generated_pdf_covers_five_answers_and_verified_sources(tmp_path):
    assert importlib.util.find_spec("build_report") is not None, "Report builder not implemented"
    import pymupdf
    from build_report import build_report
    root = Path(__file__).parents[1]
    paths = build_report(root, output_dir=tmp_path)
    document = pymupdf.open(paths["pdf"])
    assert paths["html"].is_file()
    assert "<style>" in paths["html"].read_text(), "HTML must keep its styling outside the project"
    text = " ".join("\n".join(page.get_text() for page in document).split())
    for required in ["1. Costo de adquisición", "2. Conversión a dólares", "3. Valor promedio del stock",
                     "4. Rendimientos anuales", "5. Costo anual de oportunidad", "6. Conclusiones", "7. Actividad extra", "8. Fuentes",
                     "Mínimo sin restricciones", "Objetivo mensual", "límite predictivo", "NIST", "MIT",
                     "meses completos", "1 + 1/n", "n − 1", "R + L", "no es el stock promedio",
                     "6.011,29", "Precio de fábrica", "valor neto de los activos", "1.183,78", "4.112,51", "20.883,53", "2.067,75", "998,24",
                     "31/05/2025", "02/06/2025", "Módulo 3", "Módulo 4", "Eduardo Nicolas Sanchez Lopez"]:
        assert required in text, required
    for prohibited in ["/home/", "10/10", "[unverified]", "—"]:
        assert prohibited not in text, prohibited
    import re
    detailed_values = set(re.findall(r"\b\d[\d.]*,\d{3,}\b", text))
    assert detailed_values <= {"4.112,513514", "9,901322", "4,780024"}, detailed_values
    for amount in ["5,08 USD/bolsa", "USD 0,50", "USD 0,24", "ARS 7.900,00", "ARS 7.566,00"]:
        assert amount in text, amount
    assert "importes monetarios se muestran con dos decimales" in text
    assert len(document) == 6
    extra = document[4].get_text()
    assert "7. Actividad extra" in extra
    assert "Objetivo mensual" in extra
    assert "Stock promedio óptimo" not in extra
    assert "una garantía" in extra
    assert "Conclusión de la actividad" in extra
    normalized_extra = " ".join(extra.split())
    for wording in ["cobertura nominal", "varianza positiva", "No determina una cantidad óptima demostrada"]:
        assert wording in normalized_extra, wording
    assert "el límite de Student lo aproxima" not in normalized_extra
    links = [link["uri"] for page in document for link in page.get_links() if "uri" in link]
    assert any("portfolioId=239756" in url and "asOfDate=20250531" in url for url in links)
    assert any("portfolioId=314116" in url and "asOfDate=20250531" in url for url in links)
    assert any("lanacion.com.ar" in url for url in links)
    assert any("ocw.mit.edu" in url and "lect12.pdf" in url for url in links)
    assert any("nist.gov" in url and "predlimi.htm" in url for url in links)
    assert any("web.archive.org/web/20250315045624/" in url for url in links)
    for page in document:
        assert page.get_text().strip()
        for block in page.get_text("blocks"):
            assert block[0] >= 0 and block[1] >= 0
            assert block[2] <= page.rect.width + 1 and block[3] <= page.rect.height + 1
