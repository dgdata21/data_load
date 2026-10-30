"""
load_parquet_core.py

Core functions of the load_data package: reading raw partitioned parquet
files and consolidating each table into a single parquet file, with a check
of row counts and schemas against the source.
"""

# ============================================================
# IMPORTS
# ============================================================
from pathlib import Path
import duckdb
import pandas as pd
import project_core as glob_core


# ============================================================
# SECTION 1. LOAD RAW FILES
# ============================================================
def load_df(path, columns=None, where=None) -> pd.DataFrame:
    cols = ", ".join(columns) if columns else "*"
    q = f"SELECT {cols} FROM {glob_core.src(path)}"
    if where:
        q += f" WHERE {where}"
    return duckdb.sql(q).df()


# ============================================================
# SECTION 2. COLLECTING PIVOT FILES
# ============================================================
def consolidate_all(paths: dict[str, str], out_dir) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bad = []
    for name, p in paths.items():
        out = out_dir / f"{name}.parquet"
        duckdb.execute(
            f"COPY (SELECT * FROM {glob_core.src(p)}) "
            f"TO '{out.as_posix()}' (FORMAT parquet, COMPRESSION zstd)"
        )

        n_src = duckdb.sql(
            f"SELECT count(*) FROM {glob_core.src(p)}"
        ).fetchall()[0][0]
        n_out = duckdb.sql(
            f"SELECT count(*) FROM {glob_core.src(out)}"
        ).fetchall()[0][0]
        rows_ok = n_src == n_out

        s_src, s_out = glob_core.schema(p), glob_core.schema(out)
        cols_ok = s_src == s_out

        print(
            f"{name}: "
            f"source rows={n_src}, pivot-file={n_out} "
            f"[{'OK' if rows_ok else 'not OK'}]; "
            f"source columns={len(s_src)}, pivot-file={len(s_out)} "
            f"[{'OK' if cols_ok else 'not OK'}]; "
            f"{out.stat().st_size / 1024**2:.1f} MiB -> {out}"
        )

        if not cols_ok:
            print(
                f"  source only: {s_src.keys() - s_out.keys()}\n"
                f"  pivot-file only: {s_out.keys() - s_src.keys()}\n"
                f"  other type: "
                f"{[c for c in s_src.keys() & s_out.keys() \
                    if s_src[c] != s_out[c]]}"
            )

        if not (rows_ok and cols_ok):
            bad.append(name)

    ok = [n for n in paths if n not in bad]
    print(f"\nOK: {ok}")
    print(f"PROBLEMS: {bad}")
    if bad:
        raise RuntimeError(f"Audit failed for: {bad}")
