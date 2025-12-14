import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import pytest

def test_root_serves_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_create_tweet_success(client):
    payload = {"tweet_data": "hello from test", "tweet_media_ids": []}
    headers = {"api-key": "valid"}
    r = client.post("/api/tweets", json=payload, headers=headers)
    assert r.status_code == 201
    j = r.json()
    assert j.get("result") is True
    assert isinstance(j.get("tweet_id"), int)


def test_create_tweet_unauthorized(client):
    payload = {"tweet_data": "should fail", "tweet_media_ids": []}
    headers = {"api-key": "invalid"}
    r = client.post("/api/tweets", json=payload, headers=headers)
    assert r.status_code == 401


def test_get_existing_media(client):

    r = client.get("/api/medias/1")
    assert r.status_code == 200
    assert r.content == b"jpegbytes"
    assert "image" in r.headers.get("content-type", "")


def test_get_media_not_found_raises(client):
    with pytest.raises(Exception):
        client.get("/api/medias/999")


def test_upload_media_and_retrieve(client):
    files = {"file": ("img.jpg", b"myjpegdata", "image/jpeg")}
    r = client.post("/api/medias", files=files)
    assert r.status_code in (200, 201)
    j = r.json()
    assert j.get("result") is True
    media_id = j.get("media_id")
    assert isinstance(media_id, int)

    # retrieve
    r2 = client.get(f"/api/medias/{media_id}")
    assert r2.status_code == 200
    assert r2.content == b"myjpegdata"


def test_delete_tweet_flow(client):
    headers_valid = {"api-key": "valid"}
    headers_invalid = {"api-key": "invalid"}

    payload = {"tweet_data": "to delete", "tweet_media_ids": []}
    r_create = client.post("/api/tweets", json=payload, headers=headers_valid)
    assert r_create.status_code == 201
    tid = r_create.json()["tweet_id"]

    r_unauth = client.delete(f"/api/tweets/{tid}", headers=headers_invalid)
    assert r_unauth.status_code == 401

    r = client.delete(f"/api/tweets/{tid}", headers=headers_valid)
    assert r.status_code == 200
    assert r.json().get("result") is True

    r2 = client.delete(f"/api/tweets/{99999}", headers=headers_valid)
    assert r2.status_code == 404


def test_like_and_delete_like_flow(client, setup_test_db):
    headers = {"api-key": "valid"}

    r_create = client.post("/api/tweets", json={"tweet_data": "for like", "tweet_media_ids": []}, headers=headers)
    assert r_create.status_code == 201
    tid = r_create.json()["tweet_id"]

    r = client.post(f"/api/tweets/{tid}/likes", headers=headers)
    assert r.status_code == 200
    assert r.json().get("result") is True

    r2 = client.post("/api/tweets/99999/likes", headers=headers)
    assert r2.status_code == 404

    session_maker = setup_test_db["session_maker"]

    async def insert_like():
        from database import Like
        async with session_maker() as s:
            async with s.begin():
                s.add(Like(user_id=1, tweet_id=tid))
    asyncio.run(insert_like())


    r3 = client.delete(f"/api/tweets/{tid}/likes", headers=headers)
    assert r3.status_code == 200
    assert r3.json().get("result") is True

    r4 = client.delete("/api/tweets/99999/likes", headers=headers)
    assert r4.status_code == 404


def test_follow_and_unfollow_flow(client, setup_test_db):
    headers = {"api-key": "valid"}
    session_maker = setup_test_db["session_maker"]

    async def create_user(uid=2, name="other"):
        from database import Users
        async with session_maker() as s:
            async with s.begin():
                s.add(Users(id=uid, name=name, api_key=f"key{uid}"))

    asyncio.run(create_user(2, "other"))

    r = client.post("/api/users/2/follow", headers=headers)
    assert r.status_code == 200
    assert r.json().get("result") is True


    r_self = client.post("/api/users/1/follow", headers=headers)
    assert r_self.status_code == 404

    r3 = client.delete("/api/users/2/follow", headers=headers)
    assert r3.status_code == 200
    assert r3.json().get("result") is True

    r4 = client.delete("/api/users/2/follow", headers=headers)
    assert r4.status_code == 404


def test_get_my_profile_and_user_info(client):
    headers = {"api-key": "valid"}
    r = client.get("/api/users/me", headers=headers)
    assert r.status_code == 200
    j = r.json()
    assert "user" in j
    assert j["user"]["id"] == 1
    assert "followers" in j["user"]
    assert "following" in j["user"]

    # /api/users/{user_id}
    r2 = client.get("/api/users/1")
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["user"]["id"] == 1

    r3 = client.get("/api/users/99999")
    assert r3.status_code == 404





def test_get_tweets_route_exists_replace_endpoint(monkeypatch, client):
    import app as app_module

    async def fake_get_tweets(api_key: str = None):
        return {"result": True, "tweets": []}


    for route in list(app_module.app.router.routes):
        if getattr(route, "path", None) == "/api/tweets" and "GET" in getattr(route, "methods", {}):
            app_module.app.router.routes.remove(route)
            app_module.app.add_api_route("/api/tweets", fake_get_tweets, methods=["GET"])
            break

    headers = {"api-key": "valid"}
    r = client.get("/api/tweets", headers=headers)
    assert r.status_code == 200
    j = r.json()
    assert j.get("result") is True
    assert isinstance(j.get("tweets"), list)