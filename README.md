# TwitterClone — клонированный API Твиттера (FastAPI)

Учебный проект на FastAPI + SQLAlchemy (async) — минимальный API-клон Твиттера:
создание твитов, загрузка медиа, лайки, подписки, получение профиля и ленты.

> В проекте используются асинхронные SQLAlchemy-модели (create_async_engine, AsyncSession)
> и Pydantic-схемы для входных данных.

## Описание
Проект реализует следующие возможности:
- Создание твитов (текст + список id медиа)
- Загрузка и отдача бинарных медиа-файлов
- Удаление твитов (только владельцем)
- Поставить/удалить лайк
- Подписаться/отписаться от пользователя
- Получение списка твитов (агрегация вложений и лайков)
- Получение профиля текущего пользователя и профиля по id
- Отдача статических файлов и index.html в корне

---

## Установка и настройка

1. **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/vanopavlo/twitterclone
    ```

2. **Создайте файл `.env` со следующей структурой:**

    ```env
    ENGINE=postgresql+asyncpg://username:password@0.0.0.0/db_name
    ```

3. **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Запустите приложение:**

    ```bash
    docker compose up
    ```

---


   По умолчанию приложение слушает `http://localhost:8000`. Главная страница — `/` (сервирует `templates/index.html`).

## Переменные окружения
Проект использует `.env` (через python-dotenv в моделях). Основная переменная:

- `ENGINE` — SQLAlchemy URL для подключения к БД.
  - Пример для SQLite-файла:
    sqlite+aiosqlite:///./data.db
  - Пример для PostgreSQL:
    postgresql+asyncpg://user:pass@localhost:5432/dbname

При тестах мы используем temporary SQLite-файл (см. tests/conftest.py).

## База данных
Модели находятся в `database/models.py`. Перед запуском приложение при старте выполнит:
`Base.metadata.create_all` (через lifespan) — создаст таблицы, если их нет.

Примечание: модели используют `ARRAY(Integer)` для `tweet_media_ids` (Postgres). Для локального тестирования в SQLite проект в тестах подменяет этот тип на JSON. В продакшн рекомендуется использовать PostgreSQL.

## Тестирование
- Установите dev-зависимости (pytest, httpx, aiosqlite и др.):
  pip install -r requirements.txt  # если в requirements уже есть тестовые пакеты
  pip install pytest httpx aiosqlite

- Запуск тестов:
  pytest -q

В репозитории есть fixtures для создания временной тестовой БД (sqlite+aiosqlite) и client (TestClient). Тесты покрывают основные эндпоинты. Если вы запускаете тесты локально и хотите использовать Postgres, настройте соответствующий ENGINE и/или CI.

## Эндпоинты и примеры использования

Все запросы, требующие аутентификации, используют заголовок `api_key` в сигнатуре функции, поэтому в HTTP надо передавать заголовок с дефисом: `api-key: <value>`. Примеры ниже используют `api-key: valid` (в тестовой БД создаётся пользователь с api_key='valid').

1. GET /
   - Описание: отдаёт `templates/index.html`
   - Пример:
     curl http://localhost:8000/

2. POST /api/tweets
   - Создать твит
   - Тело (JSON): `{ "tweet_data": "текст", "tweet_media_ids": [1,2] }`
   - Заголовок: `api-key: <your_api_key>`
   - Пример:
     curl -X POST http://localhost:8000/api/tweets -H "api-key: valid" -H "Content-Type: application/json" -d '{"tweet_data":"hi","tweet_media_ids":[]}'

3. GET /api/medias/{media_id}
   - Отдать бинарное содержимое медиа
   - Пример:
     curl http://localhost:8000/api/medias/1 --output media.jpg

4. POST /api/medias
   - Загрузить медиа (multipart/form-data)
   - Пример:
     curl -X POST http://localhost:8000/api/medias -F "file=@./img.jpg"

5. DELETE /api/tweets/{tweet_id}
   - Удалить твит (доступен только владельцу)
   - Пример:
     curl -X DELETE http://localhost:8000/api/tweets/1 -H "api-key: valid"

6. POST /api/tweets/{tweet_id}/likes
   - Поставить лайк
   - Пример:
     curl -X POST http://localhost:8000/api/tweets/1/likes -H "api-key: valid"

7. DELETE /api/tweets/{tweet_id}/likes
   - Удалить лайк
   - Пример:
     curl -X DELETE http://localhost:8000/api/tweets/1/likes -H "api-key: valid"

8. POST /api/users/{follow_id}/follow
   - Подписаться на пользователя
   - Пример:
     curl -X POST http://localhost:8000/api/users/2/follow -H "api-key: valid"

9. DELETE /api/users/{follow_id}/follow
   - Отписаться
   - Пример:
     curl -X DELETE http://localhost:8000/api/users/2/follow -H "api-key: valid"

10. GET /api/tweets
    - Получить список твитов (агрегация вложений/лайков)
    - Пример:
      curl http://localhost:8000/api/tweets -H "api-key: valid"

11. GET /api/users/me
    - Профиль текущего пользователя (followers, following)
    - Пример:
      curl http://localhost:8000/api/users/me -H "api-key: valid"

12. GET /api/users/{user_id}
    - Профиль по id
    - Пример:
      curl http://localhost:8000/api/users/1

Статические файлы:
- `/static`, `/css`, `/js` — монтируются через StaticFiles и отдают содержимое папки `static/`.

## Особенности и ограничения
- Модели используют Postgres-специфичные типы/функции (ARRAY, array_agg, .any). Для корректной работы всех агрегатов и запросов рекомендуется использовать PostgreSQL.
- Текущая тестовая конфигурация подменяет некоторые вещи для работы на SQLite (в тестах происходит замена типа `ARRAY` на JSON и т.д.).
- Аутентификация реализована очень просто (api_key в заголовке). Для реального приложения нужно добавить безопасную авторизацию (OAuth2/JWT), хранение секретов и ротацию ключей.

## Развёртывание
- В production рекомендую использовать PostgreSQL и uvicorn/gunicorn с workers (uvicorn workers через gunicorn/uvicorn worker).
- Подготовьте переменные окружения (ENGINE) и используйте миграции (alembic) — в текущем проекте миграции не настроены, но можно добавить Alembic для контроля схемы.

## Вклад
Пулл-реквесты и баг-репорты приветствуются. Для крупных изменений:
- Откройте issue с описанием
- Сделайте ветку feature/... и pull request
- Добавьте/обновите тесты

## Лицензия
Добавьте подходящую лицензию в репозиторий (например, MIT) или укажите текущую. Сейчас лицензия не указана.

---

Если хотите, я могу:
- добавить docker-compose с сервисом Postgres и настройкой для локального удобного запуска;
- настроить Alembic для миграций;
- улучшить README (добавить ER-диаграмму/пример данных) — скажите, что предпочитаете.
