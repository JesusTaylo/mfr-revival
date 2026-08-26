#!/usr/bin/env python3
"""
fake_gmc2.py  --  MFR Revival · Milestone 1

Servidor GMC2 FALSO + registrador de peticiones para Marvel Future Revolution.

Que hace:
  1. Escucha HTTP y RESPONDE a cualquier ruta con una config GMC2 "best-guess"
     (reconstruida del binario del cliente -- ver server/notes-protocol.md).
  2. Y lo mas importante: IMPRIME cada peticion que recibe (metodo, ruta, query,
     headers, body). Cuando apuntes el cliente real hacia aca, estos logs te dicen
     EXACTAMENTE que pide -- y con eso vamos afinando la respuesta.

Uso:
    python fake_gmc2.py                 # escucha en 0.0.0.0:8080
    python fake_gmc2.py --port 8080 --gateway http://192.168.1.50:9000

Requisitos: solo Python 3 (libreria estandar, sin dependencias).

OJO: los valores marcados con  # GUESS  son suposiciones a partir de los strings
del cliente; se ajustan viendo los logs cuando conectes el juego.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

# La URL del "gateway" que le devolvemos al cliente. El cliente luego intenta
# conectarse a  <GATEWAY>/sessions?gameCode=...&tls=true  (servidor de sesion).
# Cambia esto por la IP:puerto de TU maquina donde correra el session server.
GATEWAY_URL = "http://127.0.0.1:9000"   # <-- EDITAR con tu IP local


def gmc2_config(gateway_url: str) -> dict:
    """
    Config GMC2 reconstruida a partir de las claves halladas en classes.dex:
      gatewayUrl / IAPGatewayUrl, gmc2Key/gmc2Boolean, iapKey/iapIv,
      review_info_url / review_url, GMC2_AGREEMENT_URL / GMC2_TERMS_URL,
      useDim / strokeColor / useTitleBar, patron de worldID.

    La ESTRUCTURA del envelope (errorCode/data) es una GUESS del patron tipico
    de Netmarble; se corrige con los logs del cliente real.
    """
    return {
        "errorCode": 0,                    # GUESS: 0 = exito
        "errorMessage": "Success",         # GUESS
        "data": {
            "gatewayUrl": gateway_url,     # <- lo que de verdad importa
            "IAPGatewayUrl": gateway_url,  # GUESS
            "worldIDPattern": "[0-9]{1,10}",  # el cliente exige worldID <= 10 chars
            "gmc2Value": {                 # mapa de config string->string (GUESS)
                "review_info_url": f"{gateway_url}/review/info",
                "review_url": f"{gateway_url}/review",
                "GMC2_AGREEMENT_URL": f"{gateway_url}/agreement",
                "GMC2_TERMS_URL": f"{gateway_url}/terms",
            },
            "gmc2Boolean": {               # config booleans (GUESS)
                "useDim": False,
                "useTitleBar": True,
            },
            "strokeColor": "#000000",      # GUESS
            "iapKey": "0000000000000000",  # GUESS (16) -- placeholder
            "iapIv": "0000000000000000",   # GUESS (16) -- placeholder
        },
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "FakeGMC2/0.1"

    def _log_request(self, body: bytes):
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"\n===== {ts}  {self.command} {self.path} =====")
        for k, v in self.headers.items():
            print(f"  {k}: {v}")
        if body:
            # intenta imprimir como texto; si es binario, muestra hex corto
            try:
                print("  BODY:", body.decode("utf-8"))
            except UnicodeDecodeError:
                print("  BODY(hex):", body[:256].hex())
        print("=" * 50)

    def _respond(self, body: bytes):
        payload = json.dumps(gmc2_config(GATEWAY_URL)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._log_request(b"")
        self._respond(b"")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        self._log_request(body)
        self._respond(body)

    # silenciar el log por defecto (usamos el nuestro)
    def log_message(self, *args):
        pass


def main():
    global GATEWAY_URL
    ap = argparse.ArgumentParser(description="Fake GMC2 server for MFR revival")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--gateway", default=GATEWAY_URL,
                    help="gatewayUrl a devolver (tu IP:puerto del session server)")
    args = ap.parse_args()
    GATEWAY_URL = args.gateway

    print(f"[fake_gmc2] escuchando en http://{args.host}:{args.port}")
    print(f"[fake_gmc2] devolviendo gatewayUrl = {GATEWAY_URL}")
    print("[fake_gmc2] responde a CUALQUIER ruta y registra cada peticion.\n")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
