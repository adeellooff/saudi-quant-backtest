import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="Saudi Quant Scanner", layout="wide")
st.title("📊 Saudi Quant Scanner - Walk Forward Momentum System")


# ===================================
# ✅ Indicator Function
# ===================================
def add_indicators(df):

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.copy()

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
# ✅ Main Backtest
# ===================================
def run_backtest():

    stocks = [
        "2222.SR", "2010.SR", "1120.SR", "7010.SR",
        "1211.SR", "1180.SR", "1060.SR", "1050.SR",
        "1020.SR", "2380.SR", "2020.SR", "4002.SR",
        "4003.SR", "4004.SR", "8010.SR", "8030.SR",
        "3008.SR", "4190.SR", "1810.SR", "1830.SR"
    ]

    # ✅ تحميل البيانات مرة واحدة
    data = {}
    for symbol in stocks:
        df = yf.download(symbol, period="3y", interval="1d", progress=False)
        if df.empty:
            continue
        data[symbol] = add_indicators(df)

    trades = []

    # ✅ نحدد التواريخ المشتركة
    common_dates = None
    for df in data.values():
        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates & set(df.index)

    common_dates = sorted(list(common_dates))

    # ✅ Walk Forward Loop
    for date in common_dates:

        momentum_scores = {}

        for symbol, df in data.items():

            if date not in df.index:
                continue

            idx = df.index.get_loc(date)

            if idx < 120:
                continue

            # ✅ Momentum 120 يوم
            perf = (
                df["Close"].iloc[idx] -
                df["Close"].iloc[idx - 120]
            ) / df["Close"].iloc[idx - 120]

            momentum_scores[symbol] = perf

        if len(momentum_scores) < 5:
            continue

        # ✅ اختيار Top 5 لذلك اليوم
        top5 = sorted(
            momentum_scores,
            key=momentum_scores.get,
            reverse=True
        )[:5]

        # ✅ تطبيق النظام فقط عليهم
        for symbol in top5:

            df = data[symbol]

            idx = df.index.get_loc(date)

            if idx < 200 or idx >= len(df) - 15:
                continue

            if not (
                df["ema50"].iloc[idx] > df["ema200"].iloc[idx]
                and df["Close"].iloc[idx] > df["ema50"].iloc[idx]
            ):
                continue

            if not (
                df["Close"].iloc[idx] > df["high_20"].iloc[idx - 1]
                and df["Close"].iloc[idx] > df["Close"].iloc[idx - 1]
                and df["rsi"].iloc[idx] > 55
                and df["Volume"].iloc[idx] > df["volume_ma"].iloc[idx] * 1.2
            ):
                continue

            entry = df["Close"].iloc[idx]
            stop = entry - df["atr"].iloc[idx]
            target = entry + 1.5 * df["atr"].iloc[idx]

            future = df.iloc[idx + 1 : idx + 15]

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
if st.button("Run Walk Forward Backtest"):

    results = run_backtest()

    st.subheader("Walk Forward Results")
    st.write("Total Trades:", results["total"])
    st.write("Win Rate:", results["winrate"], "%")
    st.write("Expectancy (R):", results["expectancy"])
