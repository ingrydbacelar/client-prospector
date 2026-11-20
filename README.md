# Lead Finder

<p align="center">
  <img src="https://github.com/user-attachments/assets/a4074ce8-754e-4392-b9ac-c78f53df2ab2" alt="Lead Finder" />
</p>

Ferramenta para pesquisar empresas no **Google Business
Profile** (Google Maps) por **categoria** e **cidade**, coletando apenas
dados **públicos essenciais** (nome da empresa, categoria e telefone) e
exportando tudo para **Excel (.xlsx)**.

---

## O que a ferramenta faz

1. **Validação dos parâmetros** : categoria, cidade e estado preenchidos
   e quantidade dentro do intervalo permitido.
2. **Escolha da fonte** : se `GOOGLE_PLACES_API_KEY` estiver configurada,
   usa a API oficial do Google Places; caso contrário, usa o Playwright.
3. **Coleta** : busca os estabelecimentos da categoria na cidade e
   extrai **nome**, **categoria** e **telefone** de cada um.
4. **Proteção contra bloqueios** : se um CAPTCHA ou bloqueio for
   detectado no fallback, a coleta é **interrompida imediatamente**, sem
   nenhuma tentativa de contorno.
5. **Exportação** : gera uma planilha `.xlsx` na pasta `output/`.
6. **Registro** : grava logs de toda a execução em `logs/app.log`.

## Fontes de dados

| Fonte | Quando é usada | Observações |
|---|---|---|
| 🟢 **API do Google Places** | Quando `GOOGLE_PLACES_API_KEY` está configurada | Forma recomendada e sancionada pelo Google. Paga conforme o uso, mas estável, em conformidade com os termos e com dados estruturados. |
| 🟡 **Playwright (fallback)** | Quando a chave não está configurada | Navega no Google Maps público e coleta só o que é visível. Depende da estrutura HTML atual do Google Maps. |

## Dados coletados

| Coluna | Descrição |
|---|---|
| **Nome da Empresa** | Nome exibido na ficha do estabelecimento. |
| **Categoria** | Categoria da empresa. |
| **Telefone** | Telefone exibido publicamente; quando não houver, aparece como `Não informado`. |

---

## Pré-requisitos

- **Python 3.12+** instalado.
- **Chave da API do Google Places** ("Places API (New)"): opcional, mas
  recomendada. Veja como obter em
  https://developers.google.com/maps/documentation/places/web-service/get-api-key
- **Playwright + Chromium**: necessário apenas se você **não** usar a
  API.

## Instalação

Abra a pasta do projeto no VS Code, abra o terminal integrado
(`` Ctrl+` ``) e rode:

```bash
# 1. Criar e ativar um ambiente virtual
python3.12 -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. (Somente para o fallback via Playwright) Instalar o Chromium
playwright install chromium

# 4. Criar o arquivo de variáveis de ambiente
cp .env.example .env
```

No arquivo `.env`, preencha `GOOGLE_PLACES_API_KEY` se tiver a chave. Se
deixar em branco, a ferramenta usa o Playwright automaticamente.

## Como usar

Execute informando categoria, cidade, estado e a quantidade máxima de
resultados:

```bash
python main.py --categoria "Clínica de Estética" --cidade "São Luís" --estado "MA" --quantidade 10
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição | Exemplo |
|---|---|---|---|
| `--categoria` | Sim | Categoria/segmento da empresa | `"Dentista"` |
| `--cidade` | Sim | Cidade onde buscar | `"São Luís"` |
| `--estado` | Sim | Estado/UF | `"MA"` |
| `--quantidade` | Não (padrão 10) | Quantidade máxima de resultados (máximo 10) | `10` |

### Saída

Ao final, o arquivo é gerado na pasta `output/`:

```
Clinica_de_Estetica_Sao_Luis_20261120_143510.xlsx
```

> Durante a coleta, uma barra de progresso mostra o andamento.

## Estrutura do projeto

```
gbp_lead_finder/
├── main.py                      # ponto de entrada (CLI)
├── requirements.txt
├── .env.example
├── README.md
└── app/
    ├── config.py                # variáveis de ambiente (.env)
    ├── logger.py                # logging (console + arquivo)
    ├── models.py                # dataclasses: SearchParams, BusinessRecord
    ├── google_places_client.py  # cliente da API oficial do Google Places
    ├── playwright_scraper.py    # fallback de coleta via Playwright
    ├── exporter.py              # exportação para .xlsx
    └── collector.py             # orquestrador (escolhe API ou Playwright)
```

## Demonstração
<p align="center">
  <a href="https://github.com/ingrydbacelar/lead-finder">
    <img src="https://img.shields.io/badge/Acessar%20Lead%20Finder-14532D?style=for-the-badge&logoColor=white" alt="Acessar Lead Finder">
  </a>
</p>

## Autora
Ingryd Bacelar

> © 2026 Ingryd Bacelar. Todos os direitos reservados.

> Este projeto é disponibilizado exclusivamente para fins de demonstração e portfólio. É proibida a reprodução, cópia, modificação, distribuição ou utilização comercial do código sem autorização prévia da autora.
