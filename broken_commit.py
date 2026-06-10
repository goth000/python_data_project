from pathlib import Path
import sqlite3
import tempfile


DB_PATH = Path(tempfile.gettempdir()) / "broken_commit_example.db"


def prepare_database() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS example (value INTEGER)")
        connection.execute("DELETE FROM example")


def count_rows() -> int:
    with sqlite3.connect(DB_PATH) as connection:
        result = connection.execute("SELECT COUNT(*) FROM example").fetchone()

    return result[0]


def demonstrate_missing_commit() -> None:
    connection = sqlite3.connect(DB_PATH)
    connection.execute("INSERT INTO example (value) VALUES (1)")
    connection.close()

    print("[BROKEN] Rows after reopening without commit:", count_rows())


def demonstrate_commit() -> None:
    connection = sqlite3.connect(DB_PATH)
    connection.execute("INSERT INTO example (value) VALUES (1)")
    connection.commit()
    connection.close()

    print("[FIXED] Rows after reopening with commit:", count_rows())


def main() -> None:
    print("[INFO] SQLite database:", DB_PATH)

    prepare_database()
    demonstrate_missing_commit()
    demonstrate_commit()

    print("[INFO] Without commit, SQLite rolls back the pending insert on close.")
    print("[INFO] With commit, the insert remains in the same database file.")


if __name__ == "__main__":
    main()
