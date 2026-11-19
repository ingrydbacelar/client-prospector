"""Exportação dos resultados coletados para arquivos .xlsx e .csv."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.logger import get_logger
from app.models import BusinessRecord

logger = get_logger(__name__)

_COLUMNS = ["Nome da Empresa", "Categoria", "Telefone", "Site", "Tem Site Próprio?"]


def _build_filename(category: str, city: str, extension: str) -> str:
    """Monta um nome de arquivo seguro e único com timestamp."""
    safe_category = "".join(c if c.isalnum() else "_" for c in category).strip("_")
    safe_city = "".join(c if c.isalnum() else "_" for c in city).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_category}_{safe_city}_{timestamp}.{extension}"


def export_to_csv(records: list[BusinessRecord], output_dir: Path, category: str, city: str) -> Path:
    """Exporta os registros para um arquivo .csv (separado por vírgula, UTF-8).

    Args:
        records: Lista de empresas coletadas.
        output_dir: Diretório de destino.
        category: Categoria pesquisada (usada no nome do arquivo).
        city: Cidade pesquisada (usada no nome do arquivo).

    Returns:
        Caminho do arquivo .csv gerado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / _build_filename(category, city, "csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(_COLUMNS)
        for record in records:
            writer.writerow(
                [
                    record.name,
                    record.category,
                    record.phone,
                    record.website or "",
                    "Sim" if record.has_own_website else "Não",
                ]
            )

    logger.info("Arquivo CSV exportado: %s", filepath)
    return filepath


def export_to_excel(records: list[BusinessRecord], output_dir: Path, category: str, city: str) -> Path:
    """Exporta os registros para um arquivo .xlsx.

    Args:
        records: Lista de empresas coletadas.
        output_dir: Diretório de destino.
        category: Categoria pesquisada (usada no nome do arquivo).
        city: Cidade pesquisada (usada no nome do arquivo).

    Returns:
        Caminho do arquivo .xlsx gerado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / _build_filename(category, city, "xlsx")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Empresas"

    sheet.append(_COLUMNS)
    for col_index in range(1, len(_COLUMNS) + 1):
        cell = sheet.cell(row=1, column=col_index)
        cell.font = Font(bold=True)

    for record in records:
        sheet.append(
            [
                record.name,
                record.category,
                record.phone,
                record.website or "",
                "Sim" if record.has_own_website else "Não",
            ]
        )

    for col_index, column_name in enumerate(_COLUMNS, start=1):
        if column_name == "Tem Site Próprio?":
            valores = ["Sim" if record.has_own_website else "Não" for record in records]
        else:
            valores = [str(getattr(record, _field_for(column_name), "") or "") for record in records]
        max_length = max([len(column_name)] + [len(v) for v in valores])
        sheet.column_dimensions[get_column_letter(col_index)].width = min(max_length + 4, 60)

    workbook.save(filepath)
    logger.info("Arquivo Excel exportado: %s", filepath)
    return filepath


def _field_for(column_name: str) -> str:
    """Mapeia o nome da coluna de exibição para o atributo do BusinessRecord."""
    mapping = {
        "Nome da Empresa": "name",
        "Categoria": "category",
        "Telefone": "phone",
        "Site": "website",
    }
    return mapping[column_name]
