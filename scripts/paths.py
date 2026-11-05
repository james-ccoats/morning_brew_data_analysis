"""Shared project paths so scripts work from any machine and any working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "cleaned"

RAW_PICKS_XLSX = RAW_DIR / "mbdata.xlsx"
PICKS_CSV = CLEAN_DIR / "mbdata.csv"
MARKET_CSV = CLEAN_DIR / "market_data.csv"
SPY_PICKS_CSV = CLEAN_DIR / "spy_data.csv"
PORTFOLIO_CSV = CLEAN_DIR / "portfolio.csv"
WEEKLY_CSV = CLEAN_DIR / "weekly_comparison.csv"
