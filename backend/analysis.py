"""Part 2-4 analysis logic, all reading from cell_counts.db."""

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def get_frequency_summary(conn: sqlite3.Connection) -> pd.DataFrame:
    """Part 2: relative frequency of each population within each sample."""
    df = pd.read_sql_query(
        "SELECT sample_id AS sample, population, count FROM cell_counts",
        conn,
    )
    df["population"] = pd.Categorical(df["population"], categories=POPULATIONS, ordered=True)
    df["total_count"] = df.groupby("sample")["count"].transform("sum")
    df["percentage"] = (df["count"] / df["total_count"] * 100).round(2)
    df = df.sort_values(["sample", "population"]).reset_index(drop=True)
    return df[["sample", "total_count", "population", "count", "percentage"]]


def get_responder_comparison_data(conn: sqlite3.Connection) -> pd.DataFrame:
    """Part 3: relative frequencies for melanoma/PBMC/miraclib samples,
    labeled by responder status, for the responder-vs-non-responder comparison."""
    freq = get_frequency_summary(conn)

    meta = pd.read_sql_query(
        """
        SELECT sa.sample_id AS sample, su.condition, su.treatment, su.response, sa.sample_type
        FROM samples sa
        JOIN subjects su ON su.subject_id = sa.subject_id
        WHERE su.condition = 'melanoma'
          AND su.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND su.response IS NOT NULL
        """,
        conn,
    )

    return freq.merge(meta[["sample", "response"]], on="sample", how="inner")


def run_significance_tests(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """Part 3: Mann-Whitney U test per population, responders vs non-responders.

    Mann-Whitney U is used instead of a t-test because it does not assume
    normally-distributed percentages and is robust for this sample size.
    """
    rows = []
    for population in POPULATIONS:
        pop_df = comparison_df[comparison_df["population"] == population]
        responders = pop_df.loc[pop_df["response"] == "yes", "percentage"]
        non_responders = pop_df.loc[pop_df["response"] == "no", "percentage"]
        stat, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
        rows.append(
            {
                "population": population,
                "n_responders": len(responders),
                "n_non_responders": len(non_responders),
                "median_responders": round(responders.median(), 2),
                "median_non_responders": round(non_responders.median(), 2),
                "u_statistic": stat,
                "p_value": p_value,
            }
        )
    results = pd.DataFrame(rows)

    # Correct for testing all 5 populations at once (Benjamini-Hochberg FDR).
    _, adjusted_p, _, _ = multipletests(results["p_value"], method="fdr_bh")
    results["p_value_adjusted"] = adjusted_p
    results["significant_p<0.05"] = results["p_value"] < 0.05
    results["significant_fdr<0.05"] = results["p_value_adjusted"] < 0.05

    return results.sort_values("p_value").reset_index(drop=True)


def make_boxplot(comparison_df: pd.DataFrame, out_path: Path) -> Path:
    """Part 3: boxplot of relative frequency per population, responders vs non-responders."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plot_df = comparison_df.replace({"response": {"yes": "Responder", "no": "Non-responder"}})

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=plot_df,
        x="population",
        y="percentage",
        hue="response",
        order=POPULATIONS,
        hue_order=["Responder", "Non-responder"],
        ax=ax,
    )
    ax.set_xlabel("Cell population")
    ax.set_ylabel("Relative frequency (%)")
    ax.set_title("Melanoma / miraclib / PBMC: responders vs non-responders")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def get_baseline_subset(conn: sqlite3.Connection) -> pd.DataFrame:
    """Part 4.1: melanoma PBMC baseline (time=0) samples from miraclib-treated subjects."""
    return pd.read_sql_query(
        """
        SELECT sa.sample_id AS sample, su.subject_id AS subject, su.project_id AS project,
               su.response, su.sex
        FROM samples sa
        JOIN subjects su ON su.subject_id = sa.subject_id
        WHERE su.condition = 'melanoma'
          AND su.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
        """,
        conn,
    )


def summarize_baseline_subset(baseline_df: pd.DataFrame) -> dict:
    """Part 4.2: sample counts by project, and subject counts by response / sex."""
    return {
        "samples_per_project": baseline_df.groupby("project")["sample"].count().to_dict(),
        "subjects_by_response": baseline_df["response"].value_counts().to_dict(),
        "subjects_by_sex": baseline_df["sex"].value_counts().to_dict(),
    }


def compute_avg_b_cells_melanoma_male_responders(conn: sqlite3.Connection) -> float:
    """Part 4.3: average B cell count for melanoma male responders at time=0,
    across all sample types and treatments."""
    df = pd.read_sql_query(
        """
        SELECT cc.count
        FROM cell_counts cc
        JOIN samples sa ON sa.sample_id = cc.sample_id
        JOIN subjects su ON su.subject_id = sa.subject_id
        WHERE su.condition = 'melanoma'
          AND su.sex = 'M'
          AND su.response = 'yes'
          AND sa.time_from_treatment_start = 0
          AND cc.population = 'b_cell'
        """,
        conn,
    )
    return round(df["count"].mean(), 2)
