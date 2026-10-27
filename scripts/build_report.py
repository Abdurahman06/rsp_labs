"""Build a report and visual copies of REAL saved command output (no invented results)."""
import json
from pathlib import Path
import textwrap
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
number = int(sys.argv[1])
docs = ROOT / "docs"
evidence = docs / "evidence"
records = json.loads((evidence / f"lab{number}.json").read_text(encoding="utf-8"))
font_path = Path("C:/Windows/Fonts/consola.ttf")
font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
groups = ([("lab5-runtime", ["Compose services", "Tables", "Migration version", "/health 200", "/health 503"]),
           ("lab5-migrations", ["Data survived container recreation", "Rollback isolated migration",
             "Tables after rollback", "Reapply isolated migration", "Tables after reapply", "Repeat migration is safe"])]
          if number == 5 else [("lab6-tests", ["Integration tests"]), ("lab6-demo", ["Booking demonstration"])])
images = []
for name, checks in groups:
    lines = ["Actual command output / lab " + str(number), ""]
    for record in records:
        if record["check"] in checks:
            lines.append(record["check"])
            lines.extend(textwrap.wrap("$ " + record["command"], 120, replace_whitespace=False, drop_whitespace=False))
            for line in record["output"].splitlines():
                lines.extend(textwrap.wrap(line, 120, replace_whitespace=False, drop_whitespace=False) or [""])
            lines.append("")
    image = Image.new("RGB", (1400, 60 + 26 * len(lines)), "#101820")
    draw = ImageDraw.Draw(image)
    for idx, line in enumerate(lines):
        draw.text((24, 24 + idx * 26), line, font=font, fill="#e2edf7")
    image.save(evidence / (name + ".png"))
    images.append(f"![{name}](evidence/{name}.png)")
title = "PostgreSQL, миграции и Docker Compose" if number == 5 else "Слой доступа к данным: Repository"
report = [
    f"# Отчёт по лабораторной работе №{number}", "",
    "Дисциплина: «Разработка серверных приложений»", "",
    f"Тема работы: {title}", "",
    "Предметная область: бронирование номеров в городских отелях.", "",
    "Выполнил: ____________________  Группа: __________", "",
    "Проверил: ____________________  Учебное заведение: ____________________", "",
    "Дата выполнения: 28.10.2026", "",
    "## Цель", "",
    ("Подключить сервер к PostgreSQL, описать схему миграцией, организовать запуск Compose и проверить отказоустойчивость и сохранность данных."
     if number == 5 else "Отделить доступ к данным от бизнес-логики, реализовать безопасные CRUD-операции, преобразование ошибок и интеграционные тесты."),
    "", "## Реализация", "",
]
paths = (["erd.mmd", "migrations/000001_init_schema.up.sql", "migrations/000001_init_schema.down.sql", "docker-compose.yml"]
         if number == 5 else ["internal/repository/interfaces.py", "internal/repository/postgres/base.py", "internal/repository/postgres/room.py"])
for path in paths:
    kind = "mermaid" if path.endswith(".mmd") else "sql" if path.endswith(".sql") else "yaml" if path.endswith(".yml") else "python"
    report += [f"### {path}", "", f"```{kind}", (ROOT / path).read_text(encoding="utf-8"), "```", ""]
if number == 6:
    report += ["## Соответствие ошибок", "",
       "| Ситуация | SQLSTATE/признак | Доменная ошибка | HTTP |",
       "|---|---|---|---|",
       "| Нет пользователя/номера/брони | None или rowcount=0 | ErrNotFound | 404 |",
       "| Повтор email или номера внутри отеля | 23505 | ErrAlreadyExists | 409 |",
       "| Нет родителя; удаление номера с бронями | 23503 | ErrConflict | 409 |",
       "| CHECK, NULL, неверный UUID | 23514, 23502, 22P02 | ErrInvalidInput | 400 |",
       "| Сбой сети/таймаут | Другая ошибка драйвера | RepositoryError с __cause__ | 500 |",
       "| Пересечение бронирований | Проверка в сервисе | ErrConflict | 409 |", ""]
report += ["## Результаты проверки", "",
    "Ниже визуальные копии сохранённого вывода реально выполненных команд. Это рендер журнала, а не снимки окна терминала. Полный вывод и коды завершения приведены далее и сохранены в JSON.",
    "", *images, "", "### Полный журнал", ""]
for record in records:
    report += [f"#### {record['check']}", "", "```text", "$ " + record["command"],
               record["output"].rstrip(), "Exit code: " + str(record["exit_code"]), "```", ""]
report += ["## Ответы на контрольные вопросы", "",
           (docs / "DEFENSE.md").read_text(encoding="utf-8").split("## Краткие ответы на контрольные вопросы")[1], "",
           "## Выводы", "",
           ("Созданы пять связанных таблиц с ограничениями. Окружение воспроизводимо запускается, данные переживают пересоздание контейнеров. Проверены миграции up/down/up и HTTP 200/503/200."
            if number == 5 else "Реализованы четыре репозитория с независимыми интерфейсами, безопасным SQL и доменными ошибками. Проверки работают на отдельной PostgreSQL-базе. Транзакция с блокировкой номера отклоняет пересекающиеся брони, включая конкурентные запросы."),
           ""]
(docs / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
print(f"Report {number} generated from {len(records)} real records")
