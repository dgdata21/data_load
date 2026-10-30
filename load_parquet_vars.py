"""
load_parquet_vars.py

Settings of the load_data package: raw source directories and the output
directory for the consolidated (pivot) files.
"""

from pathlib import Path

# ============================================================
# SECTION 1. SOURCE DIRECTORIES
# ============================================================
INPUT_DIR = {
    "bonus": r"/Your_Path/fact_bonuses",
    "casino": r"/Your_Path/fact_casino_rounds",
    "poker": r"/Your_Path/fact_poker_sessions",
    "sport": r"/Your_Path/fact_sportsbook_bets",
    "sessions": r"/Your_Path/fact_sessions",
    "tzx": r"/Your_Path/fact_transactions",
    "fx": r"/Your_Path/dim_fx_rates",
    "players": r"/Your_Path/dim_players.parquet",
}

# ============================================================
# SECTION 2. OUTPUT DIRECTORY
# ============================================================
OUT_DIR = Path(r"/Your_Path/pivot_data")
