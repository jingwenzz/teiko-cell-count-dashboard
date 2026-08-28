-- Relational schema for cell-count.csv
--
-- Normalized into four tables that mirror the natural entities in the
-- data: a project runs on many subjects, each subject contributes many
-- samples over time, and each sample has a count for every cell
-- population measured in it.
--
-- cell_counts is stored long/tidy (one row per sample+population) rather
-- than as five wide columns so that adding a new population later (e.g.
-- a sixth immune cell type) is a data insert, not a schema migration.

CREATE TABLE IF NOT EXISTS projects (
    project_id  TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(project_id),
    condition   TEXT NOT NULL,   -- disease indication, e.g. melanoma
    age         INTEGER,
    sex         TEXT,
    treatment   TEXT,
    response    TEXT             -- 'yes' / 'no' / NULL (e.g. healthy, untreated)
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT NOT NULL REFERENCES subjects(subject_id),
    sample_type                TEXT NOT NULL,  -- PBMC / WB
    time_from_treatment_start  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cell_counts (
    sample_id   TEXT NOT NULL REFERENCES samples(sample_id),
    population  TEXT NOT NULL,  -- b_cell / cd8_t_cell / cd4_t_cell / nk_cell / monocyte
    count       INTEGER NOT NULL,
    PRIMARY KEY (sample_id, population)
);

CREATE INDEX IF NOT EXISTS idx_subjects_project ON subjects(project_id);
CREATE INDEX IF NOT EXISTS idx_samples_subject ON samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_sample ON cell_counts(sample_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_population ON cell_counts(population);
