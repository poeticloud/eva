import asyncio
import subprocess

import typer
from tortoise import Tortoise, transactions

from app.core import config
from app.models import Credential, Identity, Password

cmd = typer.Typer()


@cmd.command(help="create identity")
def create_identity(email: str, password: str):
    async def do():
        await Tortoise.init(config=config.db_config)
        async with transactions.in_transaction() as tx:
            if await Credential.filter(identifier_type=Credential.IdentifierType.EMAIL, identifier=email).exists():
                await tx.rollback()
                return typer.secho(f"credential with {email=} already exists", fg=typer.colors.RED)

            identity = Identity()
            await identity.save()
            credential = Credential(
                identity=identity, identifier_type=Credential.IdentifierType.EMAIL, identifier=email
            )
            await credential.save()
            await Password.from_raw(credential=credential, raw_password=password).save()
            typer.secho(f"identity created successfully! uuid: {identity.uuid}", fg=typer.colors.GREEN)

    asyncio.get_event_loop().run_until_complete(do())


@cmd.command(help="start pgcli")
def dbshell():
    subprocess.call(["pgcli", config.settings.postgres_dsn])


@cmd.command()
def init_db():
    print("do something")


if __name__ == "__main__":
    cmd()