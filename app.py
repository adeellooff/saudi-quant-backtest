import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Saudi Momentum Portfolio", layout="wide")
st.title("📊 Monthly Momentum Portfolio Backtest")


def run_backtest():

    initial_capital = 50000
    capital = initial_capital

    stocks = [
        "2222.SR", "2010.SR", "1120.SR", "7010.SR",
        "1211.SR", "1180.SR", "1060.SR", "1050.SR",
        "1020.SR", "2380.SR", "2020.SR", "4002.SR",
        "4003.SR", "4004.SR", "8010.SR", "8030.SR",
        "3008.SR", "4190.SR", "1810.SR", "1830.SR"
    ]

    data = {}

    # ✅ تحميل البيانات
    for symbol in stocks:
        df = yf.download(symbol, period="3y", interval="1d", progress=False)
        if df.empty:
            continue
        df = df.resample("M").last()  # تحويل إلى بيانات شهرية
        data[symbol] = df

    # ✅ تحديد التواريخ المشتركة
    common_dates = None
    for df in data.values():
        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates & set(df.index)

    common_dates = sorted(list(common_dates))

    equity_curve = []

    # ✅ بدء من الشهر 7 (لأننا نحتاج 6 أشهر لحساب المومنتوم)
    for i in range(6, len(common_dates) - 1):

        date = common_dates[i]

        momentum_scores = {}

        for symbol, df in data.items():

            if date not in df.index:
                continue

            idx = df.index.get_loc(date)

            if idx < 6:
                continue

            perf = (
                df["Close"].iloc[idx] -
                df["Close"].iloc[idx - 6]
            ) / df["Close"].iloc[idx - 6]

            momentum_scores[symbol] = perf

        if len(momentum_scores) < 5:
            equity_curve.append(capital)
            continue

        top5 = sorted(
            momentum_scores,
            key=momentum_scores.get,
            reverse=True
        )[:5]

        next_date = common_dates[i + 1]

        monthly_return = 0

        for symbol in top5:
            df = data[symbol]
            if next_date not in df.index:
                continue

            idx_now = df.index.get_loc(date)
            idx_next = df.index.get_loc(next_date)

            ret = (
                df["Close"].iloc[idx_next] -
                df["Close"].iloc[idx_now]
            ) / df["Close"].iloc[idx_now]

            monthly_return += ret / 5  # توزيع متساوي

        capital *= (1 + monthly_return)
        equity_curve.append(capital)

    if len(equity_curve) == 0:
        return None

    equity_series = pd.Series(equity_curve)

    total_return = (equity_series.iloc[-1] / initial_capital - 1) * 100
    years = len(equity_series) / 12
    cagr = ((equity_series.iloc[-1] / initial_capital) ** (1 / years) - 1) * 100

    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd = drawdown.min() * 100

    return {
        "final_capital": round(equity_series.iloc[-1], 2),
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_dd, 2)
    }


if st.button("Run Monthly Portfolio Backtest"):

    results = run_backtest()

    if results is None:
        st.write("No data available")
    else:
        st.subheader("📈 Portfolio Results")
        st.write("Final Capital:", results["final_capital"])
        st.write("Total Return %:", results["total_return"])
        st.write("CAGR %:", results["cagr"])
        st.write("Max Drawdown %:", results["max_drawdown"])
