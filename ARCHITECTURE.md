# City Hotels Booking API — лабораторная работа №3

## Назначение

В работе создан базовый каркас серверного приложения для сервиса бронирования отелей из лабораторных №1 и №2. Каркас реализует Clean/Layered Architecture, читает конфигурацию из переменных окружения и содержит рабочий endpoint проверки состояния сервиса.

## Выбранный стек

- Python 3.11+;
- стандартная библиотека `http.server` без внешних зависимостей;
- JSON over HTTP;
- PostgreSQL и Redis подключаются через repository-адаптеры на следующих этапах проекта.

## Слои приложения

```text
HTTP request
    ↓
internal/controller       Transport layer: URL, HTTP status, JSON
    ↓
internal/service           Domain layer: use cases and business rules
    ↓
internal/repository       Data-access layer: database/cache adapters
    ↓
PostgreSQL / Redis
```

Зависимости направлены внутрь: контроллер вызывает сервис, сервис работает через абстракцию repository. Сервис не знает, пришёл ли запрос по HTTP, и не содержит SQL. Контроллер не обращается к PostgreSQL напрямую.

## Структура каталогов

```text
.
├── cmd/app/main.py                 # точка входа и сборка зависимостей
├── internal/
│   ├── config/settings.py          # загрузка .env и проверка конфигурации
│   ├── controller/health_handler.py# HTTP transport layer
│   ├── service/health_service.py  # health use case
│   └── repository/health_repository.py # infrastructure adapter
├── .env.example                    # безопасный шаблон конфигурации
├── .gitignore
├── openapi.yaml                    # спецификация из лабораторной №2
└── README.md
```

## Переменные окружения

Секреты и настройки не зашиваются в код. При запуске приложение читает `.env`, а если его нет — использует значения по умолчанию. В Git хранится только `.env.example`; реальный `.env` исключён через `.gitignore`.

| Переменная | Назначение | Пример |
|---|---|---|
| `APP_NAME` | Название сервиса | `City Hotels Booking API` |
| `APP_VERSION` | Версия API/приложения | `0.1.0` |
| `APP_HOST` | Адрес прослушивания | `127.0.0.1` |
| `APP_PORT` | HTTP-порт | `8080` |

## Health endpoint

`GET /health` и `GET /api/v1/health` возвращают `200 OK` и JSON:

```json
{
  "status": "ok",
  "service": "City Hotels Booking API",
  "version": "0.1.0",
  "uptime_seconds": 12.431,
  "dependencies": {"application": "ok"}
}
```

Endpoint не требует авторизации и нужен для мониторинга, проверки запуска контейнера и балансировщиками нагрузки. Значение `uptime_seconds` считается от момента запуска процесса.

## Запуск и проверка

```bash
cp .env.example .env
python -m cmd.app.main
curl http://127.0.0.1:8080/health
```

Ожидаемый результат — HTTP `200` и JSON с полями `status`, `service`, `version` и `uptime_seconds`.
