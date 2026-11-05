import polars as pl
from paths import SPY_PICKS_CSV, MARKET_CSV, WEEKLY_CSV

result_df = pl.read_csv(SPY_PICKS_CSV, try_parse_dates=True)
polars_market = pl.read_csv(MARKET_CSV, try_parse_dates=True)

picks = result_df.filter(
    pl.col("close_pick").is_not_null() & pl.col("spy_close_pick").is_not_null()
).with_columns(
    shares_bought = 25 / pl.col("close_pick"),
    spy_shares_bought = 25 / pl.col("spy_close_pick"),
).sort("date")

# Snapshot at every pick date, plus the latest date we have market data for (today's mark)
pick_dates = picks.select("date").unique().sort("date")
latest_market_date = polars_market.select(pl.col("Date").max()).item()
weekly_dates = pl.concat([
    pick_dates,
    pl.DataFrame({"date": [latest_market_date]}, schema={"date": pl.Date}),
]).unique().sort("date")

# Cumulative amount invested as of each snapshot ($25 per pick, both strategies)
invested_by_date = (
    picks.group_by("date").agg(pl.len().alias("picks_that_week"))
    .sort("date")
    .with_columns(cumulative_invested = pl.col("picks_that_week").cum_sum() * 25)
)

weekly = weekly_dates.join_asof(
    invested_by_date, on="date", strategy="backward"
).with_columns(pl.col("cumulative_invested").fill_null(0))

# --- Stock-pick portfolio value at each snapshot ---
tickers = picks.select("sotw_ticker").unique()

ticker_cum_shares = (
    picks.sort(["sotw_ticker", "date"])
    .with_columns(cum_shares = pl.col("shares_bought").cum_sum().over("sotw_ticker"))
    .select(["sotw_ticker", "date", "cum_shares"])
)

ticker_prices = (
    polars_market.rename({"Date": "date", "ticker": "sotw_ticker"})
    .select(["sotw_ticker", "date", "close_price"])
    .sort(["sotw_ticker", "date"])
)

grid = (
    weekly_dates.join(tickers, how="cross")
    .sort(["sotw_ticker", "date"])
    .join_asof(ticker_cum_shares, on="date", by="sotw_ticker", strategy="backward")
    .with_columns(pl.col("cum_shares").fill_null(0))
    .join_asof(ticker_prices, on="date", by="sotw_ticker", strategy="backward")
)

portfolio_weekly = (
    grid.with_columns(position_value = pl.col("cum_shares") * pl.col("close_price"))
    .group_by("date")
    .agg(pl.col("position_value").sum().alias("portfolio_value"))
    .sort("date")
)

# --- SPY DCA benchmark value at each snapshot ---
spy_cum = (
    picks.sort("date")
    .with_columns(cum_spy_shares = pl.col("spy_shares_bought").cum_sum())
    .select(["date", "cum_spy_shares"])
)

spy_market_weekly_closes = (
    polars_market.filter(pl.col("ticker") == "SPY")
    .rename({"Date": "date"})
    .select(["date", "close_price"])
    .sort("date")
)

spy_weekly = (
    weekly_dates.join_asof(spy_cum, on="date", strategy="backward")
    .with_columns(pl.col("cum_spy_shares").fill_null(0))
    .join_asof(spy_market_weekly_closes, on="date", strategy="backward")
    .with_columns(spy_value = pl.col("cum_spy_shares") * pl.col("close_price"))
    .select(["date", "spy_value"])
)

# --- Combine into one week-by-week comparison ---
comparison = (
    weekly.join(portfolio_weekly, on="date", how="left")
    .join(spy_weekly, on="date", how="left")
    .with_columns([
        pl.col("portfolio_value").fill_null(0),
        pl.col("spy_value").fill_null(0),
    ])
    .with_columns([
        (pl.col("portfolio_value") - pl.col("cumulative_invested")).alias("portfolio_gain"),
        (pl.col("spy_value") - pl.col("cumulative_invested")).alias("spy_gain"),
    ])
    .select([
        "date",
        "cumulative_invested",
        "portfolio_value",
        "spy_value",
        "portfolio_gain",
        "spy_gain",
    ])
    .sort("date")
)

print(comparison)

comparison.write_csv(WEEKLY_CSV)
