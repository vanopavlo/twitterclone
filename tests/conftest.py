# import os
# import sys
#
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# from unittest.mock import AsyncMock, MagicMock, patch
#
# import pytest
# from fastapi.testclient import TestClient
#
# from app import app
#
#
# @pytest.fixture
# def client():
#     return TestClient(app)
#
#
# @pytest.fixture
# def mock_api():
#     class MockUser:
#         id = 1
#         name = "test"
#         api_key = "test"
#
#     mock_media = AsyncMock()
#     mock_media.id = 1
#     mock_media.file_path = "media/test.jpg"  # Путь который мы создадим
#
#     with patch("app.get_user_by_api_key") as user_mock:
#         user_mock.return_value = AsyncMock(return_value=MockUser())
#         with patch("app.session.add"), patch("app.session.commit"):
#             with patch("app.session.refresh") as refresh_mock:
#                 refresh_mock.return_value = mock_media
#                 yield mock_media
#

#
# import sys
# import os
#
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# import pytest
# from pytest_postgresql import factories
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.asyncio import create_async_engine
#
# from database import Base, Users,session
# from app import app
#
# # ✅ PostgreSQL fixture (автоматически запускает!)
# postgresql_proc = factories.postgresql_proc()
# postgresql = factories.postgresql("postgresql_proc")
#
#
# @pytest.fixture
# def db_url(postgresql):
#     """URL для asyncpg"""
#     return f"postgresql+asyncpg://{postgresql.info.user}@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
#
#
# @pytest.fixture(scope="function")
# def test_engine(db_url):
#     """Async engine для тестов"""
#     engine = create_async_engine(db_url)
#     yield engine
#     # Автоочистка
#
#
# @pytest.fixture
# def client(test_engine):
#     """TestClient с реальной БД"""
#
#     async def override_get_session():
#         async_session = sessionmaker(test_engine, class_=AsyncSession)()
#         # Добавляем тестового пользователя
#         test_user = Users(name="test_user", api_key="test")
#         async_session.add(test_user)
#         await async_session.commit()
#         yield async_session
#
#     app.dependency_overrides[str] = override_get_session
#     yield TestClient(app)
#     app.dependency_overrides.clear()
