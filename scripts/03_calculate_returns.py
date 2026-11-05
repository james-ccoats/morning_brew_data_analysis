import polars as pl
from paths import SPY_PICKS_CSV, MARKET_CSV, PORTFOLIO_CSV

result_df = pl.read_csv(SPY_PICKS_CSV)
polars_market = pl.read_csv(MARKET_CSV)

latest_prices = (
    polars_market.group_by("ticker")
    .agg(pl.col("close_price").last().alias("current_price"))
)

dca = result_df.filter(pl.col("close_pick").is_not_null()).with_columns(
    shares_bought = 25 / pl.col("close_pick")
)

shares_by_ticker = dca.group_by("sotw_ticker").agg(
    pl.col("shares_bought").sum().alias("total_shares")
)

portfolio = shares_by_ticker.join(
    latest_prices, left_on="sotw_ticker", right_on="ticker", how="left"
).with_columns(
    position_value = pl.col("total_shares") * pl.col("current_price")
)

total_invested = dca.height * 25
total_value = portfolio.select(pl.col("position_value").sum()).item()

# Benchmark: what if the same $25-per-pick-date had gone into SPY instead
spy_dca = result_df.filter(pl.col("spy_close_pick").is_not_null()).with_columns(
    spy_shares_bought = 25 / pl.col("spy_close_pick")
)

spy_total_shares = spy_dca.select(pl.col("spy_shares_bought").sum()).item()
spy_market_weekly_closes = (
    polars_market.filter(pl.col("ticker") == "SPY").sort("Date")
)
spy_current_price = spy_market_weekly_closes.select(pl.col("close_price").last()).item()
spy_invested = spy_dca.height * 25
spy_total_value = spy_total_shares * spy_current_price

print(portfolio.sort("position_value", descending=True))
print(f"Total invested: ${total_invested}")
print(f"Portfolio value today: ${total_value:.2f}")
print(f"Portfolio return: {(total_value - total_invested) / total_invested:.1%}")
print()
print(f"SPY invested: ${spy_invested}")
print(f"SPY value today: ${spy_total_value:.2f}")
print(f"SPY return: {(spy_total_value - spy_invested) / spy_invested:.1%}")

portfolio.write_csv(PORTFOLIO_CSV)
