import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import JSON

@pytest.fixture(scope="session")
def tmp_sqlite_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "test_db.sqlite"
    return str(path)

@pytest.fixture(scope="session")
def setup_test_db(tmp_sqlite_path):
    import database
    from database import Base, Users, Tweet, Media

    database_url = f"sqlite+aiosqlite:///{tmp_sqlite_path}"

    test_engine = create_async_engine(database_url, future=True)
    TestSessionMaker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _prepare():


        t = Base.metadata.tables.get("tweets")
        if t is not None and "tweet_media_ids" in t.c:
            col = t.c["tweet_media_ids"]

            col.type = JSON()


        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSessionMaker() as s:
            async with s.begin():
                user = Users(id=1, name="name", api_key="valid")
                s.add(user)
                tweet = Tweet(user_id=1, tweet_data="existing", tweet_media_ids=[])
                s.add(tweet)
                media = Media(file=b"jpegbytes")
                s.add(media)

    asyncio.run(_prepare())

    test_session_instance = TestSessionMaker()


    keys = ("engine", "async_session", "async_sessionmaker", "session", "get_session")
    originals = {k: getattr(database, k, None) for k in keys}


    setattr(database, "engine", test_engine)
    setattr(database, "async_session", TestSessionMaker)

    setattr(database, "async_sessionmaker", TestSessionMaker)

    setattr(database, "session", test_session_instance)

    async def get_session_override():
        async with TestSessionMaker() as s:
            try:
                yield s
                await s.commit()
            except:
                await s.rollback()
                raise

    setattr(database, "get_session", get_session_override)

    yield {
        "engine": test_engine,
        "session_maker": TestSessionMaker,
        "db_file": tmp_sqlite_path,
    }


    asyncio.run(test_engine.dispose())

    for k, orig in originals.items():
        if orig is None:
            if hasattr(database, k):
                try:
                    delattr(database, k)
                except Exception:
                    pass
        else:
            setattr(database, k, orig)

    try:
        os.remove(tmp_sqlite_path)
    except Exception:
        pass


@pytest.fixture
def client(setup_test_db):
    from app import app

    with TestClient(app) as client:
        yield client


