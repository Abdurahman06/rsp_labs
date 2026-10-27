"""Create an isolated database, apply migration, run real tests and demo, clean up."""
import json
import os
import re
from pathlib import Path
from uuid import uuid4
import verify_lab5 as helper

ROOT = Path(__file__).resolve().parents[1]


def main():
    database = "lab6_test_" + uuid4().hex[:12]
    created = False
    try:
        helper.sql("Create isolated test database", f"CREATE DATABASE {database};")
        created = True
        env = dict(os.environ, DB_NAME=database)
        helper.compose("Apply test migration", "run", "--no-deps", "--rm", "migrate", "up", env=env)
        output = helper.compose("Integration tests", "run", "--no-deps", "--rm",
                       "-v", str(ROOT / "tests") + ":/app/tests:ro", "app",
                       "python", "-m", "unittest", "discover", "-s", "tests", "-v", env=env)
        match = re.search(r"Ran (\d+) tests", output)
        if not match or int(match.group(1)) < 19:
            raise AssertionError("Expected all 19 integration tests to execute")
        helper.compose("Booking demonstration", "run", "--no-deps", "--rm",
                       "-v", str(ROOT / "scripts") + ":/app/scripts:ro", "app",
                       "python", "-m", "scripts.demo_booking", env=env)
        helper.compose("Final service status", "ps", "-a")
        print("ALL LAB 6 CHECKS PASSED")
    finally:
        if created:
            helper.sql("Remove only the temporary test database", f"DROP DATABASE {database};")
        evidence = ROOT / "docs" / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "lab6.json").write_text(json.dumps(helper.evidence, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
