# GBP Lead Finder

Aplicação em Python para pesquisar empresas no **Google Business Profile**
(Google Maps) por **categoria** e **cidade**, coletando apenas dados
**públicos essenciais** — nome da empresa, categoria e telefone — e
exportando os resultados para **Excel (.xlsx)**.

## Como funciona

A aplicação tenta usar a **API oficial do Google Places** sempre que uma
chave de API estiver configurada (`GOOGLE_PLACES_API_KEY`). Essa é a forma
recomendada, suportada e sancionada pelo Google para extração
programática de dados de estabelecimentos.

Caso a chave **não** esteja configurada, a aplicação recorre
automaticamente a um **fallback via Playwright**, que navega no Google
Maps público (`google.com/maps`) como um usuário comum faria em um
navegador, coletando apenas informações visíveis publicamente.

> ⚠️ **Uso responsável**
> - A aplicação **não** tenta contornar CAPTCHAs, autenticações ou
>   quaisquer medidas de proteção do Google. Se um CAPTCHA/bloqueio for
>   detectado durante o fallback via Playwright, a coleta é **interrompida
>   imediatamente**.
> - Apenas dados **públicos** são coletados (nome, categoria e telefone
>   exibidos publicamente na ficha do estabelecimento).
> - Utilize esta aplicação respeitando os
>   [Termos de Serviço do Google Maps/Places](https://cloud.google.com/maps-platform/terms)
>   e a legislação aplicável (ex.: LGPD), especialmente quanto ao uso dos
>   dados coletados para fins comerciais (ex.: prospecção).
> - Priorize sempre a API oficial do Google Places, que é paga conforme uso
>   mas garante estabilidade, conformidade com os termos de uso e dados
>   estruturados corretamente.

## Estrutura do projeto

```
gbp_lead_finder/
├── app/
│   ├── __init__.py
│   ├── config.py              # Carregamento de variáveis de ambiente (.env)
│   ├── logger.py               # Configuração de logging (console + arquivo)
│   ├── models.py                # Dataclasses: SearchParams, BusinessRecord
│   ├── google_places_client.py  # Cliente da API oficial do Google Places
│   ├── playwright_scraper.py    # Fallback de coleta via Playwright
│   ├── exporter.py              # Exportação para .xlsx
│   └── collector.py             # Orquestrador (escolhe API ou Playwright)
├── main.py                      # Ponto de entrada (CLI)
├── requirements.txt
├── .env.example
└── README.md
```

## Requisitos

- Python 3.12 ou superior
- (Opcional, recomendado) Chave de API do Google Places ("Places API (New)")
- (Necessário apenas se não usar a API) Playwright + navegador Chromium

## Instalação

1. Clone ou copie este projeto para sua máquina.

2. Crie e ative um ambiente virtual (recomendado):

   ```bash
   python3.12 -m venv venv
   source venv/bin/activate        # Linux/macOS
   venv\Scripts\activate           # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. (Somente se for usar o fallback via Playwright) Instale o navegador
   Chromium necessário:

   ```bash
   playwright install chromium
   ```

5. Copie o arquivo de exemplo de variáveis de ambiente e configure conforme
   necessário:

   ```bash
   cp .env.example .env
   ```

   - Se você possui uma chave da **API do Google Places**, preencha
     `GOOGLE_PLACES_API_KEY` no arquivo `.env`. Veja como obter uma chave em:
     https://developers.google.com/maps/documentation/places/web-service/get-api-key
   - Se deixar em branco, a aplicação usará automaticamente o fallback via
     Playwright.

## Execução

Execute via linha de comando, informando categoria, cidade, estado e a
quantidade máxima de resultados desejada:

```bash
python main.py --categoria "Clínica de Estética" --cidade "São Luís" --estado "MA" --quantidade 10
```

### Parâmetros disponíveis

| Parâmetro       | Obrigatório | Descrição                                                   | Exemplo                |
|-----------------|-------------|---------------------------------------------------------------|-------------------------|
| `--categoria`   | Sim         | Categoria/segmento da empresa                                | `"Dentista"`            |
| `--cidade`      | Sim         | Cidade onde buscar                                            | `"São Luís"`            |
| `--estado`      | Sim         | Estado/UF                                                     | `"MA"`                  |
| `--quantidade`  | Não (padrão 10) | Quantidade máxima de resultados (máximo 10)              | `10`                    |

### Saída

Ao final da execução, um arquivo é gerado dentro da pasta `output/`
(configurável via `OUTPUT_DIR` no `.env`):

- `Categoria_Cidade_AAAAMMDD_HHMMSS.xlsx`

Cada arquivo contém apenas as colunas:

- **Nome da Empresa**
- **Categoria**
- **Telefone**

### Logs

Os logs de execução são gravados em `logs/app.log` (com rotação
automática) e também exibidos no console, incluindo:

- Início/fim da busca
- Fonte de dados utilizada (API ou Playwright)
- Erros de conexão, validação ou bloqueio/CAPTCHA
- Progresso da coleta

### Barra de progresso

Durante a coleta (tanto via API quanto via Playwright), uma barra de
progresso (`tqdm`) é exibida no terminal indicando o andamento da busca.

## Tratamento de erros

A aplicação trata, entre outros, os seguintes cenários:

- Parâmetros inválidos (categoria/cidade/estado vazios, quantidade fora do
  intervalo permitido).
- Falhas de conexão com a API do Google Places (timeout, erro HTTP).
- Chave de API inválida ou não configurada (uso automático do fallback).
- Detecção de CAPTCHA/bloqueio durante o uso do Playwright (a coleta é
  interrompida, sem tentativa de contorno).
- Ausência de resultados para os critérios informados.
- Falhas ao gerar os arquivos de exportação.

Em todos os casos, uma mensagem clara é exibida ao usuário no terminal e
detalhes adicionais são registrados no arquivo de log.

## Limitações conhecidas

- O fallback via Playwright depende da estrutura HTML atual do Google
  Maps, que pode mudar a qualquer momento e exigir ajustes nos seletores
  utilizados em `app/playwright_scraper.py`.
- Nem todo estabelecimento expõe telefone publicamente; nesses casos, o
  campo é preenchido com `"Não informado"`.
- A quantidade de resultados pode ser limitada pelo próprio Google Maps
  (paginação e limites de exibição).

## Licença de uso dos dados

Os dados coletados são públicos e devem ser utilizados em conformidade
com os Termos de Serviço do Google e a legislação de proteção de dados
aplicável (ex.: LGPD). Esta aplicação não realiza nenhum tipo de coleta de
dados privados, autenticados ou protegidos por CAPTCHA.
