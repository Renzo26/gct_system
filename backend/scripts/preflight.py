"""Valida a configuração antes de subir a API.

Roda antes do alembic/uvicorn para transformar falhas de deploy (variável
ausente, credencial errada, banco inacessível) em mensagens legíveis no log,
em vez de um stack trace de dezenas de linhas.
"""
import asyncio
import os
import ssl
import sys
from urllib.parse import urlsplit

OBRIGATORIAS = [
    "DATABASE_URL",
    "WAHA_BASE_URL",
    "WAHA_API_KEY",
    "REDIS_URL",
    "JWT_SECRET",
]

PLACEHOLDERS = ("PROJETO", "SENHA", "SEU_", "SUA_", "sua-chave", "troque", "example")


def mascarar(url: str) -> str:
    try:
        p = urlsplit(url)
        user = (p.username or "?")
        return f"{p.scheme}://{user}:***@{p.hostname}:{p.port or '?'}{p.path}"
    except Exception:
        return "<ilegivel>"


async def testar_banco(url: str) -> None:
    import asyncpg

    dsn = url.replace("postgresql+asyncpg://", "postgresql://")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncio.wait_for(asyncpg.connect(dsn, ssl=ctx), timeout=20)
    versao = await conn.fetchval("select version()")
    await conn.close()
    print(f"[preflight] banco OK: {versao[:40]}", flush=True)


def main() -> int:
    print("[preflight] verificando configuracao...", flush=True)

    faltando = [v for v in OBRIGATORIAS if not os.environ.get(v, "").strip()]
    if faltando:
        print(f"[preflight] ERRO: variaveis ausentes ou vazias: {', '.join(faltando)}", flush=True)
        print("[preflight] Preencha-as em 'Variaveis de Ambiente' no EasyPanel, "
              "salve e implante novamente.", flush=True)
        return 1

    db = os.environ["DATABASE_URL"]
    print(f"[preflight] DATABASE_URL = {mascarar(db)}", flush=True)
    print(f"[preflight] CORS_ORIGINS = {os.environ.get('CORS_ORIGINS', '(vazio)')}", flush=True)

    suspeitas = [p for p in PLACEHOLDERS if p in db]
    if suspeitas:
        print(f"[preflight] ERRO: DATABASE_URL ainda contem valor de exemplo ({suspeitas[0]}).", flush=True)
        print("[preflight] O conteudo colado veio do .env.example, nao das credenciais reais.", flush=True)
        return 1

    try:
        asyncio.run(testar_banco(db))
    except asyncio.TimeoutError:
        print("[preflight] ERRO: timeout conectando no banco. Verifique host/porta "
              "(use o Session Pooler do Supabase, porta 5432).", flush=True)
        return 1
    except Exception as e:
        print(f"[preflight] ERRO conectando no banco: {type(e).__name__}: {e}", flush=True)
        return 1

    print("[preflight] tudo certo, iniciando migrations e API.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
