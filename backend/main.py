"""FastAPI app: exposes Parts 2-4 analysis results and serves the built
React dashboard as static files."""

import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.analysis import (
    compute_avg_b_cells_melanoma_male_responders,
    get_baseline_subset,
    get_frequency_summary,
    get_responder_comparison_data,
    run_significance_tests,
    summarize_baseline_subset,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "cell_counts.db"
FRONTEND_DIST = ROOT / "frontend" / "dist"

app = FastAPI(title="Teiko Cell Count Dashboard API")


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@app.get("/api/summary")
def summary():
    conn = get_conn()
    df = get_frequency_summary(conn)
    conn.close()
    return df.to_dict(orient="records")


@app.get("/api/significance")
def significance():
    conn = get_conn()
    comparison_df = get_responder_comparison_data(conn)
    conn.close()
    return run_significance_tests(comparison_df).to_dict(orient="records")


@app.get("/api/baseline-subset")
def baseline_subset():
    conn = get_conn()
    df = get_baseline_subset(conn)
    conn.close()
    return summarize_baseline_subset(df)


@app.get("/api/final-answer")
def final_answer():
    conn = get_conn()
    value = compute_avg_b_cells_melanoma_male_responders(conn)
    conn.close()
    return {"avg_b_cells_melanoma_male_responders_t0": value}


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
