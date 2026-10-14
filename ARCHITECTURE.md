# City Hotels Booking API — лабораторная работа №4

## Назначение

В работе приложение из лабораторной №3 упаковано в Docker-контейнер. Контейнер содержит минимальное Python-окружение, слоистый каркас сервиса, конфигурацию запуска и рабочий endpoint проверки состояния.

## Docker

`Dockerfile` использует `python:3.11-slim`. Для интерпретируемого Python-приложения это оптимальнее, чем добавлять компилятор и SDK: внешних зависимостей нет, поэтому отдельный builder-этап не требуется. В образ копируются только каталоги `cmd/` и `internal/`; документация, OpenAPI-файл, Git-метаданные, `.env`, кэши и IDE-файлы исключены через `.dockerignore`.

Контейнер запускается на `0.0.0.0:8080`, порт пробрасывается командой `-p 8080:8080`. Переменные `APP_NAME` и `APP_VERSION` передаются через `docker run -e`.

В Dockerfile настроен `HEALTHCHECK`: каждые 30 секунд он отправляет запрос к `http://127.0.0.1:8080/health`. Если сервер отвечает успешно, контейнер считается healthy.

## Структура приложения

В контейнер переносится каркас ЛР3:

```text
cmd/app/main.py                 # точка входа
internal/config/                # переменные окружения
internal/controller/            # HTTP transport layer
internal/service/               # бизнес-логика
internal/repository/            # адаптеры данных
```

## Сборка и проверка

```bash
docker build -t city-hotels-api:lab4 .
docker run --rm --name city-hotels-api -p 8080:8080 city-hotels-api:lab4
curl http://127.0.0.1:8080/health
```

Ожидаемый результат — HTTP `200` и JSON с полями `status`, `service`, `version` и `uptime_seconds`.
