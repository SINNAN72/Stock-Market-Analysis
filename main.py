import csv
import matplotlib.pyplot as plt
import statistics as stats

def read_data():
    data = []

    with open("data/TSLA_Prices.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)
        
        for row in reader:
            data.append(float(row[1]))
            
    return data

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

def signal(short_ma, long_ma):
    if len(short_ma) == 0 or len(long_ma) == 0:
        return "Not enouhgh data for signal"
    
    if short_ma[-1] > long_ma[-1]:
        return "BUY Signal"
    if short_ma[-1] < long_ma[-1]:
        return "SELL Signal"
    else:
        return "HOLD"
    
    
def ploting(data, ma_short, ma_long):
    plt.figure(figsize = (12, 6))
    plt.plot(data, label = "Stock Prices", alpha = 0.6)
    plt.plot(range(len(ma_short)), ma_short, label = "5-Day Moving Average")
    plt.plot(range(len(ma_long)), ma_long, label = "10-Day Moving Average")

    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.title("Stock Trend Analysis")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    data = read_data()
    average = moving_average(data, window_size=3)
    short_ma = moving_average(data, window_size=3)
    long_ma = moving_average(data, window_size=6)
    signal_result = signal(short_ma, long_ma)
    trend = detect_trend(average)
    strength = trend_strength(average)
    ploting(data, short_ma, long_ma)
    print("5-Day Moving Averages:", average)
    print("Current Trend:", trend)
    print("Trend Strength:", strength)
    print("Trading Signal:", signal_result)