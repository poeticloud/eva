import asyncio
import subprocess

import typer
import uvicorn
from tortoise import Tortoise, transactions

from app.core import config
from app.models import Credential, Identity, Password

cmd = typer.Typer()


@cmd.command(help="run develop server using uvicorn")
def runserver(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    uvicorn.run("app.main:app", reload=reload, host=host, port=port)


@cmd.command(help="generate migration files")
def makemigrations():
    subprocess.call(["aerich", "migrate"])


@cmd.command(help="do database migrate")
def migrate():
    subprocess.call(["aerich", "upgrade"])


@cmd.command(help="update all dependencies' versions and apply in requirements folder")
def update_dep():
    files = [
        "requirements/production.in",
        "requirements/test.in",
        "requirements/dev.in",
    ]
    for file in files:
        subprocess.call(
            [
                "pip-compile",
                file,
                "--no-emit-index-url",
                "-U",
                "-i",
                "https://mirrors.aliyun.com/pypi/simple/",
                "-o",
                file.replace(".in", ".txt"),
            ]
        )


@cmd.command(help="test")
def test():
    subprocess.call(["pytest", "--disable-warnings", "-v", "--cov=./", "--cov-report=xml"])
    subprocess.call(["coverage", "html"])


@cmd.command(help="lint")
def lint():
    subprocess.call(["prospector", "app"])


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


@cmd.command(help="django-like dbshell command use pgcli")
def dbshell():
    subprocess.call(["pgcli", config.settings.postgres_dsn])


@cmd.command(help="django-like shell command use ipython")
def shell():
    try:
        import IPython  # pylint: disable=import-outside-toplevel
        from traitlets.config import Config  # pylint: disable=import-outside-toplevel
    except ImportError:
        return

    models = Tortoise._discover_models("app.models", "models")  # pylint: disable=protected-access
    models_names = ", ".join([model.__name__ for model in models])
    preload_scripts = [
        "from app.main import app",
        "from app.core import config",
        "from tortoise import Tortoise",
        f"from app.models import {models_names}",
        "await Tortoise.init(config=config.db_config)",
    ]
    typer.secho("\n".join(preload_scripts), fg=typer.colors.GREEN)
    c = Config()
    c.PrefilterManager.multi_line_specials = True
    c.InteractiveShell.editor = "vim"
    c.InteractiveShellApp.exec_lines = preload_scripts
    c.TerminalIPythonApp.display_banner = False
    IPython.start_ipython(argv=[], config=c)


if __name__ == "__main__":
    cmd()
