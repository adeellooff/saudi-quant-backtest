import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="Saudi Quant Scanner", layout="wide")

st.title("📊 Saudi Quant Scanner - Momentum Ranking System")


# ===================================
# ✅ Indicator Function
# ===================================
def add_indicators(df):

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.copy()

    numeric_cols = ["Close", "High", "Low", "Volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(inplace=True)

    df["ema50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["rsi"] = ta.momentum.rsi(df["Close"], window=14)
    df["atr"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], window=14
    )
    df["volume_ma"] = df["Volume"].rolling(20).mean()
    df["high_20"] = df["High"].rolling(20).max()

    df.dropna(inplace=True)

    return df


# ===================================
# ✅ Backtest Engine with Ranking
# ===================================
def run_backtest():

    stocks = [
        "2222.SR", "2010.SR", "1120.SR", "7010.SR",
        "1211.SR", "1180.SR", "1060.SR", "1050.SR",
        "1020.SR", "2380.SR", "2020.SR", "4002.SR",
        "4003.SR", "4004.SR", "8010.SR", "8030.SR",
        "3008.SR", "4190.SR", "1810.SR", "1830.SR"
    ]

    momentum_scores = {}

    # ✅ حساب Momentum لكل سهم
    for symbol in stocks:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df.empty or len(df) < 120:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        performance = (
            df["Close"].iloc[-1] - df["Close"].iloc[-120]
        ) / df["Close"].iloc[-120]

        momentum_scores[symbol] = performance

    if len(momentum_scores) == 0:
        return {"total": 0, "winrate": 0, "expectancy": 0}

    # ✅ اختيار أعلى 8 أسهم
    top_stocks = sorted(
        momentum_scores,
        key=momentum_scores.get,
        reverse=True
    )[:8]

    trades = []

    # ✅ تطبيق الاستراتيجية فقط على الأسهم الأقوى
    for symbol in top_stocks:

        df = yf.download(symbol, period="3y", interval="1d", progress=False)
        df = add_indicators(df)

        if df.empty or len(df) < 250:
            continue

        for i in range(200, len(df) - 15):

            if not (
                df["ema50"].iloc[i] > df["ema200"].iloc[i]
                and df["Close"].iloc[i] > df["ema50"].iloc[i]
            ):
                continue

            if not (
                df["Close"].iloc[i] > df["high_20"].iloc[i - 1]
                and df["Close"].iloc[i] > df["Close"].iloc[i - 1]
                and df["rsi"].iloc[i] > 55
                and df["Volume"].iloc[i] > df["volume_ma"].iloc[i] * 1.2
            ):
                continue

            entry = df["Close"].iloc[i]
            stop = entry - df["atr"].iloc[i]
            target = entry + 1.5 * df["atr"].iloc[i]

            future = df.iloc[i + 1 : i + 15]

            result = -1

            for _, row in future.iterrows():
                if row["Low"] <= stop:
                    result = -1
                    break
                if row["High"] >= target:
                    result = 1.5
                    break

            trades.append(result)

    if len(trades) == 0:
        return {"total": 0, "winrate": 0, "expectancy": 0}

    wins = trades.count(1.5)
    total = len(trades)
    winrate = wins / total
    expectancy = (winrate * 1.5) - ((1 - winrate) * 1)

    return {
        "total": total,
        "winrate": round(winrate * 100, 2),
        "expectancy": round(expectancy, 2),
    }


# ===================================
# ✅ UI
# ===================================
if st.button("Run Ranking Backtest"):

    results = run_backtest()

    st.subheader("Momentum Ranking Results")
    st.write("Total Trades:", results["total"])
    st.write("Win Rate:", results["winrate"], "%")
    st.write("Expectancy (R):", results["expectancy"])
