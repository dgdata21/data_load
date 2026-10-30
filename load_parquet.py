"""
load_parquet.py

Entry point: consolidates every raw partitioned table into one parquet file.
"""

# ============================================================
# IMPORTS
# ============================================================
import data_load.load_parquet_core as core
import data_load.load_parquet_vars as v


# ============================================================
# SECTION 1. MAIN
# ============================================================
def main():
    core.consolidate_all(v.INPUT_DIR, v.OUT_DIR)


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()
