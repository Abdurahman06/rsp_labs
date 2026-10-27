"""Run from the project root: python scripts/verify_lab5.py.

Only a newly created verification database is rolled back. The application
database is checked for persistence, and only this script's row is removed.
"""
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from http.client import HTTPException
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
config = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        config[k] = v
evidence = []
user, database = config["DB_USER"], config["DB_NAME"]
port = config.get("HTTP_PORT", "8085")


def run(label, args, expected=0, env=None):
    result = subprocess.run(args, text=True, encoding="utf-8", errors="replace",
                            capture_output=True, env=env, timeout=180)
    output = (result.stdout + result.stderr).replace(config["DB_PASSWORD"], "[REDACTED]")
    evidence.append({"check": label, "command": subprocess.list2cmdline(args),
                     "exit_code": result.returncode, "output": output})
    print(label + ": exit " + str(result.returncode), flush=True)
    if (expected == 0 and result.returncode != 0) or (expected != 0 and result.returncode == 0):
        raise AssertionError(label + "\n" + output)
    return output


def compose(label, *args, **kw):
    return run(label, ["docker", "compose", *args], **kw)


def sql(label, query, db=None, **kw):
    return compose(label, "exec", "-T", "db", "psql", "-U", user,
                   "-d", db or database, "-v", "ON_ERROR_STOP=1", "-c", query, **kw)


def health(expected):
    deadline = time.monotonic() + 40
    last = ""
    while time.monotonic() < deadline:
        try:
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=6) as response:
                    code, body = response.status, response.read().decode()
            except HTTPError as exc:
                code, body = exc.code, exc.read().decode()
            last = str(code) + " " + body
            if code == expected:
                assert json.loads(body)["db"] == ("up" if code == 200 else "down")
                evidence.append({"check": f"/health {expected}", "command": f"GET /health",
                                 "exit_code": 0, "output": last})
                print(last, flush=True)
                return
        except (URLError, TimeoutError, ConnectionError, HTTPException):
            pass
        time.sleep(0.5)
    raise AssertionError("Unexpected health response: " + last)


def main():
    verify_db = "lab5_verify_" + uuid4().hex[:12]
    marker = "persistence-" + uuid4().hex
    created = False
    try:
        compose("Compose services", "ps", "-a")
        compose("Migration log", "logs", "--no-color", "migrate")
        sql("Tables", "\\dt")
        assert "f" in sql("Migration version", "SELECT version, dirty FROM schema_migrations;")
        health(200)
        compose("Stop database", "stop", "db")
        health(503)
        compose("Start database", "start", "db")
        health(200)
        sql("Insert persistence marker",
            f"INSERT INTO hotels(name,city,address) VALUES ('{marker}','Test City','Test Street');")
        compose("Remove containers, keep volume", "down")
        compose("Recreate containers", "up", "-d")
        health(200)
        assert marker in sql("Data survived container recreation",
                            f"SELECT name FROM hotels WHERE name='{marker}';")
        sql("Remove own persistence marker", f"DELETE FROM hotels WHERE name='{marker}';")
        sql("Create isolated verification database", f"CREATE DATABASE {verify_db};")
        created = True
        test_env = dict(os.environ, DB_NAME=verify_db)
        compose("Apply isolated migration", "run", "--no-deps", "--rm", "migrate", "up", env=test_env)
        sql("Isolated tables before rollback", "\\dt", verify_db)
        sql("Seed isolated hotel",
            "INSERT INTO hotels(id,name,city,address) VALUES "
            "('00000000-0000-0000-0000-000000000001','Test Hotel','Test City','Street');", verify_db)
        sql("Valid room", "INSERT INTO rooms(hotel_id,room_number,category,price_per_night,capacity) "
            "VALUES ('00000000-0000-0000-0000-000000000001','101','STANDARD',3000.50,2);", verify_db)
        sql("Negative price rejected (CHECK)", "INSERT INTO rooms(hotel_id,room_number,category,price_per_night,capacity) "
            "VALUES ('00000000-0000-0000-0000-000000000001','102','STANDARD',-1,2);",
            verify_db, expected=1)
        sql("Missing hotel rejected (FK)", "INSERT INTO rooms(hotel_id,room_number,category,price_per_night,capacity) "
            "VALUES ('00000000-0000-0000-0000-000000000002','102','STANDARD',1,2);",
            verify_db, expected=1)
        sql("Duplicate room rejected (UNIQUE)", "INSERT INTO rooms(hotel_id,room_number,category,price_per_night,capacity) "
            "VALUES ('00000000-0000-0000-0000-000000000001','101','STANDARD',1,2);",
            verify_db, expected=1)
        compose("Rollback isolated migration", "run", "--no-deps", "--rm", "migrate", "down", "1", env=test_env)
        tables = sql("Tables after rollback", "\\dt", verify_db)
        assert "schema_migrations" in tables and "bookings" not in tables and "hotels" not in tables
        compose("Reapply isolated migration", "run", "--no-deps", "--rm", "migrate", "up", env=test_env)
        assert "bookings" in sql("Tables after reapply", "\\dt", verify_db)
        assert "no change" in compose("Repeat migration is safe", "run", "--no-deps", "--rm", "migrate", "up", env=test_env)
        compose("Missing configuration rejected", "run", "--no-deps", "--rm", "-e", "DB_PASSWORD=",
                "app", "python", "-m", "cmd.app.main", expected=1)
        retry_code = ("from dataclasses import replace; from internal.config.settings import Settings; "
                      "from internal.database.postgres import connect; "
                      "connect(replace(Settings.from_environment(),db_host='127.0.0.1',db_port=1),attempts=2)")
        out = compose("Startup retries", "run", "--no-deps", "--rm", "app", "python", "-c", retry_code, expected=1)
        assert "attempt 1/2 failed" in out and "attempt 2/2 failed" in out
        compose("Final service status", "ps", "-a")
        print("ALL LAB 5 CHECKS PASSED", flush=True)
    finally:
        compose("Restore database after verification", "start", "db")
        if created:
            sql("Remove only the temporary verification database", f"DROP DATABASE {verify_db};")
        target = ROOT / "docs" / "evidence"
        target.mkdir(parents=True, exist_ok=True)
        (target / "lab5.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
