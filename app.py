import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="Saudi Quant Scanner", layout="wide")

st.title("📊 Saudi Quant Scanner - Backtesting Engine")


# ===================================
# ✅ Indicator Preparation
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

    df["ema20"] = df["Close"].ewm(span=20, adjust=False).mean()
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
# ✅ Institutional Backtest Engine
# ===================================
def run_backtest():

    stocks = ["2222.SR", "2010.SR", "1120.SR", "7010.SR"]

    trades_A = []
    trades_B = []

    for symbol in stocks:

        df = yf.download(symbol, period="3y", interval="1d", progress=False)

        df = add_indicators(df)

        if df.empty or len(df) < 250:
            continue

        for i in range(200, len(df) - 15):

            # ============================
            # ✅ System A - Trend Breakout
            # ============================
            if (
                df["Close"].iloc[i] > df["ema200"].iloc[i]
                and df["High"].iloc[i] >= df["high_20"].iloc[i - 1]
                and df["Volume"].iloc[i] > df["volume_ma"].iloc[i]
            ):

                entry = df["Close"].iloc[i]
                stop = entry - df["atr"].iloc[i]
                target = entry + 2 * df["atr"].iloc[i]

                future = df.iloc[i + 1 : i + 15]

                result = -1

                for _, row in future.iterrows():
                    if row["Low"] <= stop:
                        result = -1
                        break
                    if row["High"] >= target:
                        result = 2
                        break

                trades_A.append(result)

            # ============================
            # ✅ System B - Pullback Trend
            # ============================
            if (
                df["Close"].iloc[i] > df["ema200"].iloc[i]
                and abs(df["Close"].iloc[i] - df["ema20"].iloc[i])
                < df["atr"].iloc[i]
                and 40 < df["rsi"].iloc[i] < 50
            ):

                entry = df["Close"].iloc[i]
                stop = entry - df["atr"].iloc[i]
                target = entry + 2 * df["atr"].iloc[i]

                future = df.iloc[i + 1 : i + 10]

                result = -1

                for _, row in future.iterrows():
                    if row["Low"] <= stop:
                        result = -1
                        break
                    if row["High"] >= target:
                        result = 2
                        break

                trades_B.append(result)

    def calculate_stats(trades):

        if len(trades) == 0:
            return {"total": 0, "winrate": 0, "expectancy": 0}

        wins = trades.count(2)
        total = len(trades)
        winrate = wins / total
        expectancy = (winrate * 2) - ((1 - winrate) * 1)

        return {
            "total": total,
            "winrate": round(winrate * 100, 2),
            "expectancy": round(expectancy, 2),
        }

    return calculate_stats(trades_A), calculate_stats(trades_B)


# ===================================
# ✅ UI
# ===================================
if st.button("Run Backtest"):

    A, B = run_backtest()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Level A")
        st.write("Total Trades:", A["total"])
        st.write("Win Rate:", A["winrate"], "%")
        st.write("Expectancy (R):", A["expectancy"])

    with col2:
        st.subheader("Level B")
        st.write("Total Trades:", B["total"])
        st.write("Win Rate:", B["winrate"], "%")
        st.write("Expectancy (R):", B["expectancy"])
