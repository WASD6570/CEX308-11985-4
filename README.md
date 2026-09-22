# Inferencia Estadística TP4

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/WASD6570/CEX308-11985-4/blob/main/notebooks/inferencia_estadistica_tp4_colab.ipynb)

**Eduardo Nicolas Sanchez Lopez**

Costo de oportunidad del inventario de bolsas de fibra de 600 gramos. El notebook responde los cinco puntos de MAP-2 y desarrolla la actividad extra mediante un objetivo mensual de inventario condicionado a la demanda y sus supuestos estadísticos.

## Lectura y ejecución

- [Notebook con resultados](notebooks/inferencia_estadistica_tp4.ipynb).
- [Versión para Google Colab](https://colab.research.google.com/github/WASD6570/CEX308-11985-4/blob/main/notebooks/inferencia_estadistica_tp4_colab.ipynb).

En Colab, ejecutar todas las celdas en orden. La primera clona el repositorio, instala las dependencias necesarias y prepara Python. La planilla está incluida: no hace falta cargarla manualmente. Al repetir la ejecución se actualiza la rama `main` solo si no hay cambios locales y la actualización puede realizarse sin reescribir historia.

El informe PDF, su versión HTML, los resultados JSON y la auditoría de saldos se generan en `reports/generated/`. La última celda permite descargar el PDF en Colab; los demás archivos se pueden descargar desde su panel **Archivos**.

**GitHub y Colab no se sincronizan automáticamente en ambos sentidos.** Para conservar modificaciones hechas en Colab, usar **Archivo → Guardar una copia en GitHub** o **Guardar una copia en Drive**. Una copia en Drive no actualiza este repositorio por sí sola.

## Resultados de referencia

| Concepto | Resultado |
|---|---:|
| Costo informado por palet | ARS 7.574.225,00 |
| Bolsas por palet | 1.260 |
| Costo informado por bolsa | ARS 6.011,29 |
| MEP de cierre de referencia, 02/06/2025 | ARS 1.183,78/USD |
| Stock promedio corregido | 4.112,51 bolsas |
| Valor promedio del stock | USD 20.883,53 |
| Costo anual, escenario AOR | USD 2.067,75 |
| Costo anual, escenario SGOV | USD 998,24 |

Se utilizan retornos totales NAV a un año al 31/05/2025: AOR 9,901322 % y SGOV 4,780024 %. Son escenarios históricos, no pronósticos ni rentabilidades garantizadas. Los importes se presentan con dos decimales, sin redondeos intermedios.

## Criterios de cálculo

- Se conserva la planilla original. SHA-256: `240f403b1c5755b6fdd5082ad4c3b720358eafa7f6475508405d9f9773277f85`.
- El costo corresponde al subtotal «Costo Mza», antes de ganancia e IVA de venta. Su composición tributaria y el porcentaje del seguro requieren confirmación.
- La media utiliza el stock inicial y los 36 cierres corregidos. Es una media por registro, no ponderada por tiempo.
- Se aplica el MEP de junio de 2025 al promedio del registro completo, que contiene movimientos posteriores. No se reconstruye el stock disponible al 02/06/2025.
- La actividad extra propone un límite predictivo unilateral para un mes futuro. No determina una cantidad óptima demostrada: faltan validar períodos completos, demanda, plazo de entrega y cobertura.
- Las explicaciones del notebook y del PDF provienen de la misma plantilla, incluidas las precisiones sobre cobertura nominal y diferencia entre objetivo y stock promedio.

Las fuentes y sus fechas figuran en el notebook, el PDF y `data/reference/sources.json`. Los archivos de rendimientos contienen extractos factuales seleccionados de las respuestas del emisor, con el hash de la respuesta original; no son copias completas de las páginas web. El análisis posterior a la instalación no requiere descargar datos de mercado.

## Reproducción local

Requisitos: Python 3.12 o posterior y `uv`. Para generar el PDF se requieren las bibliotecas nativas usadas por WeasyPrint, disponibles en el entorno de ejecución verificado.

```bash
uv sync --locked --group dev
uv run pytest -q
uv run python src/build_report.py
```

Abrir `notebooks/inferencia_estadistica_tp4.ipynb` en VS Code o Jupyter y ejecutar de arriba hacia abajo. Para regenerar las versiones de los notebooks desde el código:

```bash
uv run python src/build_notebook.py
```

La regeneración elimina sus salidas guardadas; volver a ejecutar el notebook local para conservar los resultados visibles.

## Estructura

```text
notebooks/        Versiones local y Colab
src/              Cálculos y generadores
report/           Plantilla y estilo del informe
tests/            Pruebas de cálculos, fuentes, PDF y notebooks
data/raw/         Planilla original
data/reference/   Parámetros históricos, extractos y fuentes
```
