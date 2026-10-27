# Лабораторная работа №5 — PostgreSQL, миграции, Docker Compose

Тема: система бронирования номеров в городских отелях. Продолжение ветки lab_4.

## Запуск (PowerShell)

```powershell
Copy-Item .env.example .env
# Откройте .env и замените DB_PASSWORD на свой пароль из латинских букв и цифр.
docker compose up --build -d
docker compose ps -a
curl.exe -i http://127.0.0.1:8085/health
```

На этом компьютере рабочий .env уже подготовлен. В Git попадает только шаблон.
По умолчанию HTTP доступен на 8085, PostgreSQL на 5435; внутри сети Docker используются db:5432 и app:8080.
Пароль migrate подставляется в URL, поэтому в учебном .env используйте буквы и цифры. Для приложения драйвер корректно экранирует пароль.

## Проверка всех требований

```powershell
python scripts/verify_lab5.py
```

Сценарий проверяет схему, версию миграции, HTTP 200/503/200, ограничения,
сохранение строки после удаления и пересоздания контейнеров, down/up и повторный up,
отказ при пустом пароле и повторные попытки подключения. Он на время останавливает
только базу этого Compose-проекта. Откат выполняется в отдельной временной БД.
Результаты сохраняются в docs/evidence/lab5.json.

## Полезные команды

```powershell
docker compose logs app migrate
docker compose exec db psql -U hotel_app -d hotels -c "\dt"
docker compose exec db psql -U hotel_app -d hotels -c "SELECT version, dirty FROM schema_migrations;"
docker compose stop db
curl.exe -i http://127.0.0.1:8085/health
docker compose start db
docker compose down
```

Обычный down сохраняет том. down -v удаляет данные, для демонстрации он не нужен.
Команды migrate up/down используют параметры из entrypoint, поэтому достаточно
`docker compose run --rm migrate up`. Откат основной БД удаляет таблицы:
для сдачи используйте безопасный сценарий выше.

## Что читать

- [Понятное объяснение и ответы на вопросы](docs/DEFENSE.md)
- [Отчёт](docs/REPORT.md)
- [Архитектура и решения по данным](ARCHITECTURE.md)
- [Миграция](migrations/000001_init_schema.up.sql)

Область реализации ЛР5: подключение PostgreSQL и /health.
OpenAPI из ЛР2 содержит проект будущего API; остальные описанные операции пока
не являются реализованными HTTP-маршрутами. Redis на этой стадии не требуется.
