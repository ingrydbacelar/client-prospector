#!/usr/bin/env python3
"""
GBP Lead Finder
================

Aplicação de linha de comando para pesquisar empresas no Google Business
Profile (Google Maps) por categoria e cidade, coletando apenas dados
públicos essenciais (nome, categoria e telefone) e exportando os
resultados para Excel (.xlsx).

Uso:
    python main.py --categoria "Clínica de Estética" --cidade "São Luís" \
        --estado "MA" --quantidade 10

Consulte o README.md para mais detalhes de instalação e configuração.
"""

from __future__ import annotations

import argparse
import sys

from app.collector import CollectionError, collect_businesses
from app.config import settings
from app.exporter import export_to_excel
from app.logger import get_logger
from app.models import SearchParams

logger = get_logger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define e parseia os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Pesquisa empresas no Google Business Profile (Google Maps) por "
            "categoria e cidade, coletando apenas dados públicos essenciais."
        )
    )
    parser.add_argument(
        "--categoria",
        required=True,
        help='Categoria da empresa (ex.: "Clínica de Estética", "Psicólogo", "Dentista").',
    )
    parser.add_argument("--cidade", required=True, help='Cidade (ex.: "São Luís").')
    parser.add_argument("--estado", required=True, help='Estado/UF (ex.: "MA").')
    parser.add_argument(
        "--quantidade",
        type=int,
        default=10,
        help="Quantidade máxima de resultados a coletar (padrão: 10, máximo: 10).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da aplicação.

    Returns:
        Código de saída do processo (0 = sucesso, 1 = erro).
    """
    args = parse_args(argv)

    params = SearchParams(
        category=args.categoria,
        city=args.cidade,
        state=args.estado,
        max_results=args.quantidade,
    )

    try:
        params.validate()
    except ValueError as exc:
        logger.error("Parâmetros inválidos: %s", exc)
        print(f"Erro: {exc}")
        return 1

    logger.info(
        "Iniciando busca | categoria='%s' cidade='%s' estado='%s' quantidade=%d",
        params.category,
        params.city,
        params.state,
        params.max_results,
    )

    try:
        records, source = collect_businesses(params)
    except CollectionError as exc:
        logger.error("Falha na coleta de dados: %s", exc)
        print(f"Erro ao coletar dados: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro inesperado durante a coleta: %s", exc)
        print(f"Erro inesperado: {exc}")
        return 1

    if not records:
        logger.warning("Nenhuma empresa encontrada para os parâmetros informados.")
        print("Nenhuma empresa foi encontrada para os critérios informados.")
        return 0

    try:
        excel_path = export_to_excel(records, settings.output_dir, params.category, params.city)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao exportar resultados: %s", exc)
        print(f"Erro ao exportar resultados: {exc}")
        return 1

    print(f"\nFonte de dados utilizada: {source}")
    print(f"Total de empresas coletadas: {len(records)}")
    print(f"Arquivo Excel: {excel_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
