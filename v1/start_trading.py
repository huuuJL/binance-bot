from fastTradeV1 import fastTrade
from binance.client import Client
import multiprocessing
import threading

config = {
    'paried_symbol': 'BTCUSDT',
    'asset_symbol': 'USDT',
    'starting_asset_value': 19.85,
    'api_key': 'N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM',
    'api_secret': 'm0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI',
    'stop_loss_ratio': round(2/100, 4),
    'order_timeout': 15000,         # 1000ms = 1ssecond
    'price_anneal': 0.003,
    'target_profit': {
        'level1': round(0.58/100, 4),
        'level2': round(0.78/100, 4),
        'level3': round(1.08/100, 4)
    },
    'interval': Client.KLINE_INTERVAL_1MINUTE,
    'leverage': 8,
    'initial_data_num': 150,

    'indicator_config':{
        'macd': {
        'fastperiod': 12,
        'slowperiod': 26,
        'signalperiod': 9
    } ,

        'rsi': {
            'rsi1': 6,
            'rsi2': 12,
            'rsi3': 24
        },

        'ema': {
            'ema1': 7,
            'ema2': 30,
            'ema3': 150
        },

        'emv': {
            'period': 4,
            'divisor': 10000,
        }
    }
}

'''
# write/read: https://stackoverflow.com/questions/30294146/fastest-way-to-process-a-large-file?answertab=votes#tab-top,
              https://towardsdatascience.com/optimized-i-o-operations-in-python-194f856210e0
# multiprocessing: https://stackoverflow.com/questions/48623544/executing-two-class-methods-at-the-same-time-in-python 
'''
if __name__ == "__main__":  
    t1 = fastTrade(config)
    t1.run()
