# DailyHit

Ежедневная игра-угадайка песен в стиле Wordle / Spotle.

- [docs/spec.md](docs/spec.md) — техническое задание.
- [docs/decisions.md](docs/decisions.md) — решения по ТЗ. Где они расходятся с ТЗ, действуют решения.

## Состав

| Сервис | Что это | Адрес на хосте |
|---|---|---|
| `db` | PostgreSQL 17 | `127.0.0.1:${POSTGRES_HOST_PORT}` (только в dev) |
| `backend` | Django 5.2 + DRF (`backend/`) | `http://localhost:${BACKEND_HOST_PORT}` |
| `frontend` | React + Vite (`frontend/`) | `http://localhost:${FRONTEND_HOST_PORT}` |

Контейнеры обращаются друг к другу по имени сервиса (`db`, `backend`), а не через `localhost`.
Фронтенд проксирует `/api` в `backend`, поэтому браузер видит API на том же адресе, что и сайт.

## Запуск

Нужен Docker Desktop.

```sh
cp .env.example .env        # заполните пароль БД и DJANGO_SECRET_KEY
docker compose up -d --build
docker compose ps           # db и backend должны быть healthy
```

Если порты 5432, 8000 или 5173 у вас заняты, поменяйте `POSTGRES_HOST_PORT`, `BACKEND_HOST_PORT` или `FRONTEND_HOST_PORT` в `.env`.

Проверка:

- `http://localhost:8000/healthz` отвечает `{"status": "ok", "database": "ok"}`.
- `http://localhost:8000/admin/` открывает админку (путь задаётся в `DJANGO_ADMIN_URL`).

Создать администратора:

```sh
docker compose exec backend python manage.py createsuperuser
```

Загрузить справочники (регионы, страны, языки, жанры, стили, темы, версия игры `world`).
Команду можно запускать повторно: она добавляет недостающее и исправляет изменённое, но ничего не удаляет.

```sh
docker compose exec backend python manage.py seed_reference
```

Для разработки можно загрузить 10 демо-песен со всеми полями и фактами (статус «На проверке»):

```sh
docker compose exec backend python manage.py seed_demo
```

Сами справочники лежат в [backend/apps/catalog/seed/reference.yaml](backend/apps/catalog/seed/reference.yaml).

Язык админки по умолчанию берётся из браузера. Переключатель English / Русский есть справа вверху.

## Разработка

Код `backend/` и `frontend/` подключён в контейнеры, Django и Vite перезагружаются при изменениях.
Миграции применяются автоматически при старте `backend`.

```sh
docker compose exec backend pytest                 # тесты
docker compose exec backend ruff check .           # линтер
docker compose exec backend ruff format .          # форматирование
docker compose exec backend python manage.py makemigrations
docker compose logs -f backend                     # логи
```

Перевод админки на русский:

```sh
docker compose exec backend python manage.py makemessages -l ru --ignore "tests/*" --no-obsolete
# заполнить новые msgstr в backend/locale/ru/LC_MESSAGES/django.po
docker compose exec backend python manage.py compilemessages -l ru
```

Если Vite не замечает изменения файлов, поставьте `VITE_USE_POLLING=true` в `.env`.

После изменения `requirements*.txt` или `package.json` пересоберите образ:

```sh
docker compose up -d --build backend     # или frontend
```

Для фронтенда также удалите анонимный том с `node_modules`: `docker compose rm -sfv frontend`, затем `up -d --build frontend`.

## Данные

База хранится в именованном томе `db_data`. `docker compose down` и пересборка образов её не трогают.

> **Внимание:** `docker compose down -v` удаляет тома, то есть **всю базу**. Перед этим сделайте бэкап.

## Конфигурация

Все настройки задаются переменными окружения, их список с описанием — в [.env.example](.env.example).
`.env` не попадает в git. В репозитории только `.env.example`, без реальных секретов.
