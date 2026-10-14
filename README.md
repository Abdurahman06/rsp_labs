# Лабораторная работа №4 — контейнеризация приложения

Контейнеризация `City Hotels Booking API`, созданного в лабораторной работе №3. Работа продолжает проектирование предметной области из ЛР1, REST-контракт из ЛР2 и слоистый каркас из ЛР3.

## Что реализовано

- оптимизированный `Dockerfile` на базе `python:3.11-slim`;
- `.dockerignore` для исключения секретов, документации и временных файлов;
- запуск приложения с переменными окружения и пробросом порта;
- Docker `HEALTHCHECK`, использующий `GET /health`;
- сохранённые слои `controller`, `service`, `repository` из ЛР3.

## Сборка и запуск

```bash
docker build -t city-hotels-api:lab4 .
docker run --rm --name city-hotels-api -p 8080:8080 `
  -e APP_NAME="City Hotels Booking API" `
  -e APP_VERSION="0.1.0" `
  city-hotels-api:lab4
```

Контейнер слушает `0.0.0.0:8080`, а порт доступен на хосте как `127.0.0.1:8080`.

Проверка:

```bash
curl http://127.0.0.1:8080/health
docker inspect --format='{{json .State.Health}}' city-hotels-api
```

