import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np

st.set_page_config(page_title="Saudi Quant Backtest", layout="wide")

st.title("📊 Saudi Quant Scanner - Backtesting Engine")

STOCKS = ["2222.SR","1120.SR","2010.SR","7010.SR","1211.SR"]

def add_indicators(df):
    df['ema20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
    df['macd'] = ta.trend.macd(df['Close'])
    return df

def calculate_score(df, i):
    score = 0
    row = df.iloc[i]

    if row['Close'] > df['High'].rolling(20).max().iloc[i-1]:
        score += 30

    if row['ema20'] > row['ema50']:
        score += 20

    if 45 < row['rsi'] < 70:
        score += 15

    if df['macd'].iloc[i] > 0 and df['macd'].iloc[i-1] < 0:
        score += 20

    return score

def simulate_trade(df, i):
    entry = df['Close'].iloc[i]
    stop = df['Low'].rolling(10).min().iloc[i]
    risk = entry - stop

    if risk <= 0:
        return 0

    target = entry + (risk * 2)

    for j in range(i+1, min(i+11, len(df))):
        if df['High'].iloc[j] >= target:
            return 2
        if df['Low'].iloc[j] <= stop:
            return -1

    return 0

def run_backtest():
    results_A = []
    results_B = []

    for stock in STOCKS:
        df = yf.download(stock, period="3y", interval="1d", progress=False)
        df.dropna(inplace=True)
        df = add_indicators(df)

        for i in range(50, len(df)-11):
            score = calculate_score(df, i)

            if score >= 75:
                results_A.append(simulate_trade(df, i))
            elif score >= 55:
                results_B.append(simulate_trade(df, i))

    return results_A, results_B

if st.button("Run Backtest"):
    A, B = run_backtest()

    def stats(results):
        wins = results.count(2)
        losses = results.count(-1)
        total = len(results)
        winrate = (wins / total * 100) if total > 0 else 0
        expectancy = np.mean(results) if total > 0 else 0
        return total, round(winrate,2), round(expectancy,2)

    total_A, win_A, exp_A = stats(A)
    total_B, win_B, exp_B = stats(B)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Level A")
        st.write("Total Trades:", total_A)
        st.write("Win Rate:", win_A, "%")
        st.write("Expectancy (R):", exp_A)

    with col2:
        st.subheader("Level B")
        st.write("Total Trades:", total_B)
        st.write("Win Rate:", win_B, "%")
        st.write("Expectancy (R):", exp_B)
