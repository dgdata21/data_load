"""
project_core.py
"""

import pandas as pd
import duckdb
from pathlib import Path


# ============================================================
# PRINT OPTIONS
# ============================================================
def print_df():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    pd.set_option("display.float_format", "{:,.3f}".format)


def title(title, width=112):
    print()
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def paths_of(p) -> list[Path]:
    return [Path(p)] if isinstance(p, (str, Path)) else [Path(x) for x in p]


def src(p) -> str:
    globs = [
        (
            x.as_posix()
            if x.suffix == ".parquet"
            else f"{x.as_posix()}/**/*.parquet"
        )
        for x in paths_of(p)
    ]
    return f"read_parquet({globs}, hive_partitioning=1, union_by_name=1)"


# ============================================================
# SCHEMA
# ============================================================
def schema(path) -> dict[str, str]:
    """{колонка: тип}, данные не читаются."""
    rel = duckdb.sql(f"SELECT * FROM {src(path)} LIMIT 0")
    return dict(zip(rel.columns, map(str, rel.types)))
