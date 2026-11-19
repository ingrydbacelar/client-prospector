"""
Módulo de configuração da aplicação.

Responsável por carregar variáveis de ambiente (.env) e centralizar
parâmetros usados pelos demais módulos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env, se existir, sem sobrescrever
# variáveis já definidas no ambiente do sistema operacional.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Configurações globais da aplicação."""

    google_places_api_key: str | None = os.getenv("GOOGLE_PLACES_API_KEY") or None
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    playwright_headless: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    playwright_nav_timeout_ms: int = int(os.getenv("PLAYWRIGHT_NAV_TIMEOUT_MS", "30000"))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def has_google_places_key(self) -> bool:
        """Indica se há uma chave de API do Google Places configurada."""
        return bool(self.google_places_api_key)


settings = Settings()
