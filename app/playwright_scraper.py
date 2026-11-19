"""
Fallback de coleta via Playwright, usado somente quando a API do Google
Places não está configurada (GOOGLE_PLACES_API_KEY ausente).

IMPORTANTE - Uso responsável:
- Este módulo acessa apenas o Google Maps público (google.com/maps),
  navegando como um usuário comum faria em um navegador.
- Não realiza login, não tenta contornar CAPTCHAs e não usa proxies para
  burlar bloqueios. Caso o Google apresente um CAPTCHA ou bloqueio, o
  scraper interrompe a execução e informa o usuário, respeitando os
  Termos de Serviço do Google.
- Recomenda-se fortemente utilizar a API oficial do Google Places sempre
  que possível, pois é o método suportado e sancionado pelo Google para
  extração programática destes dados.
"""

from __future__ import annotations

from app.logger import get_logger
from app.models import BusinessRecord, SearchParams

logger = get_logger(__name__)


class CaptchaOrBlockDetected(Exception):
    """Levantada quando o Google apresenta CAPTCHA ou bloqueio de acesso."""


class PlaywrightScraper:
    """Coleta dados públicos do Google Maps via navegador automatizado."""

    MAPS_URL = "https://www.google.com/maps/search/"

    def __init__(self, headless: bool = True, nav_timeout_ms: int = 30000) -> None:
        self.headless = headless
        self.nav_timeout_ms = nav_timeout_ms

    def search_businesses(self, params: SearchParams) -> list[BusinessRecord]:
        """Executa a busca no Google Maps e retorna os registros encontrados.

        Args:
            params: Parâmetros de busca (categoria, cidade, estado, limite).

        Returns:
            Lista de BusinessRecord coletados.

        Raises:
            CaptchaOrBlockDetected: Se o Google exibir uma página de
                verificação/CAPTCHA. A execução é interrompida
                imediatamente, sem tentativa de contorno.
            RuntimeError: Para outros erros de navegação/coleta.
        """
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright não está instalado. Rode 'pip install playwright' e "
                "'playwright install chromium'."
            ) from exc

        from tqdm import tqdm  # import local para manter dependências agrupadas

        results: list[BusinessRecord] = []
        query = params.query
        search_url = self.MAPS_URL + query.replace(" ", "+")

        logger.info("Iniciando coleta via Playwright para a busca: '%s'", query)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            context = browser.new_context(locale="pt-BR")
            page = context.new_page()
            page.set_default_navigation_timeout(self.nav_timeout_ms)

            try:
                page.goto(search_url, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)

                self._check_for_block(page)

                self._scroll_results_panel(page, params.max_results)

                results = self._extract_records(page, params)

            except PlaywrightTimeoutError as exc:
                logger.error("Timeout ao navegar/carregar resultados: %s", exc)
                raise RuntimeError(
                    "Tempo excedido ao carregar resultados do Google Maps."
                ) from exc
            finally:
                context.close()
                browser.close()

        logger.info("Total de empresas obtidas via Playwright: %d", len(results))
        return results[: params.max_results]

    @staticmethod
    def _check_for_block(page) -> None:
        """Verifica se a página atual é um CAPTCHA/bloqueio do Google.

        Se detectado, interrompe a execução imediatamente (sem tentar
        contornar), conforme requisito de uso responsável.
        """
        content = page.content().lower()
        block_signals = ["captcha", "unusual traffic", "tráfego incomum", "/sorry/"]
        if any(signal in content for signal in block_signals) or "/sorry/" in page.url:
            logger.warning("Bloqueio/CAPTCHA detectado pelo Google. Encerrando coleta.")
            raise CaptchaOrBlockDetected(
                "O Google apresentou uma verificação (CAPTCHA) ou bloqueio de acesso. "
                "Esta aplicação não tenta contornar tais proteções. Recomenda-se "
                "configurar a API oficial do Google Places para evitar esse tipo de "
                "bloqueio."
            )

    @staticmethod
    def _scroll_results_panel(page, max_results: int) -> None:
        """Rola o painel de resultados para carregar mais itens (lazy load)."""
        from tqdm import tqdm

        feed_selector = 'div[role="feed"]'
        try:
            page.wait_for_selector(feed_selector, timeout=10000)
        except Exception:
            logger.warning("Painel de resultados não encontrado; pode haver poucos resultados.")
            return

        previous_count = 0
        stable_rounds = 0
        max_rounds = 25

        with tqdm(total=max_results, desc="Carregando resultados (scroll)", unit="empresa") as bar:
            for _ in range(max_rounds):
                cards = page.query_selector_all(f'{feed_selector} > div > a')
                current_count = len(cards)
                bar.n = min(current_count, max_results)
                bar.refresh()

                if current_count >= max_results:
                    break
                if current_count == previous_count:
                    stable_rounds += 1
                    if stable_rounds >= 3:
                        break
                else:
                    stable_rounds = 0

                previous_count = current_count
                page.evaluate(
                    f"""
                    const feed = document.querySelector('{feed_selector}');
                    if (feed) feed.scrollBy(0, 1000);
                    """
                )
                page.wait_for_timeout(1200)

    @staticmethod
    def _extract_records(page, params: SearchParams) -> list[BusinessRecord]:
        """Extrai nome, categoria e telefone de cada card de resultado."""
        records: list[BusinessRecord] = []
        cards = page.query_selector_all('div[role="feed"] > div > a')

        for card in cards[: params.max_results]:
            try:
                card.click()
                page.wait_for_timeout(1500)

                name = PlaywrightScraper._safe_text(page, "h1.DUwDvf, h1.fontHeadlineLarge")
                category = PlaywrightScraper._safe_text(
                    page, "button.DkEaL, span.mgr77e"
                )
                phone = PlaywrightScraper._safe_text(
                    page, 'button[data-item-id^="phone:tel:"]'
                )
                whatsapp_link_do_maps = PlaywrightScraper._extract_whatsapp_link(page)
                website = PlaywrightScraper._extract_website(page)

                if not name:
                    continue

                records.append(
                    BusinessRecord(
                        name=name,
                        category=category or params.category,
                        phone=phone or "Não informado",
                        website=website,
                        whatsapp_link_from_source=whatsapp_link_do_maps,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Falha ao extrair um card de resultado: %s", exc)
                continue

        return records

    @staticmethod
    def _extract_whatsapp_link(page) -> str | None:
        """Tenta extrair o link real do botão de WhatsApp do perfil no Maps.

        Algumas empresas configuram um botão de WhatsApp no perfil do
        Google Business, que pode apontar para um número ou mensagem
        diferentes do telefone público exibido. Quando esse botão existe,
        seu link (href) é extraído diretamente; caso contrário, retorna
        None e o link será calculado a partir do telefone público.

        Args:
            page: página (Page) do Playwright, com o perfil da empresa
                já carregado.

        Returns:
            URL do link de WhatsApp encontrado no perfil, ou None se não
            houver esse botão configurado.
        """
        seletores_possiveis = [
            'a[href*="wa.me"]',
            'a[href*="api.whatsapp.com"]',
            'a[aria-label*="WhatsApp" i]',
        ]

        for seletor in seletores_possiveis:
            elemento = page.query_selector(seletor)
            if elemento:
                href = elemento.get_attribute("href")
                if href and ("wa.me" in href or "whatsapp.com" in href):
                    return href

        return None

    @staticmethod
    def _extract_website(page) -> str | None:
        """Tenta extrair a URL do site cadastrado no perfil do Google Maps.

        O Google Maps exibe o site (quando cadastrado) em um botão com
        `data-item-id="authority"`. Esse link pode ser o site próprio da
        empresa ou, em alguns casos, um link direto para uma rede social
        (ex.: Instagram), quando é isso que a empresa cadastrou como
        "site" no perfil. A distinção entre site próprio e rede social é
        feita depois, em `BusinessRecord.has_own_website`.

        Args:
            page: página (Page) do Playwright, com o perfil da empresa
                já carregado.

        Returns:
            URL do site encontrado no perfil, ou None se não houver
            nenhum link de site cadastrado.
        """
        elemento = page.query_selector('a[data-item-id="authority"]')
        if elemento:
            href = elemento.get_attribute("href")
            if href:
                return href
        return None

    @staticmethod
    def _safe_text(page, selector: str) -> str:
        """Retorna o texto de um seletor CSS, ou string vazia se ausente."""
        el = page.query_selector(selector)
        if not el:
            return ""
        text = el.inner_text().strip()
        # Botões de telefone geralmente têm aria-label como "Telefone: (xx) ...";
        # tentamos extrair apenas o número quando possível.
        if "tel:" in (el.get_attribute("data-item-id") or ""):
            data_item = el.get_attribute("data-item-id") or ""
            return data_item.replace("phone:tel:", "").strip() or text
        return text
