# Binance Trading Bot
This trading bot was built with the Binance official Binance Python SDK. 



# Features & functionality
1. Real-time cryypto price trackng and indicators calculation.
2. Automatically make future limit orders based on the value of indicators.
    - Indicators include: MACD, EMA, RSI, EMV
3. Automatically monitor if a limit order is successfully made.
4. Automatically execute STOP LOSS and TAKE PROFIT according to the program configs.




# Beginning

## Make sure you have the follwoing packages installed on your machine:
1. APScheduler==3.6.3
2. binance-futures==1.1.0
3. certifi==2020.4.5.2
4. chardet==3.0.4
5. idna==2.9
6. pytz==2020.1
7. requests==2.23.0
8. six==1.15.0
9. tzlocal==2.1
10. urllib3==1.25.9
11. websocket-client==0.57.0


## Configs:
1. Replace your own Binance API credential in "start_trading.py"
2. Adjust the Config data based on your kowledge and risk control.


# Run

## python3 start_trading.py


## License
MIT
