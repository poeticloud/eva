from datetime import datetime, timedelta
from typing import List

from app.models import Credential, Identity, Password, Permission, Role


async def create_permissions(codes: List[str]):
    permissions = [Permission(name=code, code=code) for code in codes]
    await Permission.bulk_create(permissions)


async def get_role(code):
    return await Role.get_or_none(code=code)


def test_permission_curd(client):
    """测试权限Permission的增删改查操作"""
    resp = client.post(
        "/permission", json={"code": "fake_code", "name": "fake_name", "description": "fake description"}
    )
    assert resp.status_code == 200, resp.text
    resp = client.post(
        "/permission", json={"code": "fake_code", "name": "fake_name", "description": "fake description"}
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["message"] == "provided permission code already exists"
    resp = client.get("/permission")
    assert len(resp.json()["results"]) == 1
    obj = resp.json()["results"][0]
    assert obj["code"] == "fake_code"
    assert obj["name"] == "fake_name"

    resp = client.get("/permission/fake_code")
    assert resp.status_code == 200, resp.text
    obj = resp.json()
    assert obj["code"] == "fake_code"
    assert obj["name"] == "fake_name"
    assert obj["description"] == "fake description"

    resp = client.delete("/permission/fake_code")
    assert resp.status_code == 200, resp.text

    resp = client.get("/permission/fake_code")
    assert resp.status_code == 404, resp.text


def test_update_permission(client, event_loop):
    event_loop.run_until_complete(create_permissions(["fake_code"]))
    resp = client.patch("/permission/fake_code", json={"name": "code_fake", "description": "blabla"})
    assert resp.status_code == 200, resp.text

    async def get_permission(code):
        return await Permission.get_or_none(code=code)

    permission = event_loop.run_until_complete(get_permission("fake_code"))
    assert permission.name == "code_fake"
    assert permission.description == "blabla"


def test_roles(client, event_loop):
    resp = client.post("/role", json={"code": "fake_code", "name": "fake_name", "description": "fake description"})
    assert resp.status_code == 200, resp.text
    resp = client.post("/role", json={"code": "fake_code", "name": "fake_name", "description": "fake description"})
    assert resp.status_code == 400, resp.text
    assert resp.json()["message"] == "provided role code already exists"

    role = event_loop.run_until_complete(get_role("fake_code"))
    assert role.code == "fake_code"
    assert role.name == "fake_name"
    assert role.description == "fake description"

    event_loop.run_until_complete(create_permissions(["code1", "code2"]))
    resp = client.post(
        "/role",
        json={
            "code": "fake_code2",
            "name": "fake_name2",
            "description": "fake description2",
            "permission_codes": ["code1", "code2"],
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/role/fake_code2")
    assert resp.status_code == 200, resp.text
    resp = resp.json()
    assert resp["code"] == "fake_code2"
    assert resp["name"] == "fake_name2"
    assert resp["description"] == "fake description2"
    assert resp["permission_codes"] == ["code1", "code2"]

    resp = client.get("/role")
    assert len(resp.json()["results"]) == 2

    resp = client.delete("/role/fake_code")
    assert resp.status_code == 200

    role = event_loop.run_until_complete(get_role("fake_code"))
    assert role is None
    role = event_loop.run_until_complete(get_role("fake_code2"))
    assert role.code == "fake_code2"


def test_update_role(client, event_loop):
    event_loop.run_until_complete(create_permissions(["code1", "code2"]))
    client.post(
        "/role",
        json={
            "code": "fake_code",
            "name": "fake_name",
            "description": "fake description",
            "permission_codes": ["code1", "code2"],
        },
    )

    resp = client.patch(
        "/role/fake_code",
        json={
            "name": "fake_name2",
            "description": "fake description2",
            "permission_codes": ["code1"],
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/role/fake_code")
    assert resp.status_code == 200, resp.text
    resp = resp.json()
    assert resp["name"] == "fake_name2"
    assert resp["description"] == "fake description2"
    assert resp["permission_codes"] == ["code1"]


def test_identity(client):
    client.post(
        "/role",
        json={
            "code": "fake_code",
            "name": "fake_name",
            "description": "fake description",
        },
    )

    resp = client.post(
        "/identity",
        json={
            "role_codes": ["fake_code"],
            "is_active": True,
            "credentials": [
                {
                    "identifier": "test@123.com",
                    "identifier_type": Credential.IdentifierType.EMAIL.name,
                    "password": "123",
                },
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    resp = client.post(
        "/identity",
        json={
            "role_codes": ["not_exist"],
            "is_active": True,
            "credentials": [
                {
                    "identifier": "test@123.com",
                    "identifier_type": Credential.IdentifierType.EMAIL.name,
                    "password": "123",
                },
            ],
        },
    )
    assert resp.status_code == 400, resp.text

    resp = client.get("/identity")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["results"]) == 1

    uid = resp.json()["results"][0]["uuid"]
    resp = client.get(f"/identity/{uid}")
    assert resp.status_code == 200, resp.text
    resp = resp.json()
    assert resp["credentials"] == [{"identifier": "test@123.com", "identifier_type": "EMAIL"}]
    assert resp["is_active"] is True
    assert resp["roles"] == [{"code": "fake_code", "name": "fake_name"}]

    resp = client.patch(
        f"/identity/{uid}",
        json={
            "is_active": False,
            "credentials": [
                {
                    "identifier": "test",
                    "identifier_type": Credential.IdentifierType.USERNAME.name,
                    "password": "1234",
                },
            ],
            "roles": [],
        },
    )
    assert resp.status_code == 200, resp.text
    resp = resp.json()
    assert resp["is_active"] is False
    assert resp["credentials"] == [{"identifier": "test", "identifier_type": "USERNAME"}]
    assert resp["roles"] == []

    resp = client.delete(f"/identity/{uid}")
    assert resp.status_code == 200, resp.text
    resp = client.get(f"/identity/{uid}")
    assert resp.status_code == 404, resp.text


def test_identity_permissions(event_loop):
    async def test_has_perm():
        perm = Permission(code="perm_code", name="perm_name")
        await perm.save()
        role = Role(code="role_code", name="role_name")
        await role.save()
        await role.permissions.add(perm)
        identity = Identity()
        await identity.save()
        await identity.roles.add(role)
        assert await identity.has_perm("perm_code")
        assert not await identity.has_perm("fake_code")

    event_loop.run_until_complete(test_has_perm())


def test_password(event_loop):
    async def test_pwd():
        pwd = Password.from_raw(None, "1234", permanent=True)
        assert not pwd.is_expired
        pwd.expires_at = datetime.utcnow() - timedelta(days=1)
        assert pwd.is_expired
        assert pwd.validate_password("1234")
        assert not pwd.validate_password("12345")

    event_loop.run_until_complete(test_pwd())
