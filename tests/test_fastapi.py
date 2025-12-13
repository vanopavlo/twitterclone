# import os
# import sys
#
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
#
# def test_test(client):
#     response = client.get("/test")  # ✅ await для async client
#     assert response.status_code == 200
#
#
# def test_get_tweets_with_real_user(client):
#     response = client.get("/api/tweets", headers={"api-key": "test"})
#
#     assert response.status_code == 200
#     data = response.json()
#     assert data["result"] == True
#
#
# def test_create_tweet(client, mock_api):
#     response = client.post(
#         "/api/tweets",
#         json={"tweet_data": "Тест", "tweet_media_ids": []},
#         headers={"api-key": "test"},
#     )
#     assert response.status_code == 201
#
#
# def test_add_photo(client, mock_api):
#
#     files = {"file": ("media.jpg", "image/jpeg")}
#
#     add_response = client.post("/api/medias", files=files, headers={"api-key": "test"})
#     assert add_response.status_code == 201
#
#
# def test_get_photo(client, mock_api):
#     response = client.get("api/media/test.jpg", headers={"api-key": "test"})
#     assert response.status_code == 200
#
#
# # test_fastapi.py
# def test_create_tweet_then_delete(client):
#
#     # POST — использует test_user из БД
#     response = client.post(
#         "/api/tweets",
#         json={"tweet_data": "Тест", "tweet_media_ids": []},
#         headers={"api-key": "test"},  # test_user.api_key!
#     )
#     assert response.status_code == 201
#     tweet_id = response.json()["tweet_id"]
#
#     # DELETE — тоже реальная БД
#     delete_response = client.delete(f"/api/tweets/1", headers={"api-key": "test"})
#     assert delete_response.status_code == 200
