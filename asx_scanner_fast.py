from __future__ import annotations
from io import StringIO

import os
import re
import traceback
import pandas as pd
import yfinance as yf
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

INDEX = "STW.AX"

FALLBACK_TICKERS = [
    "CBA.AX", "BHP.AX", "CSL.AX", "WES.AX", "MQG.AX",
    "NAB.AX", "WBC.AX", "ANZ.AX", "FMG.AX", "TLS.AX",
    "WOW.AX", "COL.AX", "RIO.AX", "GMG.AX", "ALL.AX", 
    "DRO.AX", "ZIP.AX", "360.AX", "NEU.AX", "TLX.AX",
    "DMP.AX"
]


# --------------------------
# TELEGRAM
# --------------------------

def send(msg: str) -> None:
    if not TOKEN or not CHAT:
        print("Telegram token or chat ID not set.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT,
            "text": msg
        },
        timeout=30
    )
    response.raise_for_status()


# --------------------------
# ASX200 TICKERS
# --------------------------

def get_valid_asx_codes() -> set[str]:
    url = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    # ASX CSV has a preamble line before the real header
    df = pd.read_csv(StringIO(response.text), skiprows=1)

    # Normalise column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    print("ASX listed companies CSV columns:", list(df.columns))

    # Find the ASX code column flexibly
    code_col = None
    for col in df.columns:
        if "asx" in col and "code" in col:
            code_col = col
            break

    if code_col is None:
        raise ValueError(
            f"Could not find ASX code column. Columns found: {list(df.columns)}"
        )

    codes = (
        df[code_col]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .tolist()
    )

    print(f"Valid ASX codes loaded: {len(codes)}")
    print("Sample ASX codes:", codes[:10])

    return set(codes)


def get_asx200() -> list[str]:
    basket_url = (
        "https://www.ssga.com/au/en_gb/institutional/"
        "library-content/products/fund-data/etfs/apac/basket-au-en-stw.csv"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    try:
        print("Fetching STW basket...")

        response = requests.get(basket_url, headers=headers, timeout=30)
        response.raise_for_status()

        lines = response.text.splitlines()

        header_idx = None
        for i, line in enumerate(lines):
            cleaned = line.lstrip("\ufeff").strip().upper()
            if "TICKER" in cleaned and "SEDOL" in cleaned and "ISIN" in cleaned:
                header_idx = i
                print(f"Found STW holdings header on line {i}: {line[:160]}")
                break

        if header_idx is None:
            raise ValueError("Holdings header not found")

        holdings_csv = "\n".join(lines[header_idx:])
        df = pd.read_csv(StringIO(holdings_csv))

        df.columns = [str(c).strip().upper() for c in df.columns]

        if "TICKER" not in df.columns:
            raise ValueError(f"STW basket CSV missing TICKER column. Columns found: {list(df.columns)}")

        raw_tickers = (
            df["TICKER"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
            .tolist()
        )

        print(f"Raw tickers parsed: {len(raw_tickers)}")
        print("Sample raw tickers:", raw_tickers[:10])

        cleaned_tickers = []
        for t in raw_tickers:
            # Remove leading apostrophes, e.g. "'WEB" -> "WEB"
            code = t.lstrip("'").strip()

            # If a suffix exists, keep first token only, e.g. "CBA AU" -> "CBA"
            code = code.split()[0]

            # Remove any remaining non-alphanumeric characters
            code = re.sub(r"[^A-Z0-9]", "", code)

            if re.fullmatch(r"[A-Z0-9]{2,5}", code):
                cleaned_tickers.append(code)

        print(f"Ticker format valid: {len(cleaned_tickers)}")
        print("Sample cleaned tickers:", cleaned_tickers[:10])

        valid_codes = get_valid_asx_codes()
        tickers = [t for t in cleaned_tickers if t in valid_codes]

        print(f"Tickers after ASX validation: {len(tickers)}")

        if len(tickers) < 150:
            raise ValueError(f"Too few valid tickers parsed from STW basket CSV: {len(tickers)}")

        final_tickers = sorted({f"{t}.AX" for t in tickers})
        print(f"Final ASX200 ticker count: {len(final_tickers)}")

        return final_tickers

    except Exception as e:
        print(f"Primary ticker source failed: {e}")
        print(f"Using fallback list ({len(FALLBACK_TICKERS)} tickers)")
        return FALLBACK_TICKERS


# --------------------------
# ANALYSIS
# --------------------------

def analyse(df: pd.DataFrame) -> list[dict]:
    results = []

    for ticker in df.columns.levels[0]:
        data = df[ticker].dropna().copy()

        if len(data) < 200:
            continue

        data["SMA20"] = data["Close"].rolling(20).mean()
        data["SMA50"] = data["Close"].rolling(50).mean()
        data["SMA200"] = data["Close"].rolling(200).mean()

        data = data.dropna()

        if len(data) < 3:
            continue

        y = data.iloc[-2]
        t = data.iloc[-1]
        p = data.iloc[-3]

        signals = []

        if y["Close"] <= y["SMA20"] and t["Close"] > t["SMA20"]:
            signals.append("SMA20")

        if y["Close"] <= y["SMA50"] and t["Close"] > t["SMA50"]:
            signals.append("SMA50")

        if y["SMA50"] <= y["SMA200"] and t["SMA50"] > t["SMA200"]:
            signals.append("GoldenCross")

        high20 = data["Close"].tail(20).max()
        if t["Close"] >= high20:
            signals.append("Breakout")

        avg_vol = data["Volume"].tail(20).mean()
        if t["Volume"] > avg_vol * 1.5:
            signals.append("Volume")

        slope_y = y["SMA20"] - p["SMA20"]
        slope_t = t["SMA20"] - y["SMA20"]

        if slope_t > slope_y and slope_t > 0:
            signals.append("TrendAccel")

        if signals:
            results.append({
                "ticker": ticker,
                "close": float(t["Close"]),
                "signals": signals
            })

    return results


# --------------------------
# MAIN
# --------------------------

def main() -> None:
    tickers = get_asx200()
    print(f"Scanning {len(tickers)} tickers")

    market = yf.download(
        INDEX,
        period="3mo",
        interval="1d",
        progress=False,
        auto_adjust=False
    )

    if market.empty or len(market) < 30:
        raise ValueError("Not enough market data for index.")

    print("Downloading price data...")

    df = yf.download(
        tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        raise ValueError("No stock data downloaded.")

    valid_tickers = []
    failed_tickers = []

    for ticker in tickers:
        try:
            if ticker in df.columns.levels[0]:
                data = df[ticker].dropna()
                if len(data) > 0:
                    valid_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(ticker)
        except Exception:
            failed_tickers.append(ticker)

    print(f"Price data success: {len(valid_tickers)}")
    print(f"Price data failures: {len(failed_tickers)}")

    if failed_tickers:
        print("Failed tickers sample:", failed_tickers[:10])

    results = analyse(df)

    if not results:
        print("No signals")
        return

    results.sort(key=lambda x: len(x["signals"]), reverse=True)
    top = results[:10]

    print("Scan summary:")
    print(f"Signals detected: {len(results)}")
    print(f"Top opportunities returned: {len(top)}")

    message = "📊 ASX Momentum Scanner\n\n🏆 Top Opportunities\n\n"

    for rank, r in enumerate(top, start=1):
        message += (
            f"{rank}. {r['ticker']}\n"
            f"Signals: {', '.join(r['signals'])}\n"
            f"Close: {r['close']:.2f}\n\n"
        )

    send(message)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FATAL ERROR:")
        print(str(e))
        traceback.print_exc()
        raise
