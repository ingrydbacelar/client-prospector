"""
Cliente para a API "Places API (New)" do Google.

Utiliza o endpoint Text Search para buscar estabelecimentos por
categoria + cidade + estado, e o endpoint Place Details para obter o
telefone de cada estabelecimento (quando não retornado na busca).

Documentação oficial:
https://developers.google.com/maps/documentation/places/web-service/text-search
https://developers.google.com/maps/documentation/places/web-service/place-details
"""

from __future__ import annotations

from typing import Iterator

import requests
from tqdm import tqdm

from app.config import settings
from app.logger import get_logger
from app.models import BusinessRecord, SearchParams

logger = get_logger(__name__)

_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_PAGE_SIZE = 20  # máximo permitido pela API por página


class GooglePlacesError(Exception):
    """Erro genérico ao consultar a API do Google Places."""


class GooglePlacesClient:
    """Cliente HTTP simples para a Places API (New)."""

    def __init__(self, api_key: str | None = None, timeout: int | None = None) -> None:
        self.api_key = api_key or settings.google_places_api_key
        self.timeout = timeout or settings.request_timeout_seconds
        if not self.api_key:
            raise GooglePlacesError(
                "Chave da API do Google Places não configurada (GOOGLE_PLACES_API_KEY)."
            )

    def search_businesses(self, params: SearchParams) -> list[BusinessRecord]:
        """Busca empresas via Places API (New) - Text Search.

        Args:
            params: Parâmetros de busca (categoria, cidade, estado, limite).

        Returns:
            Lista de BusinessRecord com nome, categoria e telefone.

        Raises:
            GooglePlacesError: Em caso de falha de comunicação ou resposta
                inesperada da API.
        """
        results: list[BusinessRecord] = []
        page_token: str | None = None

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # FieldMask: solicitamos apenas os campos necessários para
            # reduzir custo e volume de dados, respeitando o princípio de
            # coletar somente o essencial.
            "X-Goog-FieldMask": (
                "places.displayName,places.primaryTypeDisplayName,"
                "places.nationalPhoneNumber,places.internationalPhoneNumber,"
                "places.websiteUri,nextPageToken"
            ),
        }

        with tqdm(
            total=params.max_results, desc="Buscando na API Google Places", unit="empresa"
        ) as bar:
            while len(results) < params.max_results:
                body: dict = {
                    "textQuery": params.query,
                    "languageCode": "pt-BR",
                    "regionCode": "BR",
                    "pageSize": min(_PAGE_SIZE, params.max_results - len(results)),
                }
                if page_token:
                    body["pageToken"] = page_token

                try:
                    response = requests.post(
                        _TEXT_SEARCH_URL, json=body, headers=headers, timeout=self.timeout
                    )
                except requests.RequestException as exc:
                    logger.error("Falha de conexão com a API do Google Places: %s", exc)
                    raise GooglePlacesError(f"Falha de conexão com a API: {exc}") from exc

                if response.status_code != 200:
                    logger.error(
                        "API do Google Places retornou status %s: %s",
                        response.status_code,
                        response.text[:500],
                    )
                    raise GooglePlacesError(
                        f"API retornou status {response.status_code}: {response.text[:300]}"
                    )

                data = response.json()
                places = data.get("places", [])

                if not places:
                    logger.info("Nenhum resultado adicional retornado pela API.")
                    break

                for place in places:
                    if len(results) >= params.max_results:
                        break
                    record = self._parse_place(place, fallback_category=params.category)
                    results.append(record)
                    bar.update(1)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        logger.info("Total de empresas obtidas via Google Places API: %d", len(results))
        return results

    @staticmethod
    def _parse_place(place: dict, fallback_category: str) -> BusinessRecord:
        """Converte um objeto 'place' da API em um BusinessRecord."""
        name = place.get("displayName", {}).get("text", "Não informado")
        category = place.get("primaryTypeDisplayName", {}).get("text") or fallback_category
        phone = (
            place.get("nationalPhoneNumber")
            or place.get("internationalPhoneNumber")
            or "Não informado"
        )
        website = place.get("websiteUri") or None
        return BusinessRecord(name=name, category=category, phone=phone, website=website)
