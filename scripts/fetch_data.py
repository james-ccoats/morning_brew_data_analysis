import yfinance as yf
import polars as pl
import fastexcel
import os
from datetime import timedelta

load_path = os.path.expanduser('/Users/jamesccoats/Dev/MorningBrewViz/data/raw/mbdata.xlsx')
save_path = os.path.expanduser('/Users/jamesccoats/Dev/MorningBrewViz/data/cleaned/mbdata.csv')
mb_data = pl.read_excel(load_path)

mb_data = mb_data.filter(pl.col('sotw_ticker').is_not_null() & pl.col('date').is_not_null())
mb_data = mb_data.with_row_index("pick_id").with_columns(
    one_week_date = pl.col('date') + timedelta(weeks = 1),
    one_month_update = pl.col("date") + timedelta(weeks = 4),
    six_month_update = pl.col("date") + timedelta(weeks = 26),
    one_year_update = pl.col("date") + timedelta(weeks = 52)
)

tickers = mb_data.select(pl.col('sotw_ticker').str.join(delimiter=" ")).item()
min_date = mb_data.select(pl.col('date').min()).item()
# needs to cover out to one_year_update, plus a buffer for weekends/holidays
max_date = mb_data.select(pl.col('date').max()).item() + timedelta(weeks=52, days=7)

market_data = yf.download(
    tickers=tickers,
    start=min_date,
    end=max_date,
    group_by="ticker"
)

market_df = market_data.xs("Close", level=1, axis=1).reset_index()
pandas_long = market_df.melt(id_vars=["Date"], var_name="ticker", value_name="close_price")

polars_market = (
    pl.from_pandas(pandas_long)
    .with_columns(pl.col("Date").dt.date())
    .drop_nulls("close_price")
    .sort(["ticker", "Date"])
)

horizon_cols = ["date", "one_week_date", "one_month_update", "six_month_update", "one_year_update"]

long_dates = mb_data.select(["pick_id", "sotw_ticker", *horizon_cols]).unpivot(
    index=["pick_id", "sotw_ticker"],
    on=horizon_cols,
    variable_name="horizon",
    value_name="target_date"
).sort(["sotw_ticker", "target_date"])

joined = long_dates.join_asof(
    polars_market,
    left_on="target_date",
    right_on="Date",
    by_left="sotw_ticker",
    by_right="ticker",
    strategy="forward",
)

wide = joined.pivot(
    index="pick_id",
    on="horizon",
    values="close_price"
).rename({
    "date": "close_pick",
    "one_week_date": "close_1wk",
    "one_month_update": "close_1mo",
    "six_month_update": "close_6mo",
    "one_year_update": "close_1yr",
})

result_df = mb_data.join(wide, on="pick_id", how="left")

result_df.write_csv(save_path)