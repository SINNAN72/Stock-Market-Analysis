import os
import csv
import matplotlib.pyplot as plt
import statistics as stats
import yfinance as yf
import requests

def fetch_data(market="stock", symbol=None, file_path=None):
    if market == "stock_csv":
        prices = []
        asset_name = os.path.basename(file_path).replace("_Prices.csv", "")
        
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            next(reader)
            
            for row in reader:
                prices.append(float(row[1]))
        
        return prices, asset_name

    elif market == "yahoo":
        data = yf.download(symbol, period="120d", interval="1d")
        prices = data["Close"].squeeze().dropna().tolist()
        return prices, symbol
    
    elif market == "crypto":
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "limit": 120}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        prices = [float(candle[4]) for candle in data]
        return prices, symbol
    
    else:
        raise ValueError("Invalid market type!")
    

def moving_average(data, window_size):
    averages = []
    
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        avg = sum(window) / window_size
        averages.append(avg)
        
    return averages

def detect_trend(averages):
    if len(averages) < 2:
        return "Not enough data to determine trend"
    
    last = averages[-1]
    previous = averages[-2]
    
    if last > previous:
        return "Upward Trend"   
    elif last < previous:
        return "Downward Trend"
    else:
        return "Sideways"
    
def trend_strength(averages):
    if len(averages) < 2:
        return "Not enough data to determine trend strength"
    
    diff = abs(averages[-1] - averages[-2])
    change_percent = (diff / averages[-2]) * 100
    
    if change_percent < 0.3:
        return "Weak Trend"
    elif change_percent < 1.0:
        return "Moderate Trend"
    else:
        return "Strong Trend"
    
def volatility(data, window_size):
    vol = []
    
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        vol.append(stats.stdev(window))
        
    return vol

def signal(short_ma, long_ma, trend, volatility_value, strength, min_vol=1.0):
    if len(short_ma) == 0 or len(long_ma) == 0:
        return "Not enough data for signal"
    
    if volatility_value < min_vol:
        return "NO TRADE (Low Volatility)"

    if short_ma[-1] > long_ma[-1] and trend == "Upward Trend":
        if strength == "Strong Trend":
            return "STRONG BUY"
        else:
            return "WEAK BUY"

    if short_ma[-1] < long_ma[-1] and trend == "Downward Trend":
        if strength == "Strong Trend":
            return "STRONG SELL"
        else:
            return "WEAK SELL"

    return "HOLD"

def buy_sell(short_ma, long_ma, short_w, long_w):
    buy_points = []
    sell_points = []
    
    start = max(short_w, long_w) - 1
    
    for i in range(start, len(short_ma)):
        prev_short = short_ma[i - 1]
        prev_long = long_ma[i - 1 - (long_w - short_w)]
        
        curr_short = short_ma[i]
        curr_long = long_ma[i - (long_w - short_w)]
        
        if prev_short <= prev_long and curr_short > curr_long:
            buy_points.append(i)
        elif prev_short >= prev_long and curr_short < curr_long:
            sell_points.append(i)
            
    return buy_points, sell_points

def signal_accuracy(data, buy_points, sell_points, lookahead=3):
    correct = 0
    total = 0
    for i in buy_points:
        if i + lookahead <len(data):
            total += 1
            if data[i + lookahead] > data[i]:
                correct += 1     
    
    for i in sell_points:
        if i + lookahead < len(data):
            total += 1
            if data[i + lookahead] <data[i]:
                correct += 1
    
    if total ==0:
        return 0.0
    
    return (correct / total) * 100
    
def plot_chart(data, ma_short, ma_long, short_w, long_w, buy, sell, stock_name):
    plt.figure(figsize = (12, 6))
    plt.plot(data, label =f"{stock_name} Prices", alpha = 0.6)
    plt.plot(range(short_w - 1, len(data)), ma_short, label = f"{short_w}-Day Moving Average")
    plt.plot(range(long_w - 1, len(data)), ma_long, label = f"{long_w}-Day Moving Average")
    plt.scatter(buy, [data[i] for i in buy], marker = '^', color = 'g', label = 'BUY', s = 100)
    plt.scatter(sell, [data[i] for i in sell], marker = 'v', color = 'r', label = 'SELL', s = 100)
    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.title(f"\"{stock_name}\" Market Trend Analysis")
    plt.legend()
    plt.grid(True)
    plt.show()

def export_result(data, short_ma, long_ma, short_w, long_w, filename="trend_analysis.csv"):
    with open(filename, "w", newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(["Day", "Price", "Short_MA", "Long_MA"])
        
        for i in range(len(data)):
            s = short_ma[i - (short_w - 1)] if i >= (short_w - 1) else ""
            l = long_ma[i - (long_w - 1)] if i >= (long_w - 1) else ""
            writer.writerow([i, data[i], s, l])

if __name__ == "__main__":
    data, stock_name = fetch_data(market="stock_csv", file_path="data/TSLA_Prices.csv") #data reading
    data, stock_name = fetch_data(market="yahoo", symbol="TSLA")
    data, stock_name = fetch_data(market="crypto", symbol="BTCUSDT")
    
    short_window = 7 # window sizes
    long_window = 14
    
    short_ma = moving_average(data, short_window) # indicators
    long_ma = moving_average(data, long_window)
    
    average = moving_average(data, window_size=5)

    volatility_values = volatility(data, window_size=5) # volatility
    latest_volatility = volatility_values[-1] 
    
    market_trend = detect_trend(long_ma) # trend detection
    strength = trend_strength(long_ma)

    signal_result = signal(short_ma, long_ma, market_trend, latest_volatility, strength) # signal 
    
    buy, sell = buy_sell(short_ma, long_ma, short_window, long_window) # buy/sell
    
    accuracy = signal_accuracy(data, buy, sell)
    
    # export_result(data, short_ma, long_ma, short_window, long_window)
    
    print("Market Trend:", market_trend)    # Outputs
    print("Trend Strength:", strength)
    print("Latest Volatility Values:", round(latest_volatility, 2))
    print("Trading Signal:", signal_result)
    print("signal Accuracy (%): ", round(accuracy, 2))
    
    # print("Analysis exported to CSV file.")
    
    plot_chart(data, short_ma, long_ma, short_window, long_window, buy, sell, stock_name) #Graph plotting