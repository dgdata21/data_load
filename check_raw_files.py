"""
check_raw_files.py

Exploration of the raw partitioned parquet files exported from the database:
files, size on disk, rows, estimated RAM, and DESCRIBE / SAMPLE / SUMMARIZE
for every table. The result is printed and saved to eda_all.txt.
"""

# ============================================================
# IMPORTS
# ============================================================
import duckdb
import pandas as pd
import data_load.load_parquet_vars as v
import project_core as glob_core


# ============================================================
# SECTION 1. SOURCE STATISTICS
# ============================================================
def source_stats(paths: dict, sample_rows: int = 10_000) -> pd.DataFrame:
    """Files, size on disk, rows and estimated RAM for each raw table."""
    out = []
    for name, p in paths.items():
        files = [
            f
            for x in glob_core.paths_of(p)
            for f in (x.rglob("*.parquet") if x.is_dir() else [x])
        ]
        src = glob_core.src(p)
        n_rows = duckdb.sql(f"SELECT count(*) FROM {src}").fetchall()[0][0]
        smp = duckdb.sql(
            f"SELECT * FROM {src} USING SAMPLE {sample_rows} ROWS"
        ).df()
        out.append(
            {
                "table": name,
                "files": len(files),
                "disk_mib": round(
                    sum(f.stat().st_size for f in files) / 1024**2, 1
                ),
                "rows": n_rows,
                "cols": smp.shape[1],
                "est_ram_mib": round(
                    smp.memory_usage(deep=True).sum()
                    / len(smp)
                    * n_rows
                    / 1024**2,
                    1,
                ),
            }
        )
    return pd.DataFrame(out)


# ============================================================
# SECTION 2. TABLE EDA
# ============================================================
def eda_text(name: str, p) -> str:
    """DESCRIBE, SAMPLE and SUMMARIZE of one raw table as text."""
    src = glob_core.src(p)
    parts = [f"\n===== {name} ====="]
    for title, sql in (
        ("DESCRIBE", f"DESCRIBE SELECT * FROM {src}"),
        ("SAMPLE", f"SELECT * FROM {src} USING SAMPLE 10 ROWS"),
        ("SUMMARIZE", f"SUMMARIZE SELECT * FROM {src}"),
    ):
        df = duckdb.sql(sql).df()
        if title == "SUMMARIZE":
            cols = ["avg", "std", "q25", "q50", "q75"]
            df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")
        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].round(4)
        parts.append(f"\n--- {title} ---\n{df.to_string(index=False)}")
    return "\n".join(parts)


# ============================================================
# SECTION 3. MAIN
# ============================================================
def main():
    print()
    stats = source_stats(v.INPUT_DIR)
    report = [
        stats.to_string(index=False),
        f"Total RAM, MiB: {stats['est_ram_mib'].sum():,.1f}",
    ]
    report += [eda_text(name, p) for name, p in v.INPUT_DIR.items()]

    text = "\n".join(report)
    print(text)
    v.OUT_DIR.mkdir(parents=True, exist_ok=True)
    (v.OUT_DIR / "eda_all.txt").write_text(text, encoding="utf-8")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()
