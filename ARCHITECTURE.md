# Архитектура сервиса аренды автомобилей (Carsharing API)

## Описание проекта
Бэкенд-сервис для системы каршеринга. Приложение обеспечивает поиск, бронирование и аренду автомобилей пользователями, а также управление автопарком со стороны операторов. Реализован учет пробега и уровня топлива, отслеживание доступности авто и заморозка (холдирование) депозита на карте клиента.

## Ролевая модель и Use Cases

### Водитель
- Регистрация и аутентификация
- Поиск свободных автомобилей на карте
- Бронирование и старт аренды
- Завершение аренды и расчет стоимости
- Просмотр истории поездок

### Оператор автопарка
- Добавление и редактирование автомобилей
- Изменение статусов авто (доступен, в ремонте, заблокирован)
- Мониторинг пробега, уровня топлива и текущих координат
- Просмотр общей статистики поездок
- Управление тарифами

## Диаграмма C4 Container (Уровень 2)

```mermaid
C4Container
    title Container Diagram for Carsharing API

    Person(driver, "Водитель", "Клиент сервиса, арендующий автомобили")
    Person(operator, "Оператор автопарка", "Сотрудник, следящий за состоянием машин")

    System_Boundary(carsharing, "Carsharing Platform") {
        Container(mobile_app, "Mobile App", "Flutter / Kotlin / Swift", "Приложение для поиска авто и управления арендой")
        Container(web_admin, "Admin Web Portal", "React / Vue", "Панель управления автопарком")
        Container(backend_api, "Backend API Service", "Go / Python / Java", "Основной сервер бизнес-логики и обработки аренд")
        ContainerDb(database, "Relational Database", "PostgreSQL", "Хранение данных пользователей, авто, поездок и транзакций")
        ContainerDb(redis, "In-Memory Cache", "Redis", "Кэширование геолокации и активных сессий")
    }

    System_Ext(payment_gw, "Payment Gateway", "YooKassa / Stripe", "Обработка платежей и холдирование средств")
    System_Ext(telematics, "IoT Telematics System", "GPS Tracker / OBD-II", "Передача данных о пробеге и уровне топлива")

    Rel(driver, mobile_app, "Использует", "HTTPS")
    Rel(operator, web_admin, "Использует", "HTTPS")
    
    Rel(mobile_app, backend_api, "API запросы", "JSON/HTTPS")
    Rel(web_admin, backend_api, "API запросы", "JSON/HTTPS")
    
    Rel(backend_api, database, "Чтение / Запись", "SQL/TCP")
    Rel(backend_api, redis, "Чтение / Запись", "RESP/TCP")
    
    Rel(backend_api, payment_gw, "Холдирование и списывание", "JSON/HTTPS")
    Rel(telematics, backend_api, "Телеметрия", "MQTT")
```

## ER-диаграмма базы данных (3NF)

```mermaid
erDiagram
    USERS {
        uuid id PK
        string role
        string full_name
        string phone
        string license_number
        datetime created_at
    }

    VEHICLES {
        uuid id PK
        string license_plate
        string make_model
        string status
        int fuel_level
        int mileage
    }

    TARIFFS {
        uuid id PK
        string name
        decimal price_per_minute
        decimal price_per_km
    }

    RENTALS {
        uuid id PK
        uuid user_id FK
        uuid vehicle_id FK
        uuid tariff_id FK
        datetime start_time
        datetime end_time
        int start_mileage
        int end_mileage
        decimal total_cost
        string status
    }

    PAYMENTS {
        uuid id PK
        uuid user_id FK
        uuid rental_id FK
        decimal amount
        string type
        string status
        datetime processed_at
    }

    USERS ||--o{ RENTALS : "makes"
    VEHICLES ||--o{ RENTALS : "involved_in"
    TARIFFS ||--o{ RENTALS : "applied_to"
    USERS ||--o{ PAYMENTS : "owns"
    RENTALS ||--o{ PAYMENTS : "requires"
```

### Структура таблиц и ограничений

1. **USERS**
   - `id` (UUID, PK) — идентификатор пользователя.
   - `role` (VARCHAR, NOT NULL) — роль в системе (DRIVER, OPERATOR).
   - `phone` (VARCHAR, UNIQUE, NOT NULL) — телефон.
   - `license_number` (VARCHAR, UNIQUE) — номер водительского удостоверения.
   - Индексы: `phone`, `license_number`.

2. **VEHICLES**
   - `id` (UUID, PK) — идентификатор автомобиля.
   - `license_plate` (VARCHAR, UNIQUE, NOT NULL) — регистрационный номер.
   - `status` (VARCHAR, NOT NULL) — текущий статус (AVAILABLE, IN_USE, MAINTENANCE).
   - `fuel_level` (INT, CHECK(fuel_level >= 0 AND fuel_level <= 100)) — процент топлива.
   - `mileage` (INT, CHECK(mileage >= 0)) — пробег в километрах.
   - Индексы: `status`.

3. **TARIFFS**
   - `id` (UUID, PK) — идентификатор тарифа.
   - `name` (VARCHAR, UNIQUE, NOT NULL) — название тарифа.
   - `price_per_minute` (DECIMAL, NOT NULL) — стоимость минуты аренды.
   - `price_per_km` (DECIMAL, NOT NULL) — стоимость километра пробега.

4. **RENTALS**
   - `id` (UUID, PK) — идентификатор аренды.
   - `user_id` (UUID, FK -> USERS.id, NOT NULL) — арендатор.
   - `vehicle_id` (UUID, FK -> VEHICLES.id, NOT NULL) — автомобиль.
   - `tariff_id` (UUID, FK -> TARIFFS.id, NOT NULL) — применяемый тариф.
   - `status` (VARCHAR, NOT NULL) — состояние аренды (ACTIVE, COMPLETED, CANCELED).
   - Индексы: `user_id`, `vehicle_id`.

5. **PAYMENTS**
   - `id` (UUID, PK) — идентификатор транзакции.
   - `user_id` (UUID, FK -> USERS.id, NOT NULL) — плательщик.
   - `rental_id` (UUID, FK -> RENTALS.id, NULLable) — связанная аренда.
   - `type` (VARCHAR, NOT NULL) — тип операции (DEPOSIT, PAYMENT, REFUND).
   - `status` (VARCHAR, NOT NULL) — статус транзакции (PENDING, SUCCESS, FAILED).
   - Индексы: `rental_id`.
