import yfinance as yf
import pandas as pd

from consts import *

def parse(start="2014-09-17"):
    # --- Download data ---
    df_btc = yf.download("BTC-USD", start=start, progress=False)
    df_gold = yf.download("GC=F", start=start, progress=False)

    # --- Preprocess data ---
    df_btc, df_gold = preprocess(df_btc, df_gold)
    df = pd.merge(df_btc, df_gold, on="Date", how="left") # Слияние датафреймов по датам

    # Gold in free days
    df["gold_Price"] = df["gold_Price"].ffill().bfill()
    df["BTC_Price"] = df["BTC_Price"].ffill().bfill()
    df["BTC_Volume"] = df["BTC_Volume"].fillna(0)

    # --- Calculate metrics ---
    df["gold price"] = df["BTC_Price"] / df["gold_Price"]
    df["demand"] = df["BTC_Volume"]
    df["inflation"] = (100 * df["gold_Price"].pct_change(periods=365)).fillna(0)

    # --- End ---
    res = df[
        [
            "Date",
            "gold price",
            "demand",
            "inflation",
        ]
    ].rename(columns={"Date": "date"})
    return res

def preprocess(df_btc, df_gold):
    # Сбрасываем индекс, чтобы дата стала обычной колонкой
    df_btc = df_btc.reset_index()
    df_gold = df_gold.reset_index()

    # В новых версиях yfinance колонки могут иметь мульти-индекс (MultiIndex). 
    # Сплющиваем их (оставляем только верхний уровень - Close, Volume и т.д.), чтобы не было ошибок
    if isinstance(df_btc.columns, pd.MultiIndex):
        df_btc.columns = df_btc.columns.get_level_values(0)
    if isinstance(df_gold.columns, pd.MultiIndex):
        df_gold.columns = df_gold.columns.get_level_values(0)

    # Оставляем только нужные колонки и переименовываем их
    df_btc = df_btc[["Date", "Close", "Volume"]].rename(
        columns={"Close": "BTC_Price", "Volume": "BTC_Volume"}
    )
    df_gold = df_gold[["Date", "Close"]].rename(columns={"Close": "gold_Price"})

    # Очищаем информацию о часовых поясах из дат (чтобы слияние прошло успешно)
    df_btc["Date"] = pd.to_datetime(df_btc["Date"]).dt.tz_localize(None)
    df_gold["Date"] = pd.to_datetime(df_gold["Date"]).dt.tz_localize(None)

    return df_btc, df_gold

def main():
    res = parse()
    res.to_csv(DATASET_DIR, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
