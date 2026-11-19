#!/usr/bin/env python3
"""
GBP Lead Finder - Interface Web
================================

Servidor HTTP local, usando apenas a biblioteca padrao do Python (nao
precisa instalar Flask nem nada alem do que o projeto ja usa). Ele serve
a interface web (pasta "web/") e expoe uma pequena API para rodar as
buscas do main.py, mostrando progresso e log em tempo real no navegador.

Como usar:
    1. Coloque este arquivo (e a pasta "web") na mesma pasta do main.py.
    2. De um duplo clique em "abrir_interface_web.bat", ou rode:
       python server.py
    3. O navegador abre automaticamente em http://127.0.0.1:8765/

Para parar o servidor, feche a janela do terminal ou pressione Ctrl+C.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Pasta do projeto = pasta onde este arquivo esta (funciona em qualquer
# maquina/local, sem precisar editar caminhos fixos).
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(PASTA_PROJETO, "web")
PORT = 8765

# Estado global compartilhado entre as requisicoes HTTP.
_lock = threading.Lock()
_estado = {
    "rodando": False,
    "log": [],        # lista de strings (linhas de log)
    "progresso": {},  # categoria -> status ("aguardando...", "buscando...", "concluido", "erro")
}


def _log(msg: str) -> None:
    with _lock:
        _estado["log"].append(msg)


def _set_status(categoria: str, status: str) -> None:
    with _lock:
        _estado["progresso"][categoria] = status


def _executar_buscas(categorias: list[str], cidade: str, uf: str, quantidade: int) -> None:
    main_py = os.path.join(PASTA_PROJETO, "main.py")

    with _lock:
        _estado["rodando"] = True
        _estado["log"] = []
        _estado["progresso"] = {c: "aguardando..." for c in categorias}

    _log(f"Iniciando buscas em {cidade}/{uf} (ate {quantidade} por categoria)")

    for categoria in categorias:
        _set_status(categoria, "buscando...")
        _log(f"\n--- Buscando categoria: {categoria} ---")

        comando = [
            sys.executable,
            main_py,
            "--categoria", categoria,
            "--cidade", cidade,
            "--estado", uf,
            "--quantidade", str(quantidade),
        ]

        try:
            processo = subprocess.run(
                comando,
                cwd=PASTA_PROJETO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as exc:  # noqa: BLE001
            _log(f"Erro ao executar main.py: {exc}")
            _set_status(categoria, "erro")
            continue

        if processo.stdout:
            _log(processo.stdout.strip())
        if processo.stderr:
            _log(processo.stderr.strip())

        _set_status(categoria, "concluido" if processo.returncode == 0 else "erro")

    _log("\nTodas as buscas foram concluidas. Verifique a pasta 'output'.")
    with _lock:
        _estado["rodando"] = False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # silencia log padrao no console
        pass

    def _send_json(self, data, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, caminho: str) -> None:
        tipos = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        ext = os.path.splitext(caminho)[1]
        with open(caminho, "rb") as f:
            conteudo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipos.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/status":
            with _lock:
                self._send_json(dict(_estado))
            return

        if path == "/":
            path = "/index.html"

        arquivo = os.path.normpath(os.path.join(WEB_DIR, path.lstrip("/")))
        if not arquivo.startswith(WEB_DIR) or not os.path.isfile(arquivo):
            self.send_error(404, "Arquivo nao encontrado")
            return

        self._send_static(arquivo)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/buscar":
            self.send_error(404)
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        try:
            dados = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            self._send_json({"erro": "JSON invalido."}, status=400)
            return

        with _lock:
            if _estado["rodando"]:
                self._send_json({"erro": "Ja existe uma busca em andamento."}, status=409)
                return

        categorias = [c.strip() for c in dados.get("categorias", []) if str(c).strip()]
        cidade = str(dados.get("cidade", "")).strip()
        uf = str(dados.get("estado", "")).strip()
        try:
            quantidade = int(dados.get("quantidade", 10))
        except (TypeError, ValueError):
            quantidade = 10
        quantidade = max(1, min(10, quantidade))

        if not categorias:
            self._send_json({"erro": "Adicione ao menos uma categoria."}, status=400)
            return
        if not cidade:
            self._send_json({"erro": "A cidade nao pode ficar vazia."}, status=400)
            return
        if not uf:
            self._send_json({"erro": "O estado nao pode ficar vazio."}, status=400)
            return

        main_py = os.path.join(PASTA_PROJETO, "main.py")
        if not os.path.isfile(main_py):
            self._send_json(
                {"erro": f"Nao foi possivel encontrar main.py em: {PASTA_PROJETO}"},
                status=500,
            )
            return

        threading.Thread(
            target=_executar_buscas,
            args=(categorias, cidade, uf, quantidade),
            daemon=True,
        ).start()
        self._send_json({"ok": True})


def main() -> None:
    if not os.path.isdir(WEB_DIR):
        print(f"[ERRO] Pasta 'web' nao encontrada em: {WEB_DIR}")
        print("Certifique-se de manter a pasta 'web' junto com server.py.")
        input("Pressione Enter para sair...")
        sys.exit(1)

    servidor = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print("============================================")
    print("  GBP Lead Finder - Interface Web")
    print("============================================")
    print(f"Servidor rodando em {url}")
    print("Feche esta janela ou pressione Ctrl+C para parar.")

    threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.shutdown()


if __name__ == "__main__":
    main()
