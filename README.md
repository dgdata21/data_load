# `load_data` package: raw file exploration and consolidation

## Purpose

The second step of the project, after database exploration. The data has already been exported from the database as partitioned parquet files (one folder per table, many files inside). This package:

1. **explores** the raw files (size, rows, column types, value ranges);
2. **consolidates** every table into a single parquet file and verifies that no rows or columns were lost.

Pipeline position:

```
database exploring -> export (manual) -> load_data -> data quality -> data types -> currency conversion
```

## Modules

| Module | Role |
|---|---|
| `load_parquet_vars.py` | Settings: raw source directories and the output directory |
| `load_parquet_core.py` | Functions: `load_df` and `consolidate_all` |
| `load_parquet.py` | Entry point: consolidation of all tables |
| `check_raw_files.py` | Entry point: exploration of the raw files |
| `project_core.py` | Global Functions |

Run from the project root: first `python check_raw_files.py`, then `python load_parquet.py`.

The package relies on three helpers from the shared `project_core` module (they are not part of this package): `paths_of(p)` (list of paths for a source), `src(p)` (SQL expression that reads a source), and `schema(p)` (dict `column -> type`).

## 1. load_parquet_vars.py

- `INPUT_DIR` — dictionary `table name -> source`. The key becomes the name of the output file (`casino` -> `casino.parquet`). A source is a folder with partitions (facts, `fx`) or a single parquet file (`players`).
- `OUT_DIR` — folder for the consolidated files (and for `eda_all.txt`). Downstream packages must read from this same folder.

## 2. load_parquet_core.py

**`load_df(path, columns=None, where=None)`** — reads a raw source into pandas through DuckDB:
- builds `SELECT <columns or *> FROM <source>`;
- appends `WHERE <where>` when a filter is given;
- returns a DataFrame. Not used by the entry points; kept as a helper.

**`consolidate_all(paths, out_dir)`**
- creates `out_dir` if it does not exist;
- for every table, `COPY (SELECT * FROM <source>) TO <name>.parquet (FORMAT parquet, COMPRESSION zstd)` — DuckDB streams the data to disk without pandas, so large tables do not need to fit in memory;
- counts rows in the source and in the new file (`rows_ok`);
- compares the schemas of both (`cols_ok`): column names and types;
- prints one line per table: row counts, column counts, `OK` / `not OK`, size in MiB and path;
- on a schema mismatch prints the columns that exist only in the source, only in the pivot file, and the columns whose type differs;
- collects the tables with problems; at the end prints `OK: [...]` and `PROBLEMS: [...]` and raises `RuntimeError` if any table failed.

Existing output files are overwritten without a warning.

## 3. load_parquet.py

`main()` calls `consolidate_all(INPUT_DIR, OUT_DIR)`.

## 4. check_raw_files.py

**`source_stats(paths, sample_rows=10_000)`** — one row per table:
- `files` — number of parquet files (recursively for folders);
- `disk_mib` — total size on disk;
- `rows` — row count;
- `cols` — number of columns;
- `est_ram_mib` — estimated size of the table as a pandas DataFrame: memory per row measured on a random sample of `sample_rows` rows, multiplied by the number of rows.

**`eda_text(name, p)`** — text report for one table:
- `DESCRIBE` — column names and DuckDB types;
- `SAMPLE` — 10 random rows;
- `SUMMARIZE` — per column: min, max, `approx_unique`, average, standard deviation, quartiles, row count and `null_percentage`. Average, deviation and quartiles are empty for text and date columns. Numeric values are rounded to 4 decimals, so small shares and rates stay visible.

**`main()`** — prints and saves the statistics table, the total estimated RAM and the report of every table to `OUT_DIR/eda_all.txt` (the folder is created if needed). Every query runs once; the same text goes to the screen and to the file.

## What to check in the output

- Row counts and period of the raw files against the previous export: they must match the source of the pivot files, otherwise the pivot files are stale.
- `DESCRIBE`: column types must be the same across exports; the consolidation check compares them automatically.
- `SUMMARIZE`: ranges of dates and amounts, `null_percentage`, and the number of distinct values of categorical columns.

## Notes

1. `approx_unique` is an estimate and can be wrong, including for small columns. Do not use it to verify keys; use an exact check in the data quality step.
2. Equal row counts and schemas do not prove that the contents are identical.
3. The consolidation does not remove old files from `OUT_DIR`.
4. `OUT_DIR` and the folders in `INPUT_DIR` are absolute paths; adjust them to your machine.
5. `est_ram_mib` depends on the pandas version (text columns take much less memory in pandas 3 than in pandas 2) and is only an estimate.
