"""Modelos de dados usados na aplicação."""

from __future__ import annotations

import re
from dataclasses import dataclass

_CODIGO_PAIS_BRASIL = "55"
_DIGITOS_SEM_DDI_VALIDOS = (10, 11)


def _normalizar_telefone_para_link(telefone: str) -> str | None:
    """Normaliza um telefone para o formato usado em links do WhatsApp.

    Remove tudo que não for dígito e adiciona o código do Brasil (55)
    quando o número tiver 10 ou 11 dígitos (sem DDI). Números fora desses
    padrões, ou vazios/"Não informado", retornam None.

    Args:
        telefone: telefone em formato livre, como veio da fonte de dados.

    Returns:
        Telefone normalizado (apenas dígitos, com DDI) ou None se inválido.
    """
    if not telefone:
        return None

    somente_digitos = re.sub(r"\D", "", telefone)

    if not somente_digitos:
        return None

    if somente_digitos.startswith(_CODIGO_PAIS_BRASIL) and len(somente_digitos) in (12, 13):
        return somente_digitos

    if len(somente_digitos) in _DIGITOS_SEM_DDI_VALIDOS:
        return _CODIGO_PAIS_BRASIL + somente_digitos

    return None


_DOMINIOS_REDES_SOCIAIS = (
    "instagram.com",
    "facebook.com",
    "fb.com",
    "wa.me",
    "api.whatsapp.com",
    "linktr.ee",
    "linktree.com",
    "wa.link",
)


def _eh_link_de_rede_social(url: str) -> bool:
    """Verifica se uma URL aponta para uma rede social/agregador de links
    (Instagram, Facebook, WhatsApp, Linktree etc.) em vez de um site
    próprio da empresa.

    Args:
        url: URL a ser verificada.

    Returns:
        True se a URL pertencer a um domínio de rede social conhecido.
    """
    if not url:
        return False
    url_lower = url.lower()
    return any(dominio in url_lower for dominio in _DOMINIOS_REDES_SOCIAIS)


@dataclass(frozen=True)
class SearchParams:
    """Parâmetros de busca informados pelo usuário."""

    category: str
    city: str
    state: str
    max_results: int

    @property
    def query(self) -> str:
        """Monta a string de busca combinando categoria, cidade e estado."""
        return f"{self.category} em {self.city}, {self.state}"

    def validate(self) -> None:
        """Valida os parâmetros de busca.

        Raises:
            ValueError: Se algum parâmetro estiver inválido.
        """
        if not self.category or not self.category.strip():
            raise ValueError("A categoria não pode ser vazia.")
        if not self.city or not self.city.strip():
            raise ValueError("A cidade não pode ser vazia.")
        if not self.state or not self.state.strip():
            raise ValueError("O estado não pode ser vazio.")
        if self.max_results <= 0:
            raise ValueError("A quantidade máxima de resultados deve ser maior que zero.")
        if self.max_results > 10:
            raise ValueError("A quantidade máxima de resultados não pode exceder 10.")


@dataclass
class BusinessRecord:
    """Registro essencial de uma empresa coletada."""

    name: str
    category: str
    phone: str
    website: str | None = None
    """URL do site informado no perfil do Google Business Profile, quando
    disponível. Pode ser um site próprio ou um link para rede social
    (ex.: Instagram), dependendo do que a empresa cadastrou."""

    whatsapp_link_from_source: str | None = None
    """Link de WhatsApp extraído diretamente da fonte (ex.: botão do
    Google Maps), quando disponível. Tem prioridade sobre o link
    calculado a partir do telefone, pois pode conter um número ou
    mensagem pré-configurada diferente do telefone público exibido."""

    @property
    def whatsapp_link(self) -> str:
        """Retorna o link do WhatsApp para este contato.

        Prioridade:
            1. Link extraído diretamente da fonte (Google Maps), se
               disponível — pode ser diferente do telefone público, caso
               a empresa tenha configurado um número/mensagem específicos
               no botão de WhatsApp do perfil.
            2. Link construído a partir do telefone público, normalizado
               (apenas dígitos, com DDI 55 quando aplicável).

        Caso nenhuma das duas fontes produza um link válido, retorna
        uma string vazia.

        Returns:
            URL do WhatsApp (ex.: "https://wa.me/5511999999999") ou
            string vazia se não for possível determinar um link válido.
        """
        if self.whatsapp_link_from_source:
            return self.whatsapp_link_from_source

        telefone_normalizado = _normalizar_telefone_para_link(self.phone)
        if not telefone_normalizado:
            return ""
        return f"https://wa.me/{telefone_normalizado}"

    @property
    def has_own_website(self) -> bool:
        """Indica se a empresa possui site próprio.

        Retorna True somente se houver uma URL cadastrada em `website` e
        essa URL NÃO for um link de rede social/agregador (Instagram,
        Facebook, WhatsApp, Linktree etc.). Isso é útil para identificar
        leads que ainda não têm presença web própria — só perfil em
        redes sociais.

        Returns:
            True se a empresa tiver um site próprio; False se não tiver
            site algum ou se o único link cadastrado for de rede social.
        """
        if not self.website:
            return False
        return not _eh_link_de_rede_social(self.website)

    def as_dict(self) -> dict:
        """Converte o registro em um dicionário simples (para export)."""
        return {
            "Nome da Empresa": self.name,
            "Categoria": self.category,
            "Telefone": self.phone,
            "Site": self.website or "",
            "Tem Site Próprio?": "Sim" if self.has_own_website else "Não",
            "Link WhatsApp": self.whatsapp_link,
        }
