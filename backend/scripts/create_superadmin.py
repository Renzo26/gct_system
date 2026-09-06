"""Cria (ou promove) um usuário SUPERADMIN do grupo GCT.

Uso:
    python -m scripts.create_superadmin --name "Renzo" --email admin@gct.com --password "senha"

Um SUPERADMIN não pertence a nenhum cliente (workshop_id nulo) e enxerga
todos os clientes cadastrados.
"""
import argparse
import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select  # noqa: E402

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402


async def main(name: str, email: str, password: str) -> int:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            existing.role = UserRole.SUPERADMIN
            existing.workshop_id = None
            existing.is_active = True
            existing.password_hash = hash_password(password)
            await db.commit()
            print(f"Usuário {email} promovido a SUPERADMIN.")
            return 0

        user = User(
            workshop_id=None,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.SUPERADMIN,
        )
        db.add(user)
        await db.commit()
        print(f"SUPERADMIN {email} criado.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.name, args.email, args.password)))
