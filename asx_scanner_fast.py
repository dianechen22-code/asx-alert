from __future__ import annotations

import os
import pandas as pd
import yfinance as yf
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

INDEX = "STW.AX"


# --------------------------
# TELEGRAM
# --------------------------

def send(msg):

    if not TOKEN:
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,json={
        "chat_id":CHAT,
        "text":msg
    })


# --------------------------
# ASX200 TICKERS
# --------------------------

def get_asx200():

    url = "https://en.wikipedia.org/wiki/S%26P/ASX_200"

    table = pd.read_html(url)[0]

    tickers = [t + ".AX" for t in table["Code"]]

    return tickers


# --------------------------
# ANALYSIS
# --------------------------

def analyse(df):

    results = []

    for ticker in df.columns.levels[0]:

        data = df[ticker].dropna()

        if len(data) < 200:
            continue

        data["SMA20"] = data.Close.rolling(20).mean()
        data["SMA50"] = data.Close.rolling(50).mean()
        data["SMA200"] = data.Close.rolling(200).mean()

        data = data.dropna()

        y = data.iloc[-2]
        t = data.iloc[-1]
        p = data.iloc[-3]

        signals = []

        if y.Close <= y.SMA20 and t.Close > t.SMA20:
            signals.append("SMA20")

        if y.Close <= y.SMA50 and t.Close > t.SMA50:
            signals.append("SMA50")

        if y.SMA50 <= y.SMA200 and t.SMA50 > t.SMA200:
            signals.append("GoldenCross")

        high20 = data.Close.tail(20).max()

        if t.Close >= high20:
            signals.append("Breakout")

        avg_vol = data.Volume.tail(20).mean()

        if t.Volume > avg_vol * 1.5:
            signals.append("Volume")

        slope_y = y.SMA20 - p.SMA20
        slope_t = t.SMA20 - y.SMA20

        if slope_t > slope_y and slope_t > 0:
            signals.append("TrendAccel")

        if signals:

            results.append({
                "ticker":ticker,
                "close":float(t.Close),
                "signals":signals
            })

    return results


# --------------------------
# MAIN
# --------------------------

def main():

    tickers = get_asx200()

    market = yf.download(INDEX, period="3mo", interval="1d", progress=False)

    market_return = (market.Close.iloc[-1] / market.Close.iloc[-30]) - 1

    df = yf.download(
        tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        progress=False
    )

    results = analyse(df)

    if not results:
        print("No signals")
        return

    results.sort(key=lambda x: len(x["signals"]), reverse=True)

    top = results[:10]

    message = "📊 ASX Momentum Scanner\n\n🏆 Top Opportunities\n\n"

    rank = 1

    for r in top:

        message += (
            f"{rank}. {r['ticker']}\n"
            f"Signals: {', '.join(r['signals'])}\n"
            f"Close: {r['close']:.2f}\n\n"
        )

        rank += 1

    send(message)


if __name__ == "__main__":
    main()
