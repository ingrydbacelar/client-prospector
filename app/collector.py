"""
Módulo orquestrador da coleta de dados.

Decide automaticamente qual estratégia usar:
1. API oficial do Google Places, se GOOGLE_PLACES_API_KEY estiver configurada.
2. Fallback via Playwright (Google Maps público), caso contrário.
"""

from __future__ import annotations

from app.config import settings
from app.google_places_client import GooglePlacesClient, GooglePlacesError
from app.logger import get_logger
from app.models import BusinessRecord, SearchParams
from app.playwright_scraper import CaptchaOrBlockDetected, PlaywrightScraper

logger = get_logger(__name__)


class CollectionError(Exception):
    """Erro genérico durante o processo de coleta de empresas."""


def collect_businesses(params: SearchParams) -> tuple[list[BusinessRecord], str]:
    """Coleta empresas usando a melhor fonte disponível.

    Args:
        params: Parâmetros de busca já validados.

    Returns:
        Tupla (lista de BusinessRecord, nome da fonte utilizada).

    Raises:
        CollectionError: Se todas as fontes de coleta falharem.
    """
    if settings.has_google_places_key:
        logger.info("Chave da API do Google Places detectada. Utilizando a API oficial.")
        try:
            client = GooglePlacesClient()
            records = client.search_businesses(params)
            return records, "Google Places API"
        except GooglePlacesError as exc:
            logger.error("Falha ao usar a API do Google Places: %s", exc)
            raise CollectionError(
                f"Falha ao consultar a API do Google Places: {exc}"
            ) from exc

    logger.warning(
        "GOOGLE_PLACES_API_KEY não configurada. Utilizando fallback via Playwright "
        "(dados públicos do Google Maps)."
    )
    try:
        scraper = PlaywrightScraper(
            headless=settings.playwright_headless,
            nav_timeout_ms=settings.playwright_nav_timeout_ms,
        )
        records = scraper.search_businesses(params)
        return records, "Playwright (Google Maps público)"
    except CaptchaOrBlockDetected as exc:
        logger.error("Coleta interrompida por bloqueio/CAPTCHA: %s", exc)
        raise CollectionError(str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Falha ao usar o Playwright: %s", exc)
        raise CollectionError(f"Falha ao coletar dados via Playwright: {exc}") from exc
