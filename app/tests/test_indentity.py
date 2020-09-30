def test_permission_curd(client):
    resp = client.post(
        "/permission",
        json={"code": "fake_code", "name": "fake_name", "description": "fake description"},
    )
    assert resp.status_code == 200, resp.text
