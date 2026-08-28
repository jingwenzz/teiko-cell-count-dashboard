"""
load_data.py
Part 1: initializes cell_counts.db and loads cell-count.csv.

Run with: python load_data.py
(No arguments, no -m; running it directly builds the database.)
"""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "backend" / "schema.sql"
CSV_PATH = ROOT / "data" / "cell-count.csv"
DB_PATH = ROOT / "cell_counts.db"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())


def load_csv(conn: sqlite3.Connection) -> None:
    with CSV_PATH.open(newline="") as f:
        rows = list(csv.DictReader(f))

    cur = conn.cursor()

    projects = {row["project"] for row in rows}
    cur.executemany(
        "INSERT OR IGNORE INTO projects (project_id) VALUES (?)",
        [(p,) for p in projects],
    )

    subjects = {}
    for row in rows:
        subjects[row["subject"]] = (
            row["subject"],
            row["project"],
            row["condition"],
            int(row["age"]),
            row["sex"],
            row["treatment"],
            row["response"] or None,
        )
    cur.executemany(
        """INSERT OR IGNORE INTO subjects
           (subject_id, project_id, condition, age, sex, treatment, response)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        list(subjects.values()),
    )

    cur.executemany(
        """INSERT OR IGNORE INTO samples
           (sample_id, subject_id, sample_type, time_from_treatment_start)
           VALUES (?, ?, ?, ?)""",
        [
            (
                row["sample"],
                row["subject"],
                row["sample_type"],
                int(row["time_from_treatment_start"]),
            )
            for row in rows
        ],
    )

    cur.executemany(
        """INSERT OR IGNORE INTO cell_counts (sample_id, population, count)
           VALUES (?, ?, ?)""",
        [
            (row["sample"], population, int(row[population]))
            for row in rows
            for population in POPULATIONS
        ],
    )

    conn.commit()


def main() -> None:
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        init_schema(conn)
        load_csv(conn)
    finally:
        conn.close()
    print(f"Loaded {CSV_PATH.name} into {DB_PATH}")


if __name__ == "__main__":
    main()
