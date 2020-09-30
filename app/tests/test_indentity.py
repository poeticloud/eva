def test_permission_curd(client):
    resp = client.post(
        "/permission", json={"code": "fake_code", "name": "fake_name", "description": "fake description"}
    )
    assert resp.status_code == 200, resp.text
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
    assert resp.status_code == 200

    resp = client.get("/permission/fake_code")
    assert resp.status_code == 404, resp.text
