import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Saudi Momentum Portfolio (Expanded)", layout="wide")
st.title("📊 Monthly Momentum Portfolio Backtest - Expanded Universe")


def run_backtest():

    initial_capital = 50000
    capital = initial_capital

    # ✅ قائمة موسعة ~70 سهم سعودي
    stocks = [
        "2222.SR","2010.SR","1120.SR","7010.SR","1211.SR","1180.SR","1060.SR",
        "1050.SR","1020.SR","2380.SR","2020.SR","4002.SR","4003.SR","4004.SR",
        "8010.SR","8030.SR","3008.SR","4190.SR","1810.SR","1830.SR",
        "1150.SR","1140.SR","1080.SR","1090.SR","1111.SR","1182.SR","1183.SR",
        "1201.SR","1202.SR","1301.SR","1302.SR","1320.SR","1330.SR","2001.SR",
        "2040.SR","2050.SR","2060.SR","2070.SR","2080.SR","2090.SR",
        "2100.SR","2110.SR","2120.SR","2130.SR","2140.SR","2150.SR",
        "2160.SR","2170.SR","2180.SR","2190.SR",
        "2200.SR","2210.SR","2220.SR","2230.SR","2240.SR",
        "2250.SR","2260.SR","2270.SR","2280.SR","2290.SR",
        "2300.SR","2310.SR","2320.SR","2330.SR","2340.SR"
    ]

    data = {}

    # ✅ تحميل البيانات الشهرية
    for symbol in stocks:
        df = yf.download(symbol, period="5y", interval="1d", progress=False)

        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.resample("ME").last()
        df = df.dropna()

        if len(df) >= 12:
            data[symbol] = df

    if len(data) < 10:
        return None

    # ✅ التواريخ المشتركة
    common_dates = None
    for df in data.values():
        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates & set(df.index)

    common_dates = sorted(list(common_dates))

    equity_curve = []

    for i in range(6, len(common_dates) - 1):

        date = common_dates[i]
        next_date = common_dates[i + 1]

        momentum_scores = {}

        for symbol, df in data.items():

            if date not in df.index:
                continue

            idx = df.index.get_loc(date)

            if idx < 6:
                continue

            past_price = df["Close"].iloc[idx - 6]
            current_price = df["Close"].iloc[idx]

            if past_price == 0:
                continue

            perf = (current_price - past_price) / past_price

            if pd.notna(perf):
                momentum_scores[symbol] = perf

        if len(momentum_scores) < 5:
            equity_curve.append(capital)
            continue

        # ✅ Top 5 فقط
        top5 = sorted(
            momentum_scores,
            key=momentum_scores.get,
            reverse=True
        )[:5]

        monthly_return = 0

        for symbol in top5:

            df = data[symbol]

            if next_date not in df.index:
                continue

            idx_now = df.index.get_loc(date)
            idx_next = df.index.get_loc(next_date)

            price_now = df["Close"].iloc[idx_now]
            price_next = df["Close"].iloc[idx_next]

            if price_now == 0:
                continue

            ret = (price_next - price_now) / price_now
            monthly_return += ret / 5

        capital *= (1 + monthly_return)
        equity_curve.append(capital)

    if len(equity_curve) == 0:
        return None

    equity_series = pd.Series(equity_curve)

    final_capital = equity_series.iloc[-1]
    total_return = (final_capital / initial_capital - 1) * 100
    years = len(equity_series) / 12
    cagr = ((final_capital / initial_capital) ** (1 / years) - 1) * 100

    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd = drawdown.min() * 100

    return {
        "final_capital": round(final_capital, 2),
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_dd, 2)
    }


if st.button("Run Expanded Universe Backtest"):

    results = run_backtest()

    if results is None:
        st.write("Not enough data available")
    else:
        st.subheader("📈 Portfolio Results (Expanded)")
        st.write("Final Capital:", results["final_capital"])
        st.write("Total Return %:", results["total_return"])
        st.write("CAGR %:", results["cagr"])
        st.write("Max Drawdown %:", results["max_drawdown"])
