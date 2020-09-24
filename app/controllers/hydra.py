from typing import List

from fastapi import APIRouter, Depends, Form
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from app.models import Credential
from app.utils.hydra_cli import HydraClient, hydra_client

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/auth/login")
async def login(request: Request, login_challenge: str, hydra_cli: HydraClient = Depends(hydra_client)):
    get_login_resp = await hydra_cli.get_login_request(challenge=login_challenge)
    # If hydra was already able to authenticate the user, skip will be true and we do not need to re-authenticate
    # the user.
    if get_login_resp["skip"]:
        accept_login_resp = await hydra_cli.accept_login_request(
            challenge=login_challenge,
            subject=get_login_resp["subject"],
        )
        return RedirectResponse(accept_login_resp["redirect_to"], status_code=302)

    return templates.TemplateResponse("login.html", context={"challenge": login_challenge, "request": request})


@router.post("/auth/login")
async def accept_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    challenge: str = Form(...),
    hydra_cli: HydraClient = Depends(hydra_client),
):  # pylint: disable=too-many-arguments
    credential = await Credential.filter(identifier_type=Credential.IdentifierType.EMAIL, identifier=email).first()
    if not credential:
        return templates.TemplateResponse(
            "login.html",
            context={
                "request": request,
                "challenge": challenge,
                "error": "The email / password combination is not correct",
            },
        )
    succeed = True
    async for pwd in credential.passwords:
        if pwd.validate_password(password):
            succeed = True
            break
    if not succeed:
        return templates.TemplateResponse(
            "login.html",
            context={
                "challenge": challenge,
                "error": "The email / password combination is not correct",
                "request": request,
            },
        )

    resp = await hydra_cli.accept_login_request(
        challenge=challenge, subject="1@2.com", remember=remember, remember_for=3600
    )
    print(resp)
    return RedirectResponse(resp["redirect_to"])


@router.get("/auth/consent")
async def consent(request: Request, consent_challenge: str, hydra_cli: HydraClient = Depends(hydra_client)):
    resp = await hydra_cli.get_consent_request(challenge=consent_challenge)
    if resp["skip"]:
        grant_scope = resp["requested_scope"]
        grant_access_token_audience = resp["requested_access_token_audience"]
        print(resp)
        resp = await hydra_cli.accept_consent_request(
            challenge=consent_challenge,
            grant_scope=grant_scope,
            grant_access_token_audience=grant_access_token_audience,
        )
        return RedirectResponse(resp["redirect_to"])
    return templates.TemplateResponse(
        "consent.html",
        context={
            "request": request,
            "user": resp["subject"],
            "client": resp["client"],
            "challenge": consent_challenge,
            "requested_scope": resp["requested_scope"],
        },
    )


@router.post("/auth/consent")
async def accept_consent(
    challenge: str = Form(...),
    grant_scope: List[str] = Form(...),
    remember: bool = Form(...),
    submit: str = Form(False),
    hydra_cli: HydraClient = Depends(hydra_client),
):
    if submit == "Deny access":
        resp = await hydra_cli.reject_consent_request(
            challenge=challenge,
            error="access_denied",
            error_description="The resource owner denied the request",
        )
        return RedirectResponse(resp["redirect_to"])

    resp = await hydra_cli.get_consent_request(challenge=challenge)
    print(resp)
    resp = await hydra_cli.accept_consent_request(
        challenge=challenge,
        grant_scope=grant_scope,
        remember=remember,
        grant_access_token_audience=resp["requested_access_token_audience"],
    )
    print(resp)
    return RedirectResponse(resp["redirect_to"])
