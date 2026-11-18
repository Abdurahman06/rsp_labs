# Лабораторная работа №7 — Service Layer и CRUD REST API

Предметная область: бронирование номеров в городских отелях. Работа продолжает ЛР6, используя ее PostgreSQL, миграцию и репозитории.

## Запуск (PowerShell)

```powershell
Copy-Item .env.example .env
docker compose up --build -d
curl.exe -i http://127.0.0.1:8086/health
python -m unittest tests.test_services -v
```

Локальный `.env` игнорируется Git. Подробный отчет и инструкция демонстрации: `docs/REPORT_LAB7.md`.

## Маршруты

| Метод и путь | Назначение | Успешный ответ |
|---|---|---|
| `POST /api/v1/hotels` | Создать отель | `201` и `Location` |
| `GET /api/v1/hotels?limit=20&offset=0` | Список отелей | `200` |
| `GET /api/v1/hotels/{id}` | Получить отель | `200` |
| `PUT /api/v1/hotels/{id}` | Полностью изменить отель | `200` |
| `DELETE /api/v1/hotels/{id}` | Удалить отель | `204` |
| `POST /api/v1/bookings` | Создать бронь | `201` и `Location` |
| `GET /api/v1/bookings/{id}` | Получить бронь | `200` |
| `POST /api/v1/bookings/{id}/cancel` | Отменить бронь | `200` |

Ошибки преобразуются централизованно: неверные данные — 400, не найдено — 404, конфликт — 409, сбой БД — 500.

Для учебной демонстрации `userId` передается в теле создания брони. Полноценная JWT-аутентификация описана контрактом ЛР2, но не реализована предыдущими лабораторными.

`python -m unittest tests.test_services -v` запускает модульные тесты на fake-репозиториях без сервера и базы. Для остановки: `docker compose down`; данные в томе сохраняются.
