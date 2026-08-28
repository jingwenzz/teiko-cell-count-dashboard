"""
run_pipeline.py
Runs the full pipeline end to end: (re)build the database, then generate
every table and plot required by Parts 2-4 into outputs/.

Run with: python run_pipeline.py
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

import load_data  # noqa: E402
from analysis import (  # noqa: E402
    compute_avg_b_cells_melanoma_male_responders,
    get_baseline_subset,
    get_frequency_summary,
    get_responder_comparison_data,
    make_boxplot,
    run_significance_tests,
    summarize_baseline_subset,
)

OUTPUTS = ROOT / "outputs"


def main() -> None:
    load_data.main()

    conn = sqlite3.connect(load_data.DB_PATH)
    OUTPUTS.mkdir(exist_ok=True)

    # Part 2
    frequency_summary = get_frequency_summary(conn)
    frequency_summary.to_csv(OUTPUTS / "frequency_summary.csv", index=False)

    # Part 3
    comparison_df = get_responder_comparison_data(conn)
    significance = run_significance_tests(comparison_df)
    significance.to_csv(OUTPUTS / "significance_tests.csv", index=False)
    make_boxplot(comparison_df, OUTPUTS / "boxplot.png")

    # Part 4
    baseline_df = get_baseline_subset(conn)
    baseline_summary = summarize_baseline_subset(baseline_df)
    final_answer = compute_avg_b_cells_melanoma_male_responders(conn)
    (OUTPUTS / "baseline_subset_summary.json").write_text(
        json.dumps(baseline_summary, indent=2)
    )
    (OUTPUTS / "final_answer.txt").write_text(
        f"Average B cell count, melanoma male responders at time=0 "
        f"(all sample/treatment types): {final_answer:.2f}\n"
    )

    conn.close()
    print(f"Pipeline complete. Outputs written to {OUTPUTS}/")
    print(f"Part 4 final answer: {final_answer:.2f}")


if __name__ == "__main__":
    main()
