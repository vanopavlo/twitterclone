from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Header, HTTPException, Path, UploadFile, Depends
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import (Base, Follow, Like, Media, Tweet, Users, engine,
                      get_user_by_api_key, session, TweetIN, get_session)



@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await session.close()
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title="API Твитер",
    description="API для клона Твитера",
    version="1.0.0",
)

@app.get(
    "/",
    summary="Главная страница",
    description="Возвращает HTML-страницу с клиентским интерфейсом приложения.",
    tags=["Frontend"],
    response_description="HTML страница главного интерфейса",
) #11
async def root():
    return FileResponse("templates/index.html")





@app.post(
    "/api/tweets",
    summary="Создать твит",
    description=(
        "Создает новый твит от имени авторизованного пользователя. "
        "Тело запроса содержит текст твита и, при необходимости, список ID медиа-файлов."
    ),
    tags=["Tweets"],
    response_description="Результат создания твита и его идентификатор",
    status_code=201,
)
async def create_tweet(
    tweet: TweetIN,
    api_key: str = Header(...),
):

    user = await get_user_by_api_key(api_key=api_key, session=session)

    new_post = Tweet(
        user_id=user.id,
        tweet_data=tweet.tweet_data,  # ✅ Доступ через .
        tweet_media_ids=tweet.tweet_media_ids,  # ✅ Доступ через .
    )

    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return {"result": True, "tweet_id": new_post.id}


@app.get(
    "/api/medias/{media_id}",
    summary="Получить медиа-файл",
    description="Возвращает бинарное содержимое медиа-файла по его ID.",
    tags=["Media"],
    response_description="Бинарные данные медиа-файла",
)
async def get_media(media_id: int):
    media = await session.get(Media, media_id)
    return Response(
        content=media.file,  # bytes из LargeBinary
        media_type="image/jpeg"  # или media.mime_type
    )



@app.post(
    "/api/medias",
    summary="Загрузить медиа-файл",
    description="Принимает файл и сохраняет его в базе как медиа-объект.",
    tags=["Media"],
    response_description="Результат операции и ID загруженного медиа-файла",
    status_code=201,
)
async def upload_media(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    print(file)
    content = await file.read()
    media = Media(file=content)
    session.add(media)
    await session.flush()
    return {"result": True, "media_id": media.id}


@app.delete(
    "/api/tweets/{tweet_id}",
    summary="Удалить твит",
    description="Удаляет твит по его ID, если пользователь авторизован и является владельцем твита.",
    tags=["Tweets"],
    response_description="Результат удаления",
    status_code=200,
) #!!
async def delete_tweet(
    tweet_id: int = Path(..., title="ID твита для удаления"),
    api_key: str = Header(..., description="API ключ авторизованного пользователя"),
) -> dict:


    user = await get_user_by_api_key(api_key, session)

    tweet = (
        await session.execute(
            select(Tweet)
            .join(Users, Tweet.user_id == Users.id)
            .where((Tweet.id == tweet_id) & (Users.id == user.id))
        )
    ).scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.tweet_media_ids:
        await session.execute(
            delete(Media).where(Media.id.in_(tweet.tweet_media_ids))
        )
    await session.delete(tweet)
    await session.commit()
    return {"result": True}


@app.post(
    "/api/tweets/{tweet_id}/likes",
    summary="Поставить лайк твиту",
    description="Добавляет лайк к твиту от авторизованного пользователя.",
    tags=["Tweets"],
    response_description="Результат операции",
    status_code=200
) #!!
async def like_tweet(
    api_key: str = Header(..., description="API ключ авторизованного пользователя"),
    tweet_id: int = Path(..., title="ID твита для лайка"),
) -> dict:


    await get_user_by_api_key(api_key, session)
    tweet = (
        await session.execute(select(Tweet).where(Tweet.id==tweet_id))
    ).scalar_one_or_none()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # session.add(Like(user_id=user.id, tweet_id=tweet_id))
    # await session.commit()

    return {"result": True}


@app.delete(
    "/api/tweets/{tweet_id}/likes",
    summary="Удалить лайк твита",
    description="Удаляет лайк пользователя с указанного твита.",
    tags=["Tweets"],
    response_description="Результат операции",
    status_code=200,
) #!!!
async def delete_like_tweet(
    api_key: str = Header(..., description="API ключ авторизованного пользователя"),
    tweet_id: int = Path(..., title="ID твита для удаления лайка"),
) -> dict:
    user = await get_user_by_api_key(api_key, session)
    like = (
        await session.execute(
            select(Like).where((tweet_id == Like.tweet_id) & (Like.user_id == user.id))
        )
    ).scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    await session.delete(like)
    await session.commit()

    return {"result": True}


@app.post(
    "/api/users/{follow_id}/follow",
    summary="Подписаться на пользователя",
    description="Добавляет подписку текущего пользователя на другого по ID.",
    tags=["Users"],
    response_description="Результат операции",
    status_code=200,
)
async def follow_user(
    api_key: str = Header(..., description="API ключ авторизованного пользователя"),
    follow_id: int = Path(..., title="ID пользователя для подписки"),
) -> dict:
    user = await get_user_by_api_key(api_key, session)

    following = (
        await session.execute(select(Users).where(Users.id == follow_id))
    ).scalar_one_or_none()
    if not following:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == following.id:
        raise HTTPException(status_code=404, detail="You can't subscribe to yourself")
    try:
        session.add(Follow(follower_id=user.id, following_id=following.id))
        await session.commit()
    except IntegrityError:
        raise HTTPException(status_code=404, detail="You are already follow user")
    return {"result": True}



@app.get(
    "/api/tweets",
    summary="Получить список твитов",
    description=(
        "Возвращает список твитов с информацией об авторе, прикреплённых медиа "
        "и пользователях, поставивших лайк. Результат отсортирован по количеству лайков."
    ),
    tags=["Tweets"],
    response_description="Список твитов с метаданными",
)
async def get_tweets(api_key: str = Header(...)) -> dict:
    await get_user_by_api_key(api_key, session)

    tweets_data = await session.execute(
        select(
            Tweet.id, Tweet.tweet_data, func.array_agg(Media.id).label("attachments"),
            Users.id.label("user_id"), Users.name.label("user_name")
        )
        .select_from(Tweet)
        .outerjoin(Media, Tweet.tweet_media_ids.any(Media.id))
        .join(Users, Tweet.user_id == Users.id)
        .group_by(Tweet.id, Tweet.tweet_data, Users.id, Users.name)
    )

    likes_data = await session.execute(
        select(Like.tweet_id, Like.user_id, Users.name).join(Users, Like.user_id == Users.id)
    )

    tweet_likes = defaultdict(list)
    for tweet_id, user_id, user_name in likes_data:
        tweet_likes[tweet_id].append({"user_id": user_id, "name": user_name})

    tweets_list = []
    for tweet_id, content, attachments, user_id, user_name in tweets_data:
        print(tweet_likes[tweet_id])
        tweets_list.append({
            "id": tweet_id, "content": content,
            "attachments": None if attachments == [None] else [f"/api/medias/{media_id}" for media_id in attachments],
            "author": {"id": user_id, "name": user_name},
            "likes": tweet_likes[tweet_id],
        })

    tweets_list.sort(key=lambda t: len(tweet_likes[t["id"]]), reverse=True)

    return {"result": True, "tweets": tweets_list}

@app.delete(
    "/api/users/{follow_id}/follow",
    summary="Отписаться от пользователя",
    description="Удаляет подписку текущего пользователя с другого пользователя.",
    tags=["Users"],
    response_description="Результат операции",
    status_code=200,
)
async def unfollow_user(
    api_key: str = Header(..., description="API ключ авторизованного пользователя"),
    follow_id: int = Path(..., title="ID пользователя для отписки"),
) -> dict:


    user = await get_user_by_api_key(api_key, session)

    follow = (
        await session.execute(
            select(Follow).where(
                (user.id == Follow.follower_id) & (follow_id == Follow.following_id)
            )
        )
    ).scalar_one_or_none()

    if not follow:
        raise HTTPException(
            status_code=404, detail="You are not subscribed to the user"
        )

    await session.delete(follow)
    await session.commit()
    return {"result": True}


@app.get(
    "/api/users/me",
    summary="Получить профиль текущего пользователя",
    description="Возвращает информацию о пользователе, его подписчиках и на кого он подписан.",
    tags=["Users"],
    response_description="Профиль пользователя",
    status_code=200,
)
async def get_my_profile(
    api_key: str = Header(..., description="API ключ авторизованного пользователя")
) -> dict:

    user = await get_user_by_api_key(api_key, session)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    followers_query = (
        select(Users)
        .join(Follow, Users.id == Follow.following_id)
        .where(Follow.follower_id == user.id)
    )
    followers_result = await session.execute(followers_query)
    followers = [{"id": u.id, "name": u.name} for u in followers_result.scalars().all()]

    following_query = (
        select(Users)
        .join(Follow, Users.id == Follow.follower_id)
        .where(Follow.following_id == user.id)
    )
    following_result = await session.execute(following_query)
    following = [{"id": u.id, "name": u.name} for u in following_result.scalars().all()]

    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": followers,
            "following": following,
        },
    }


@app.get(
    "/api/users/{user_id}",
    summary="Получить информацию о пользователе",
    description="Возвращает данные пользователя с подписчиками и подписками по ID пользователя.",
    tags=["Users"],
    response_description="Профиль пользователя",
    status_code=200,
)
async def get_user_info(user_id: int = Path(..., title="ID пользователя")) -> dict:
    user = (
        await session.execute(select(Users).where(Users.id== user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    followers_query = (
        select(Users)
        .join(Follow, Users.id == Follow.following_id)
        .where(Follow.follower_id == user_id)
    )
    followers_result = await session.execute(followers_query)
    followers = [{"id": u.id, "name": u.name} for u in followers_result.scalars().all()]

    following_query = (
        select(Users)
        .join(Follow, Follow.follower_id == Users.id)
        .where(Follow.following_id == user_id)
    )
    following_result = await session.execute(following_query)
    following = [{"id": u.id, "name": u.name} for u in following_result.scalars().all()]

    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": followers,
            "following": following,
        },
    }



app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/css", StaticFiles(directory="static/css"), name="css")     # ← ДОБАВИТЕ
app.mount("/js", StaticFiles(directory="static/js"), name="js")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
