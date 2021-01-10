import logging
import asyncio
from binance.client import Client
from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *
import time
import threading
import talib as ta
import numpy as np
from datetime import datetime
import curses
import json
import os
from os import path
from talipp.ohlcv import OHLCVFactory
import talipp.indicators as talippIndicator

def utc_2_datetime(timestamp):
    return '{}({})'.format(datetime.fromtimestamp(int(timestamp)), (str(time.tzname[-1])))

def calculate_ema(np_price_list, indicator_config):
    '''
    https://blog.csdn.net/qq_37174526/article/details/92414970
    
    # ema1 = ta.EMA(np_price_list, indicator_config['ema']['ema1'])
    # ema2 = ta.EMA(np_price_list, indicator_config['ema']['ema2'])
    # ema3 = ta.EMA(np_price_list, indicator_config['ema']['ema3'])
    '''

    ema_task_1 = MyThread(ta.EMA, args=(np_price_list, indicator_config['ema']['ema1']))
    ema_task_2 = MyThread(ta.EMA, args=(np_price_list, indicator_config['ema']['ema2']))
    ema_task_3 = MyThread(ta.EMA, args=(np_price_list, indicator_config['ema']['ema3']))
    ema_task_1.start()
    ema_task_2.start()
    ema_task_3.start()
    ema_task_1.join()
    ema_task_2.join()
    ema_task_3.join()

    ema1 = ema_task_1.get_result()
    ema2 = ema_task_2.get_result()
    ema3 = ema_task_2.get_result()
    return [ema1, ema2, ema3]

def calculate_macd(np_price_list, indicator_config):
    macd, macdsignal, macdhist = ta.MACD(np_price_list, 
                                    fastperiod=indicator_config['macd']['fastperiod'], 
                                    slowperiod=indicator_config['macd']['slowperiod'], 
                                    signalperiod=indicator_config['macd']['signalperiod'])
    return [macd, macdsignal, macdhist]

def calculate_rsi(np_price_list, indicator_config):
    '''
    https://blog.csdn.net/qq_37174526/article/details/92414970      
    
    # rsi_1 = ta.RSI(np_price_list, self.indicator_config['rsi']['rsi1'])
    # rsi_2 = ta.RSI(np_price_list, self.indicator_config['rsi']['rsi2'])
    # rsi_3 = ta.RSI(np_price_list, self.indicator_config['rsi']['rsi3'])  
    '''
    res_task_1 = MyThread(ta.RSI, args=(np_price_list, indicator_config['rsi']['rsi1']))
    res_task_2 = MyThread(ta.RSI, args=(np_price_list, indicator_config['rsi']['rsi2']))
    res_task_3 = MyThread(ta.RSI, args=(np_price_list, indicator_config['rsi']['rsi3']))
    res_task_1.start()
    res_task_2.start()
    res_task_3.start()
    res_task_1.join()
    res_task_2.join()
    res_task_3.join()

    res1 = res_task_1.get_result()
    res2 = res_task_2.get_result()
    res3 = res_task_2.get_result()
    return [res1, res2, res3]

def calculate_emv(open, high, low, close, volume, indicator_config):
    period = indicator_config['emv']['period']
    divisor = indicator_config['emv']['divisor']

    ohlcv = OHLCVFactory.from_matrix2(
        [
        open,
        high,
        low,
        close,
        volume
        ]
    )

    return talippIndicator.EMV(period, divisor, ohlcv)[-1]

def get_indicators(kline_dict, indicator_config):

    open_price_list = np.array(kline_dict['open_price_list']).astype(float)
    high_price_list = np.array(kline_dict['high_price_list']).astype(float)
    low_price_list = np.array(kline_dict['low_price_list']).astype(float)
    close_price_list = np.array(kline_dict['close_price_list']).astype(float)
    vol_list = np.array(kline_dict['volume_list']).astype(float)
    

    MACD_task = MyThread(calculate_macd, args=(close_price_list, indicator_config))
    EMA_task = MyThread(calculate_ema, args=(close_price_list, indicator_config))
    RSI_task = MyThread(calculate_rsi, args=(close_price_list, indicator_config))
    EMV_task = MyThread(calculate_emv, args=(open_price_list, high_price_list, low_price_list, close_price_list, vol_list, indicator_config))

    # indicator_task_list = [MACD_task, EMA_task, RSI_task, EMV_task]
    indicator_task_list = [MACD_task, EMA_task, RSI_task, EMV_task]

    for task in indicator_task_list:
        task.start()

    for task in indicator_task_list:
        task.join()

    MACD_result = MACD_task.get_result()
    EMA_result = EMA_task.get_result()
    RSI_result = RSI_task.get_result()
    EMV_result = RSI_task.get_result()


    return MACD_result, EMA_result, RSI_result, EMV_result[-1]

def current_date_time():
    return '{}({})'.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), (str(time.tzname[-1])))

def current_utc_time():
    return time.time()

def convert_object_to_string(object):
    object_dict = (object.__dict__) 
    string = '====================================================================\n'
    for key in object_dict.keys():
        string += '{}: {}\n'.format(key, object_dict[key])
    return string

def put_to_log(content, path):
    '''
    https://www.guru99.com/reading-and-writing-files-in-python.html
    '''
    try:
        f=open(path, "a+")
        f.write(content)
        f.close()
    except Exception as e:
        print("Logging for {} failed: {}".format(content, e))

class MyThread(threading.Thread):
    '''
    https://blog.csdn.net/qq_37174526/article/details/92414970
    '''
    def __init__(self, func, args):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

class positionStatus:
    def __init__(self, paired_symbol):
        self.paired_symbol = paired_symbol

        self.position_object = Position()
        # self.order_update_object = 

        self.order_status = None
        self.order_side = None
        self.order_amount = None
        self.order_cumulativeFilledQty = None

        self.position_last_update_time = None
        self.order_last_update_time = None

class fastTrade:
    def __init__(self, config):

        self.__paried_symbol = config['paried_symbol']
        self.__asset_symbol = config['asset_symbol']
        self.__starting_asset_value = config['starting_asset_value']
        self.__api_key = config['api_key']
        self.__api_secret = config['api_secret']
        self.__interval = config['interval']
        self.__leverage = config['leverage']
        self.__initial_data_num = config['initial_data_num']
        self.__acc_profit = 0
        self.__price_anneal = config['price_anneal']
        self.__order_timeout = config['order_timeout']
        self.__first_order = True
        self.indicator_config = config['indicator_config']
        self.position_status = positionStatus(self.__paried_symbol)


        self.__recommendation_log_path = None
        self.__order_log_path = None
        self.__error_log_path = None
        self.__position_log_path = None
        self.__profit_log_path = None

        self.__comission_rate = 0.0002 + 0.0004 + 0.0002

        self.__latest_data_update_timestamp = 0
        self.__latest_data_analysis_timestamp = 0
        self.__latest_depth_update_timestamp = 0

        self.order_update_list = []
        self.account_update_list = []
        self.depth_object = None
        
        self.margin = '===================================================================='


        self.target_profit_dict = config['target_profit']
        self.__stop_loss_ratio = config['stop_loss_ratio']

        self.__level_1_target_proofit = self.target_profit_dict['level1']
        self.__level_2_target_proofit = self.target_profit_dict['level2']
        self.__level_3_target_proofit = self.target_profit_dict['level3']

        self.indicator_dict = dict()

        self.finished_position_dict = {
            '''
            'uniqueOrderId': {
                'side': 'SIDE',
                'entryPrice': -99999,
                'exitPrice': -99999,
                'quantity': 0,
                'relatedOrderID': {}
            }
            '''
        }
        

        
        self.current_position_dict = {}
        '''
        'uniqueOrderId': {
                            'uniqueOrderId': None
                            'level': 1, 2, or 3
                            'positionSide': 'SIDE',
                            'trigeredPrice': -99999
                            'entryPrice': -99999,
                            'exitPrice': -99999,
                            'quantity': 0,
                            'relatedOrderID': {}
                            'comission': 999
                            }
                        ...
        '''


        self.current_recommendation = {
            'short': {
                'updated_time': 0,
                'level': 0,
                'price': None
            },

            'long': {
                'updated_time': 0,
                'level': 0,
                'price': None
            }
        }


        # Need to be updated automatically
        self.client = None  
        self.request_client = None
        self.listen_key = None
        self.exchange_info = None
        self.paired_asset_info = None

        self.account_info = None

        self.sub_client = None

        

        self.kline_info = {
            'kline_list': {
                'open_price_list': [],
                'high_price_list': [],
                'low_price_list': [],
                'close_price_list': [],
                'quoteAssetVolume_list': [],
                'volume_list': [],
                'takerBuyBaseAssetVolume_list': [],
                'takerBuyQuoteAssetVolume_list': [],
                'numTrades_list': []
            },
            'latest_time': 0
        }

        '''
            "pricePrecision": 5,  // 价格小数点位数
            "quantityPrecision": 0,  // 数量小数点位数
            "baseAssetPrecision": 8,  // 标的资产精度
            "quotePrecision": 8,  // 报价资产精度
        '''

        self.__pricePrecision = None
        self.__quantityPrecision = None
        self.__baseAssetPrecision = None
        self.__quotePrecision = None

        # self.__asset_balance = 0
        # self.__remaining = 0

    def update_config_info(self):
        if self.sub_client != None:
            self.sub_client.unsubscribe_all()
        self.update_listen_key()  
        self.update_client()
        self.update_exchange_info()
        self.update_account_info() 
        self.get_historical_kline()
        print('========== Succeed updating trading config ==========')
    
    def make_dir(self):
        '''
        https://www.guru99.com/reading-and-writing-files-in-python.html
        '''

        try:
            current_time = current_utc_time()
            folder_name = str(int(current_time))
            folder_path = 'logs/' + self.__paried_symbol + '/' + folder_name
            self.__recommendation_log_path = folder_path + "/recommendation.txt"
            self.__order_log_path = folder_path + "/order.txt"
            self.__error_log_path = folder_path + "/error.txt"
            self.__position_log_path = folder_path + "/position.txt"
            self.__profit_log_path = folder_path + "/profit.txt"

            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            if not os.path.exists('logs/' + self.__paried_symbol):
                os.mkdir('logs/' + self.__paried_symbol)
            
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            

            current_datetime = utc_2_datetime(current_time)
            recommendation_logs = open(self.__recommendation_log_path,"w+")
            recommendation_logs.write("This recommendation log was created at UTC: {}({}).\n".format(current_time, current_datetime))
            recommendation_logs.close()

            order_logs = open(self.__order_log_path,"w+")
            order_logs.write("This order log was created at UTC: {}({}).\n".format(current_time, current_datetime))
            order_logs.close()

            error_logs = open(self.__error_log_path, "w+")
            error_logs.write("This error log was created at UTC: {}({}).\n".format(current_time, current_datetime))
            error_logs.close()

            error_logs = open(self.__position_log_path, "w+")
            error_logs.write("This position log was created at UTC: {}({}).\n".format(current_time, current_datetime))
            error_logs.close()

            error_logs = open(self.__profit_log_path, "w+")
            error_logs.write("This profit log was created at UTC: {}({}).\n".format(current_time, current_datetime))
            error_logs.close()
            
        except Exception as e:
            print("An error occurs while making log directory: ", e)
            return False
        
        else:
            return True
    
    def update_parired_asset_info(self):
        """
        https://binance-docs.github.io/apidocs/futures/cn/#0f3f2d5ee7
        https://www.w3schools.com/python/ref_func_hasattr.asp
        """
        for item in self.exchange_info.symbols:
            # PrintMix.print_data(item)
            if ((hasattr(item, 'contractType')) and (hasattr(item, 'symbol')) and (hasattr(item, 'pair'))):
                if ((item.pair == self.__paried_symbol) and (item.symbol == self.__paried_symbol) and (item.contractType == "PERPETUAL")):
                    # PrintMix.print_data(item)
                    self.paired_asset_info = item 

                    self.__pricePrecision = item.pricePrecision
                    self.__quantityPrecision = item.quantityPrecision
                    self.__baseAssetPrecision = item.baseAssetPrecision
                    self.__quotePrecision = item.quotePrecision

                    break
        if self.paired_asset_info == None:
            raise Exception('\nInvalid symbol: {}\n'.format(self.__paried_symbol))
        else:
            self.update_parired_asset_info()

        print('\n========== Succeed updating paired asset info ==========\n')

    def update_exchange_info(self):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#0f3f2d5ee7
        '''
        result = self.request_client.get_exchange_information()
        self.exchange_info = result
        if self.exchange_info == None:
            raise Exception('\nFailed updating exchange info\n')
        print('========== Succeed updating exchage info ==========')
    
    def update_client(self):
        client = Client(self.__api_key, self.__api_secret)
        self.client = client
        if self.client == None:
            raise Exception('\nFailed updating client\n')
        print('========== Succeed updating client ==========')

    def update_listen_key(self):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#listenkey-user_stream-
        '''
        request_client = RequestClient(api_key=self.__api_key, secret_key=self.__api_secret)
        listen_key = request_client.start_user_data_stream()
        self.request_client = request_client
        self.listen_key = listen_key
        self.update_sub_client()
        print('========== Succeed updating listen key ==========')

    def extend_listen_key(self):
        '''
        Keep user data stream
        https://binance-docs.github.io/apidocs/futures/cn/#listenkey-user_stream2
        '''
        result = self.request_client.keep_user_data_stream()
        print("Trying to reconnect...\nResult: ", result)

    def update_account_info(self):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#v2-user_data-2
        '''
        result = self.request_client.get_account_information_v2()
        self.account_info = result
        if self.account_info == None:
            raise Exception('\nFailed updating account info\n')
        print('========== Succeed updating account info ==========')
    
    def update_sub_client(self):
        sub_client = SubscriptionClient(api_key=g_api_key, secret_key=g_secret_key)
        self.sub_client = sub_client
        if self.sub_client == None:
            raise Exception('\nFailed updating subscription client\n')
        print('========== Succeed updating subscription client ==========')

    def subscribe_book_depth_event(self):
        '''
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/example/websocket/subscribebookdepth.py
        https://binance-docs.github.io/apidocs/futures/cn/#6ae7c2b506
        '''

        logger = logging.getLogger("binance-futures")
        logger.setLevel(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

        def callback(data_type: 'SubscribeMessageType', event: 'any'):
            '''
            https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/orderbookevent.py
            '''
            if data_type == SubscribeMessageType.RESPONSE:
                pass
                # print("Event ID: ", event)
            elif  data_type == SubscribeMessageType.PAYLOAD:
                self.depth_object = event
                self.__latest_depth_update_timestamp = event.transactionTime
                # print("Event type: ", event.eventType)
                # print("Event time: ", event.eventTime)
                # print("transaction time: ", event.transactionTime)
                # print("Symbol: ", event.symbol)
                # print("first update Id from last stream: ", event.firstUpdateId)
                # print("last update Id from last stream: ", event.lastUpdateId)
                # print("last update Id in last stream: ", event.lastUpdateIdInlastStream)
                # print("=== Bids ===")
                # PrintMix.print_data(event.bids)
                # print("===================")
                # print("=== Asks ===")
                # PrintMix.print_data(event.asks)
                # print("===================")
            else:
                print("Unknown Data:")
            # print()


        def error(e: 'BinanceApiException'):
            print(e.error_code + e.error_message)
            log = "\n\n{}\nBook depth subscription error: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e.error_code + e.error_message, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

        # Valid limit values are 5, 10, or 20 
        self.sub_client.subscribe_book_depth_event(self.__paried_symbol.lower(), 20, callback, error, update_time=UpdateTime.FAST)
        #sub_client.subscribe_book_depth_event("btcusdt", 10, callback, error, update_time=UpdateTime.NORMAL)
        #sub_client.subscribe_book_depth_event("btcusdt", 10, callback, error)

    def subscribe_user_data_event(self):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#balance-position
        https://binance-docs.github.io/apidocs/futures/cn/#060a012f0b
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/accountupdate.py
        '''
        logger = logging.getLogger("binance-client")
        logger.setLevel(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        sub_client = self.sub_client

        def callback(data_type: 'SubscribeMessageType', event: 'any'):
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif  data_type == SubscribeMessageType.PAYLOAD:
                if (event.eventType == "ACCOUNT_UPDATE"):
                    for item in event.positions:
                        if (item.symbol == self.__paried_symbol):
                            self.account_update_list.append(event)
                            put_to_log('\n\nPosition updated: {}\n{}\n'.format(current_date_time(), convert_object_to_string(item)), self.__position_log_path)
                            self.position_status.position_last_update_time = event.transactionTime
                            # print('\n\n\n------------------')
                            # print('Position amount')
                            # print("Event Type: ", event.eventType)
                            # print("Event time: ", event.eventTime)
                            # print("Current time: ", current_date_time())
                            # print("Transaction time: ", event.transactionTime)
                            # print('------------------')
                            # print(PrintMix.print_data(self.position_status))
                            self.position_status.position_object = item
                            # print('----------    CHANGED TO    ----------')
                            # PrintMix.print_data(self.position_status)
                            # print('------------------\n')

                            # print("=== Balances ===")
                            # PrintMix.print_data(event.balances)
                            # print("================")
                            # print("=== Positions ===")
                            # PrintMix.print_data(event.positions)
                            # print("================")
                elif(event.eventType == "ORDER_TRADE_UPDATE"):
                    '''
                    https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/orderupdate.py
                    NEW
                    PARTIAL_FILL 部分成交
                    FILL 成交
                    CANCELED 已撤
                    CALCULATED
                    EXPIRED 订单失效
                    TRADE 交易
                    '''

                    if event.symbol == self.__paried_symbol:
                        self.order_update_list.append(event)
                        # print('------------------')
                        # print("Event Type: ", event.eventType)
                        # print("Event time: ", event.eventTime)
                        # print("Current time: ", current_date_time())
                        # print("Transaction Time: ", event.transactionTime)
                        # print('------------------')
                        # print(PrintMix.print_data(self.position_status))
                        self.position_status.order_status = event.orderStatus
                        self.position_status.order_cumulativeFilledQty = event.cumulativeFilledQty
                        self.position_status.order_amount = event.avgPrice
                        self.position_status.order_side = event.side
                        self.position_status.order_last_update_time = event.eventTime
                        # print('----------    CHANGED TO    ----------')
                        # PrintMix.print_data(self.position_status)
                        # print('------------------\n\n\n')


                        # print("Symbol: ", event.symbol)
                        # print("Client Order Id: ", event.clientOrderId)
                        # print("Side: ", event.side)
                        # print("Order Type: ", event.type)
                        # print("Time in Force: ", event.timeInForce)
                        # print("Original Quantity: ", event.origQty)
                        # print("Position Side: ", event.positionSide)
                        # print("Price: ", event.price)
                        # print("Average Price: ", event.avgPrice)
                        # print("Stop Price: ", event.stopPrice)
                        # print("Execution Type: ", event.executionType)
                        # print("Order Status: ", event.orderStatus)
                        # print("Order Id: ", event.orderId)
                        # print("Order Last Filled Quantity: ", event.lastFilledQty)
                        # print("Order Filled Accumulated Quantity: ", event.cumulativeFilledQty)
                        # print("Last Filled Price: ", event.lastFilledPrice)
                        # print("Commission Asset: ", event.commissionAsset)
                        # print("Commissions: ", event.commissionAmount)
                        # print("Order Trade Time: ", event.orderTradeTime)
                        # print("Trade Id: ", event.tradeID)
                        # print("Bids Notional: ", event.bidsNotional)
                        # print("Ask Notional: ", event.asksNotional)
                        # print("Is this trade the maker side?: ", event.isMarkerSide)
                        # print("Is this reduce only: ", event.isReduceOnly)
                        # print("stop price working type: ", event.workingType)
                        # print("Is this Close-All: ", event.isClosePosition)
                        # if not event.activationPrice is None:
                        #     print("Activation Price for Trailing Stop: ", event.activationPrice)
                        # if not event.callbackRate is None:
                        #     print("Callback Rate for Trailing Stop: ", event.callbackRate)
                elif(event.eventType == "listenKeyExpired"):
                    print("\nEvent: ", event.eventType)
                    print("Event time: ", event.eventTime)
                    print("CAUTION: YOUR LISTEN-KEY HAS BEEN EXPIRED!!!")
                    print("CAUTION: YOUR LISTEN-KEY HAS BEEN EXPIRED!!!")
                    print("CAUTION: YOUR LISTEN-KEY HAS BEEN EXPIRED!!!")
                    self.extend_listen_key()
                
            else:
                print("Unknown Data:")
            # print()

        def error(e: 'BinanceApiException'):
            # print(e.error_code + e.error_message)
            log = "\n\n{}\nUser data subscription error: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e.error_code + e.error_message, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

        sub_client.subscribe_user_data_event(self.listen_key, callback, error)

    def subscribe_candlestick_event(self):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#k-4
        or
        https://binance-docs.github.io/apidocs/futures/cn/#k-5
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/candlestickevent.py
        '''
        logger = logging.getLogger("binance-futures")
        logger.setLevel(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        sub_client = self.sub_client

        def callback(data_type: 'SubscribeMessageType', event: 'any'):
            if data_type == SubscribeMessageType.RESPONSE:
                pass
                # print("Event ID: ", event)
            elif  data_type == SubscribeMessageType.PAYLOAD:
                self.update_historical_kline(event)
                # print("Event type: ", event.eventType)
                # print("Event time: ", event.eventTime)
                # print("Symbol: ", event.symbol)
                # print("Data:")
                # PrintBasic.print_obj(event.data)
            else:
                print("Unknown Data:")
            # print()


        def error(e: 'BinanceApiException'):
            # print(e.error_code + e.error_message)
            log = "\n\n{}\nCandlestick subscription error: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e.error_code + e.error_message, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

        sub_client.subscribe_candlestick_event(self.__paried_symbol.lower(), self.__interval, callback, error)

    def update_historical_kline(self, event):
        '''
        https://binance-docs.github.io/apidocs/futures/cn/#k-4
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/candlestickevent.py
        event:
                Event type:  kline
                Event time:  1609506873291
                Symbol:  BLZUSDT
                Data:
                    close:0.06756
                    closeTime:1609506899999
                    firstTradeId:3634790
                    high:0.06758
                    ignore:0
                    interval:1m
                    isClosed:False
                    json_parse:<function Candlestick.json_parse at 0x107909d30>
                    lastTradeId:3634796
                    low:0.06751
                    numTrades:7
                    open:0.06758
                    quoteAssetVolume:746.46888
                    startTime:1609506840000
                    symbol:BLZUSDT
                    takerBuyBaseAssetVolume:0.0
                    takerBuyQuoteAssetVolume:0.0
                    volume:11054.0

        '''
        try:
            startTime = event.data.startTime
            isClosed = event.data.isClosed
            if isClosed:
                self.get_historical_kline()

            elif startTime - self.kline_info['updated_time'] < 60000:
                kline_info = self.kline_info.copy()
                kline_object = event.data
                kline_info['kline_list']['open_price_list'][-1] = float(kline_object.open)                                     # o
                kline_info['kline_list']['high_price_list'][-1] = float(kline_object.high)                                     # h
                kline_info['kline_list']['low_price_list'][-1] = float(kline_object.low)                                       # l
                kline_info['kline_list']['close_price_list'][-1] = float(kline_object.close)                                   # c
                kline_info['kline_list']['quoteAssetVolume_list'][-1] = float(kline_object.quoteAssetVolume)                       # vol(quoAsset)
                kline_info['kline_list']['volume_list'][-1] = float(kline_object.volume)                                       # vol
                kline_info['kline_list']['takerBuyBaseAssetVolume_list'][-1] = float(kline_object.takerBuyBaseAssetVolume)     # takerBuyBaseAssetVolume
                kline_info['kline_list']['takerBuyQuoteAssetVolume_list'][-1] = float(kline_object.takerBuyQuoteAssetVolume)   # takerBuyQuoteAssetVolume
                kline_info['kline_list']['numTrades_list'][-1] = int(kline_object.numTrades)                                 # numTrades
                kline_info['updated_time'] = startTime

                self.kline_info = kline_info
            else:
                self.get_historical_kline()
    
            self.__latest_data_update_timestamp = event.eventTime
            
            # print(self.kline_info['kline_list']['close_price_list'][-10:])
        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while updating historical data: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

    def get_historical_kline(self):
        '''
        klines:
        close:347.15
        closeTime:1609496279999
        high:347.75
        ignore:0
        json_parse:<function Candlestick.json_parse at 0x10c8b41f0>
        low:347.06
        numTrades:298
        open:347.30
        openTime:1609496220000
        quoteAssetVolume:65901.36106
        takerBuyBaseAssetVolume:111.498
        takerBuyQuoteAssetVolume:38745.65489
        volume:189.645
        [
            [
                1499040000000,      // 开盘时间
                "0.01634790",       // 开盘价                         o
                "0.80000000",       // 最高价                         h
                "0.01575800",       // 最低价                         l
                "0.01577100",       // 收盘价(当前K线未结束的即为最新价)  c
                "148976.11427815",  // 成交量                         
                1499644799999,      // 收盘时间
                "2434.19055334",    // 成交额
                308,                // 成交笔数
                "1756.87402397",    // 主动买入成交量
                "28.46694368",      // 主动买入成交额
                "17928899.62484339" // 请忽略该参数
            ]
        ]
        '''

        try:
            klines = self.request_client.get_candlestick_data(symbol=self.__paried_symbol, interval=self.__interval,limit=self.__initial_data_num)
            # PrintBasic.print_obj(klines[-1])
            last_n = klines[((-1) * self.__initial_data_num):]
            kline_info = self.kline_info.copy()
            kline_info['kline_list'] = {
                'open_price_list': [],
                'high_price_list': [],
                'low_price_list': [],
                'close_price_list': [],
                'quoteAssetVolume_list': [],
                'volume_list': [],
                'takerBuyBaseAssetVolume_list': [],
                'takerBuyQuoteAssetVolume_list': [],
                'numTrades_list': []
            }
            kline_info['updated_time'] = last_n[-1].openTime

            for item in last_n:
                kline_info['kline_list']['open_price_list'].append(float(item.open))                                     # o
                kline_info['kline_list']['high_price_list'].append(float(item.high))                                     # h
                kline_info['kline_list']['low_price_list'].append(float(item.low))                                       # l
                kline_info['kline_list']['close_price_list'].append(float(item.close))                                   # c
                kline_info['kline_list']['quoteAssetVolume_list'].append(float(item.quoteAssetVolume))                   # vol(quoAsset)
                kline_info['kline_list']['volume_list'].append(float(item.volume))                                       # vol
                kline_info['kline_list']['takerBuyBaseAssetVolume_list'].append(float(item.takerBuyBaseAssetVolume))     # takerBuyBaseAssetVolume
                kline_info['kline_list']['takerBuyQuoteAssetVolume_list'].append(float(item.takerBuyQuoteAssetVolume))   # takerBuyQuoteAssetVolume
                kline_info['kline_list']['numTrades_list'].append(int(item.numTrades))                                 # numTrades

            self.kline_info = kline_info

            print('========== Succeed getting historical data ==========')
            # print(self.kline_info['kline_list']['close_price_list'])
        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while getting historical data: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)
    
    def start_subscribing(self):
        try:
            t1 = threading.Thread(target=self.subscribe_candlestick_event)
            t2 = threading.Thread(target=self.subscribe_user_data_event)
            # t3 = threading.Thread(target=self.subscribe_book_depth_event)

            # subs_task_list = [t1, t2, t3]
            subs_task_list = [t1, t2]

            for task in subs_task_list:
                task.start()
            
            for task in subs_task_list:
                task.join()
        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while starting subscription: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)
    
    def start_handler(self):
        time.sleep(3)
        try:
            t1 = threading.Thread(target=self.order_handler)
            t2 = threading.Thread(target=self.position_handler)
            # t3 = threading.Thread(target=self.position_status_handler)

            handler_task_list = [t1, t2]

            for task in handler_task_list:
                task.start()
            
            for task in handler_task_list:
                task.join()

        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while starting the handler: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

    def get_recommendation(self, MACD_dict, EMA_dict, RSI_dict):
        level = 0
        side = None

        
        try:
            # Long
            if ( ( EMA_dict['ema2'][-1] > EMA_dict['ema3'][-1] ) and ( EMA_dict['ema2'][-2] < EMA_dict['ema3'][-2] ) ):
                side = 'long'
                level = 3
                return level, side
            
            # Short
            elif ( ( EMA_dict['ema2'][-1] < EMA_dict['ema3'][-1] ) and ( EMA_dict['ema2'][-2] > EMA_dict['ema3'][-2] ) ):
                side = 'short'
                level = 3
                return level, side
            
            # # Long
            # elif ( ( RSI_dict['rsi1'][-1] > 30 ) and ( RSI_dict['rsi1'][-2] < 30 ) and ( RSI_dict['rsi2'][-1] > 30 ) and ( RSI_dict['rsi2'][-2] < 30 ) and ( RSI_dict['rsi3'][-1] > 30 ) and ( RSI_dict['rsi3'][-2] < 30 ) ):
            #     side = 'long'
            #     level = 2
            #     return level, side

            # Short
            # elif ( ( RSI_dict['rsi1'][-1] < 70 ) and ( RSI_dict['rsi1'][-2] > 70 ) and ( RSI_dict['rsi2'][-1] < 70 ) and ( RSI_dict['rsi2'][-2] > 70 ) and ( RSI_dict['rsi3'][-1] < 70 ) and ( RSI_dict['rsi3'][-2] > 70 ) ):
            #     side = 'short'
            #     level = 2
            #     return level, side

            # Long
            elif ( ( ( EMA_dict['ema1'][-1] > EMA_dict['ema3'][-1] ) and ( EMA_dict['ema1'][-2] < EMA_dict['ema3'][-2] ) ) and ( ( ( MACD_dict['macd'][-1] - MACD_dict['macdsignal'][-1] ) >= 0 ) ) ):
                side = 'long'
                level = 2
                return level, side
            
            # Short
            elif ( ( ( EMA_dict['ema1'][-1] < EMA_dict['ema3'][-1] ) and ( EMA_dict['ema1'][-2] > EMA_dict['ema3'][-2] ) ) and ( ( ( MACD_dict['macd'][-1] - MACD_dict['macdsignal'][-1] ) <= 0 ) ) ):
                side = 'short'
                level = 2
                return level, side

            # Long
            elif ( ( ( EMA_dict['ema1'][-1] > EMA_dict['ema2'][-1] ) and ( EMA_dict['ema1'][-2] < EMA_dict['ema2'][-2] ) ) and ( ( ( MACD_dict['macd'][-1] - MACD_dict['macdsignal'][-1] ) >= 0 ) ) ):
                side = 'long'
                level = 1
                return level, side
            
            # Short
            elif ( ( ( EMA_dict['ema1'][-1] < EMA_dict['ema2'][-1] ) and ( EMA_dict['ema1'][-2] > EMA_dict['ema2'][-2] ) ) and ( ( ( MACD_dict['macd'][-1] - MACD_dict['macdsignal'][-1] ) <= 0 ) ) ):
                side = 'short'
                level = 1
                return level, side

        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while getting recommendations: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
            print(log)
            put_to_log(log, self.__error_log_path)

            return level, side
        
        else:
            # return 1, 'short'
            return level, side
    
    def start_analysing(self):
        while True:
            try:

                # print((self.current_recommendation['short']['updated_time']))
                
                if ((current_utc_time() - (self.current_recommendation['short']['updated_time'])) > 0.5):
                    self.current_recommendation['short'] = {
                                                                            'updated_time': 0,
                                                                            'level': 0,
                                                                            'price': None
                                                                        }

                if ((current_utc_time() - (self.current_recommendation['long']['updated_time'])) > 0.5):
                    self.current_recommendation['long'] = {
                                                                            'updated_time': 0,
                                                                            'level': 0,
                                                                            'price': None
                                                                        }

                kline_info = self.kline_info
                if len(kline_info['kline_list']['close_price_list']) == self.__initial_data_num:
                    self.__latest_data_analysis_timestamp = self.__latest_data_update_timestamp
                    MACD, EMA, RSI, EMV = get_indicators(kline_info['kline_list'], self.indicator_config)

                    if ((MACD != None) and (EMA != None) and (RSI != None)):

                        MACD_dict = {
                            'macd': np.round(MACD[0], decimals=4),
                            'macdsignal':  np.round(MACD[1], decimals=4),
                            'macdhist':  np.round(MACD[2], decimals=4)
                        }

                        EMA_dict = {
                            'ema1': np.round(EMA[0], decimals=3),
                            'ema2': np.round(EMA[1], decimals=3),
                            'ema3': np.round(EMA[2], decimals=3)
                        }

                        RSI_dict = {
                            'rsi1': np.round(RSI[0], decimals=3),
                            'rsi2': np.round(RSI[1], decimals=3),
                            'rsi3': np.round(RSI[2], decimals=3)
                        }


                        self.indicator_dict = {
                            'MACD_dict': MACD_dict,
                            'EMA_dict': EMA_dict,
                            'RSI_dict': RSI_dict,
                            'EMV_list': EMV
                        }

                        latest_price = kline_info['kline_list']['close_price_list'][-1]

                        level, side = self.get_recommendation(MACD_dict, EMA_dict, RSI_dict)

                        '''
                                self.current_recommendation = {
                                'short': {
                                    'updated_time': 0,
                                    'level': 0,
                                    'price': None
                                },

                                'long': {
                                    'updated_time': None,
                                    'level': 0,
                                    'price': None
                                }
                            }
                        '''
                        if level >= 0:
                            if (side == 'long' or side == 'short'):
                                self.current_recommendation[side]['level'] = level
                                self.current_recommendation[side]['price'] = latest_price
                                self.current_recommendation[side]['updated_time'] = current_utc_time()
                                temp_logs = '\n\n{}\nNew {} recommendation:\nLevel: {}\nPrice: {}\nDatetime: {}\nTimestamp: {}\n{}\n\n'.format(
                                    self.margin, 
                                    side.upper(), 
                                    level, 
                                    latest_price, 
                                    utc_2_datetime(self.current_recommendation[side]['updated_time']), 
                                    self.current_recommendation[side]['updated_time'], 
                                    self.margin
                                    )
                                # print(temp_logs)
                                put_to_log(temp_logs, self.__recommendation_log_path)
                    
                        # print ("\r||(MACD - MACDSignal) = {:.3f}||RSI({}): {:.3f}||RSI({}): {:.3f}||RSI({}): {:.3f}||EMA{}: {:.3f}||EMA{}: {:.3f}|| EMA{}: {:.3f}||Buy level: {}||Sell level: {}||Price: {:.2f}||Time: {}||".format
                        #         (macd[-1] - macdsignal[-1], 
                        #         self.indicator_config['rsi']['rsi1'],
                        #         rsi1[-1], 
                        #         self.indicator_config['rsi']['rsi2'],
                        #         rsi2[-1], 
                        #         self.indicator_config['rsi']['rsi3'],
                        #         rsi3[-1], 
                        #         self.indicator_config['ema']['ema1'],
                        #         ema1[-1],
                        #         self.indicator_config['ema']['ema2'],
                        #         ema2[-1],
                        #         self.indicator_config['ema']['ema3'],
                        #         ema3[-1],
                        #         buy_level,
                        #         sell_level,
                        #         float(np_price_list[-1]),
                        #         current_date_time()
                        #         ), end="")

            except Exception as e:
                log = "\n\n{}\nAn ERROR happend while analyzing market data: {} at {}\n{}\n\n".format(self.margin,
                                                                                                    e, 
                                                                                                    str(datetime.fromtimestamp(current_utc_time())),
                                                                                                    self.margin
                                                                                                    )
                print(log)
                put_to_log(log, self.__error_log_path)

    def check_if_service_avaliable(self):
        '''
        https://stackoverflow.com/questions/16755394/what-is-the-easiest-way-to-get-current-gmt-time-in-unix-timestamp-format
        '''
        time.sleep(3)
        while True:
            if len(self.current_position_dict) > 0:
                string = "\r|" + current_date_time() 
                for clientID in self.current_position_dict.keys():
                    string += "|PositionSide: {} |Amount: {} |EntryPrice: {}|CurrentPrice: {}  ROE: {:.3f}%|".format(
                    self.current_position_dict[clientID]['positionSide'],
                    self.current_position_dict[clientID]['quantity'] if self.current_position_dict[clientID]['quantity']!= None else "NA",
                    self.current_position_dict[clientID]['entryPrice'] if self.current_position_dict[clientID]['entryPrice'] else "NA",
                    self.kline_info['kline_list']['close_price_list'][-1] if self.kline_info['kline_list']['close_price_list'][-1] != None else "NA",
                    (100*self.__leverage*(self.kline_info['kline_list']['close_price_list'][-1]/self.current_position_dict[clientID]['entryPrice']-1) * (-1) if self.current_position_dict[clientID]['positionSide'].lower() == 'short' else 1) if ( self.current_position_dict[clientID]['entryPrice'] != None) else 0.00
                                                                                )

                print(string, end = "")
            else:
                kling_string = '|o:{:.2f}|h:{:.2f}|l:{:.2f}|c:{:.2f}|QuoVol:{:.2f}|BaseVol:{:.2f}|BuyBaseVol:{:.2f}|BuyQuoVol:{:.2f}|numTrades:{}|'.format(
                    self.kline_info['kline_list']['open_price_list'][-1],
                    self.kline_info['kline_list']['high_price_list'][-1],
                    self.kline_info['kline_list']['low_price_list'][-1],
                    self.kline_info['kline_list']['close_price_list'][-1],

                    self.kline_info['kline_list']['quoteAssetVolume_list'][-1],
                    self.kline_info['kline_list']['volume_list'][-1],
                    self.kline_info['kline_list']['takerBuyBaseAssetVolume_list'][-1],
                    self.kline_info['kline_list']['takerBuyQuoteAssetVolume_list'][-1],

                    self.kline_info['kline_list']['numTrades_list'][-1]
                )

                recommendation_string = '|_R_|LONG:L: {},P:{}|SHORT:L: {},P:{}|'.format(
                    self.current_recommendation['long']['level'],
                    self.current_recommendation['long']['price'],
                    self.current_recommendation['short']['level'],
                    self.current_recommendation['short']['price']
                )

                indicator_dict = self.indicator_dict
                if len(indicator_dict) > 0:
                    # print(indicator_dict['EMV_list'][-1])
                    indicator_string = '|EMA:{:.2f}--{:.2f}--{:.2f}|MACDdiff:{:.2f}|EMV:{:.2f}|'.format(
                        indicator_dict['EMA_dict']['ema1'][-1],
                        indicator_dict['EMA_dict']['ema2'][-1],
                        indicator_dict['EMA_dict']['ema3'][-1],
                        indicator_dict['MACD_dict']['macd'][-1] - indicator_dict['MACD_dict']['macdsignal'][-1],
                        indicator_dict['EMV_list'][-1]
                    )
                else:
                    indicator_string = ""
                

                print('\r' + kling_string + recommendation_string + indicator_string, end="")
            

            try:
                # time.sleep(1)
                # if self.depth_object!= None:
                #     bids_string = '{}'.format([order.price for order in self.depth_object.bids[-10:]])
                #     asks_string = '{}'.format([order.price for order in self.depth_object.asks[-10:]])
                #     margin = '========================================================================='
                #     print('\n\n\n{}\nRecent Market Prices:\n{}\n\nTop bids:\n{}\n\nTop asks:\n{}\n{}\n\n\n'.format(margin, price_string, bids_string, asks_string, margin))


                current_time = current_utc_time()*1000
                server_status = self.client.get_system_status()
                current_candlestick_data_time = int(self.__latest_data_update_timestamp)
                current_depth_data_time = int(self.__latest_depth_update_timestamp)


                candlestick_data_time_diff_in_seconds = (current_time - current_candlestick_data_time)/1000
                depth_data_time_diff_in_seconds = (current_time - current_depth_data_time)/1000

                if server_status['status'] == 1:
                    print('> > > > > > > > > > > > > > System maintenance. < < < < < < < < < < < < < < < <')
                if ((candlestick_data_time_diff_in_seconds > 1) and (current_time != (candlestick_data_time_diff_in_seconds*1000))):
                    print("Candlestick data fetching was down for: {:.3f}s".format(candlestick_data_time_diff_in_seconds))
                if ((depth_data_time_diff_in_seconds > 1) and (current_time!=(depth_data_time_diff_in_seconds*1000))):
                    print("Depth data fetching was down for: {:.3f}s".format(depth_data_time_diff_in_seconds))
            except Exception as e:
                log = "\n\n{}\nAn ERROR happend while monitoring services: {} at {}\n{}\n\n".format(self.margin,
                                                                                                    e, 
                                                                                                    str(datetime.fromtimestamp(current_utc_time())),
                                                                                                    self.margin
                                                                                                    )
                print(log)
                put_to_log(log, self.__error_log_path)
    
    def position_handler(self):
        '''
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/orderupdate.py
        has_key was removed in Python 3:
            https://stackoverflow.com/questions/33727149/dict-object-has-no-attribute-has-key?answertab=votes#tab-top
            https://docs.python.org/3.0/whatsnew/3.0.html#builtins
        https://github.com/Binance-docs/Binance_Futures_python/blob/master/binance_f/model/orderupdate.py

        self.current_position_dict = {
            'uniqueOrderId': {
                            'uniqueOrderId': None
                            'level': 1, 2, or 3
                            'positionSide': 'SIDE',
                            'trigeredPrice': -99999
                            'entryPrice': -99999,
                            'exitPrice': -99999,
                            'quantity': 0,
                            'comission': 999,
                            'relatedOrderID': {}
                            }
        Order status (status):

        NEW
        PARTIALLY_FILLED
        FILLED
        CANCELED
        REJECTED
        EXPIRED
        '''
        while True:
            try:
                if len(self.order_update_list) > 0:
                    first_order = self.order_update_list.pop(0)
                    clientOrderId = first_order.clientOrderId
                    if len(clientOrderId) >= 13:
                        prefix_id = clientOrderId[:13]
                    else:
                        prefix_id = clientOrderId

                    if prefix_id in self.current_position_dict:
                        print("\n====================================================================\nReceived a bot order:")
                        PrintMix.print_data(first_order)
                        put_to_log('\n\nBot order: {}\n{}\n'.format(current_date_time(), convert_object_to_string(first_order)), self.__order_log_path)
                        print("====================================================================")
                        
                        positionSide = first_order.positionSide.lower()
                        orderPosition = first_order.side.lower()
                        orderStatus = first_order.orderStatus.lower()

                        if ((positionSide == 'long' and orderPosition == 'buy') or (positionSide == 'short' and orderPosition == 'sell')):
                            if (orderStatus == 'PARTIALLY_FILLED'.lower() or  orderStatus == 'FILLED'.lower()):
                                if orderStatus == 'PARTIALLY_FILLED'.lower():
                                    try:
                                        self.client.futures_cancel_order(origClientOrderId = clientOrderId, symbol = self.__paried_symbol)
                                    except Exception as e:
                                        log = "\n\n{}\nAn ERROR happend while cancelling the unfilled order: {}, ERROR({}) at {}\n{}\n\n".format(self.margin,
                                                                                                                            clientOrderId,
                                                                                                                            e, 
                                                                                                                            str(datetime.fromtimestamp(current_utc_time())),
                                                                                                                            self.margin
                                                                                                                            )
                                        print(log)
                                        put_to_log(log, self.__error_log_path)

                                self.current_position_dict[prefix_id]['entryPrice'] = first_order.avgPrice
                                self.current_position_dict[prefix_id]['quantity'] = first_order.cumulativeFilledQty
                                self.current_position_dict[prefix_id]['relatedOrderID'][clientOrderId] = first_order
                                self.current_position_dict[prefix_id]['comission'] += (0 if first_order.commissionAmount == None else first_order.commissionAmount)
                                # self.__starting_asset_value -= ((first_order.avgPrice * first_order.cumulativeFilledQty)/self.__leverage)
                                #TODO: sell order:

                                correspondingTargetProfitRatio = self.target_profit_dict['level' + str(self.current_position_dict[prefix_id]['level'])]
                                
                                if positionSide.lower() == 'long':
                                    TP_stopPrice = round( ( first_order.avgPrice * (1+ (correspondingTargetProfitRatio + self.__comission_rate)/self.__leverage) ) ,2)
                                    SM_stopPrice = round( ( first_order.avgPrice * (1-(self.__stop_loss_ratio)/self.__leverage) ),2)
                                elif positionSide.lower() == 'short':
                                    TP_stopPrice = round( ( first_order.avgPrice * (1 - (correspondingTargetProfitRatio + self.__comission_rate)/self.__leverage) ) ,2)
                                    SM_stopPrice = round( ( first_order.avgPrice * (1 + (self.__stop_loss_ratio)/self.__leverage) ),2)

                                quantity =round((first_order.avgPrice*first_order.lastFilledQty),3)
                                
                                # Take profit order
                                self.client.futures_create_order(symbol = self.__paried_symbol,
                                                        side=(OrderSide.BUY if positionSide.lower() == "short" else OrderSide.SELL), 
                                                        type=OrderType.TAKE_PROFIT,
                                                        positionSide=positionSide.upper(),
                                                        # closePosition=True,
                                                        quantity =quantity,
                                                        stopPrice = TP_stopPrice,
                                                        price = TP_stopPrice,
                                                        newClientOrderId= prefix_id + OrderSide.SELL + "_" + positionSide + "_TP",
                                                        )
                                                        
                                # Stop loss order
                                self.client.futures_create_order(symbol = self.__paried_symbol, 
                                                        side=(OrderSide.BUY if positionSide.lower() == "short" else OrderSide.SELL), 
                                                        type=OrderType.STOP_MARKET,
                                                        positionSide=positionSide.upper(),
                                                        closePosition=True,
                                                        quantity =quantity,
                                                        stopPrice = SM_stopPrice,
                                                        newClientOrderId= prefix_id + OrderSide.SELL + "_" + positionSide + "_SM",
                                                        )
                            else:
                                self.current_position_dict[prefix_id]['relatedOrderID'][clientOrderId] = first_order

                        elif ((positionSide == 'long' and orderPosition == 'sell') or (positionSide == 'short' and orderPosition == 'buy')):
                                self.current_position_dict[prefix_id]['comission'] += (0 if first_order.commissionAmount == None else first_order.commissionAmount)
                                self.current_position_dict[prefix_id]['relatedOrderID'][clientOrderId] = first_order
                                if orderStatus == 'FILLED'.lower():
                                    TP = clientOrderId[:-2] + "TP"
                                    SM = clientOrderId[:-2] + "SM"
                                    clientOrderID_not_filled = TP if clientOrderId[-2:] == "SM" else SM
                                    originalSpend = self.current_position_dict[prefix_id]['entryPrice'] * self.current_position_dict[prefix_id]['quantity']

                                    TP_quantity = self.current_position_dict[prefix_id]['relatedOrderID'][TP].cumulativeFilledQty 
                                    TP_average_price = self.current_position_dict[prefix_id]['relatedOrderID'][TP].avgPrice
                                    TP_total = TP_quantity * TP_average_price

                                    SM_quantity = self.current_position_dict[prefix_id]['relatedOrderID'][SM].cumulativeFilledQty
                                    SM_average_price = self.current_position_dict[prefix_id]['relatedOrderID'][SM].avgPrice
                                    SM_total = SM_quantity * SM_average_price

                                    if positionSide.upper() == 'short':
                                        profit = ( (TP_total + SM_total)- originalSpend  - self.current_position_dict[prefix_id]['comission'])
                                    else:
                                        profit = ( originalSpend - (TP_total + SM_total)  - self.current_position_dict[prefix_id]['comission'])

                                    self.__starting_asset_value += profit

                                    try:
                                        self.client.futures_cancel_order(origClientOrderId = clientOrderID_not_filled, symbol = self.__paried_symbol)
                                    except Exception as e:
                                        log = "\n\n{}\nAn ERROR happend while cancelling the order: {}, ERROR({}) at {}\n{}\n\n".format(self.margin,
                                                                                                                            clientOrderID_not_filled,
                                                                                                                            e, 
                                                                                                                            str(datetime.fromtimestamp(current_utc_time())),
                                                                                                                            self.margin
                                                                                                                            )
                                        print(log)
                                        put_to_log(log, self.__error_log_path)
                                    else:
                                        log_string = '\n\n{}\nPNL for this order:\nclientOrderId: {}\npositionSide: {}\nentryPrice: {}\nexitPrice: {}\nTakeProfitAmount: {}\n      TakeProfitQuantity: {}\n     TakeProfitPrice: {}\nStopLossAmount: {}\n       StopLossQuantity: {}\n      StopLossPrice: {}\nComission: {}\nProfit: {}\nStart Datetime: {}\nFinished Datetime: {}\n{}'.format(self.margin, 
                                                                            prefix_id,
                                                                            positionSide.upper(),
                                                                            self.current_position_dict[prefix_id]['entryPrice'],
                                                                            ((TP_total + SM_total)/(TP_quantity + SM_quantity)),
                                                                            TP_total, TP_quantity, TP_average_price,
                                                                            SM_total, SM_quantity, SM_average_price,
                                                                            self.current_position_dict[prefix_id]['comission'], 
                                                                            profit, 
                                                                            utc_2_datetime(int(prefix_id)/1000),
                                                                            current_date_time(), 
                                                                            self.margin)
                                        put_to_log(log_string, self.__profit_log_path)
                                        print(log_string)
                                        del self.current_position_dict[prefix_id]

                                else:
                                    self.current_position_dict[prefix_id]['relatedOrderID'][clientOrderId] = first_order
                    else:
                        print("\n====================================================================\nReceived an user order:")
                        PrintMix.print_data(first_order)
                        put_to_log('\n\nUser order:\n{}\n'.format(convert_object_to_string(first_order)), self.__order_log_path)
                        print("====================================================================\n")

            except Exception as e:
                log = "\n\n{}\nAn ERROR happend in position handler function: {} at {}\n{}\n\n".format(self.margin,
                                                                                                    e, 
                                                                                                    str(datetime.fromtimestamp(current_utc_time())),
                                                                                                    self.margin
                                                                                                    )
                print(log)
                put_to_log(log, self.__error_log_path)

    def position_status_handler(self):
        '''
        NEW
        PARTIALLY_FILLED 部分成交
        FILLED 成交
        CANCELED 已撤
        CALCULATED
        EXPIRED 订单失效
        TRADE 交易
        '''
 

        while True:

            try:
                current_order_status = None if self.position_status.order_status == None else self.position_status.order_status.upper()
                if (current_order_status == 'FILLED'):
                    time.sleep(0.05)
                    if ((self.position_status.position_object.amount == 0) and ((current_order_status =='FILLED'))):
                        # Position finished successfully, reset
                        self.position_status = positionStatus(self.__paried_symbol)
                        print('Position finished!:\nPosition status reset!')

                    elif ((self.position_status.position_object.amount != 0) and ((current_order_status =='FILLED'))):
                        # Order finished successfully, reset order, handle/monitor position
                        pass

                elif (current_order_status == 'CANCELED'):
                    time.sleep(0.05)
                    if ((self.position_status.position_object.amount== 0) and ((current_order_status =='CANCELED'))):
                        # Position finished unexpectively, reset
                        self.position_status = positionStatus(self.__paried_symbol)
                        print('Order was canceled, but position finished: \nPosition status reset!\n')
                    elif ((self.position_status.position_object.amount != 0) and ((current_order_status =='CANCELED'))):
                        # Order canceled, handle/monitor position
                        pass

                elif (current_order_status == 'NEW'):
                    time.sleep(0.05)
                    if ((self.position_status.position_object.amount == 0) and ((current_order_status =='NEW'))):
                        # Order waiting to be filled to position
                        pass
                    elif ((self.position_status.position_object.amount != 0) and ((current_order_status =='NEW'))):
                        # Order created, handle/monitor position
                        print("Order is created to handle the corresponding position!")

                elif (current_order_status == 'EXPIRED'):
                    time.sleep(0.05)
                    if ((self.position_status.position_object.amount == 0) and ((current_order_status =='EXPIRED'))):
                        # Position finished unexpectively,  Reset
                        pass
                    elif ((self.position_status.position_object.amount != 0) and ((current_order_status =='EXPIRED'))):
                        # Order finished successfully, reset order, handle/monitor position
                        pass
                
                elif ((current_order_status == None) and (self.position_status.position_object.amount == 0)):
                    #analyzing
                    time.sleep(1)
                    # print('This is not finished yet!', self.kline_info['kline_list']['close_price_list'][-4:])
                    pass


                elif (current_order_status == 'PARTIALLY_FILLED'):
                    pass
                elif (current_order_status == 'CALCULATED'):
                    pass
                elif (current_order_status == 'TRADE'):
                    pass
                # else:
                #     raise Exception("\nUnkown error happened while handlling position: invalid position status: {}".format(self.position_status.order_status))
            except Exception as e:
                log = "\n\n{}\nAn ERROR happend while handling position status: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
                print(log)
                put_to_log(log, self.__error_log_path)
          
    def order_handler(self):
        '''
        self.current_recommendation = {
            'short': {
                'updated_time': 0,
                'level': 0,
                'price': None
            },

            'long': {
                'updated_time': 0,
                'level': 0,
                'price': None
            }
        }

        self.current_position_dict = {
            'uniqueOrderId': {
                            'uniqueOrderId': None
                            'level': 1, 2, or 3
                            'positionSide': 'SIDE',
                            'trigeredPrice': -99999
                            'entryPrice': -99999,
                            'exitPrice': -99999,
                            'quantity': 0,
                            'relatedOrderID': {}
                            'comission': 999
                            }
        }
        '''
        while True:
            try:
                for clientID in self.current_position_dict.keys():
                    clientOrderID = clientID + OrderSide.BUY + "_" + self.current_position_dict[clientID]['positionSide']
                    if ( ( ( int(time.time())*1000 - int(clientID[:13] ) ) > self.__order_timeout) and ( self.current_position_dict[clientID]['entryPrice'] == None ) ):
                        result = None
                        try:
                            result = self.client.futures_cancel_order(origClientOrderId = clientOrderID, symbol = self.__paried_symbol)
                        except Exception as e:
                            log = "\n\n{}\nAn ERROR happend while cancelling the timeout order: {} at {}\n{}\n\n".format(self.margin,
                                                                                                                e, 
                                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                                self.margin
                                                                                                                )
                            print(log)
                            put_to_log(log, self.__error_log_path)
                        else:
                            if result!= None:
                                if result.status.upper() == 'CANCELED':
                                    del self.current_position_dict[clientID]
                            else:
                                raise Exception("\n\nTimeout order: {} was not successfully canceled.".format(clientID))

                if ( ( ( self.__acc_profit + self.__starting_asset_value) < 8) and ( len(self.current_position_dict) == 0 ) ):
                    print('\n\nNot enough balance: {}\n\n'.format( self.__acc_profit + self.__starting_asset_value))
                    time.sleep(3)

                if len(self.current_position_dict) <2:
                    recom = self.current_recommendation.copy()
                    if len(self.current_position_dict) == 1:
                        pass
                        # # Uncomment the following if both long and short can exist
                        # current_position_clientOrderId = list(self.current_position_dict.keys())[0]
                        # current_position_side = self.current_position_dict[current_position_clientOrderId]['positionSide']
                        # opoPositionSide = PositionSide.SHORT if current_position_side.upper() == PositionSide.LONG else PositionSide.SHORT

                        # if recom[opoPositionSide.lower()]['level'] > 0:
                        #     rec_price = recom[opoPositionSide.lower()]['price']
                        #     quantity =round((1/rec_price*(self.__starting_asset_value*self.__leverage)),3)
                        #     positionSide = opoPositionSide.lower()
                        #     level = recom[opoPositionSide.lower()]['level']
                        #     uniqueOrderId = str(int(current_utc_time())*1000)
                        #     self.place_limit_buy(positionSide, level, quantity, rec_price, uniqueOrderId)
                        #     time.sleep(0.2)

                    elif len(self.current_position_dict) == 0:
                        if (recom['short']['level'] > 0 or recom['long']['level'] > 0):
                            if recom['short']['level'] > 0:
                                posisionSide = 'short'
                            elif recom['long']['level'] > 0:
                                posisionSide = 'long'
                                
                            if (posisionSide == 'long' or posisionSide == 'short'):
                                rec_price = recom[posisionSide.lower()]['price']
                                quantity =round((1/rec_price*(self.__starting_asset_value*self.__leverage)),3)
                                level = recom[posisionSide.lower()]['level']
                                uniqueOrderId = str(int(current_utc_time())*1000)
                                self.place_limit_buy(posisionSide, level, quantity, rec_price, uniqueOrderId)

            except Exception as e:
                log = "\n\n{}\nAn ERROR happend while handling an order: {} at {}\n{}\n\n".format(self.margin,
                                                                                                e, 
                                                                                                str(datetime.fromtimestamp(current_utc_time())),
                                                                                                self.margin
                                                                                                )
                print(log)
                put_to_log(log, self.__error_log_path)

    def place_limit_buy(self, positionSide, level, quantity, price, uniqueOrderId):
        try: 
            self.client.futures_create_order(symbol = self.__paried_symbol, 
                                            side=(OrderSide.BUY if positionSide.lower() == "long" else OrderSide.SELL), 
                                            type=OrderType.LIMIT,
                                            positionSide=positionSide.upper(),
                                            timeInForce = TimeInForce.GTC,
                                            quantity =quantity,
                                            price = round((price * (1.0003 if positionSide.lower() == "long" else 0.9997)), 2),
                                            newClientOrderId=uniqueOrderId + OrderSide.BUY + "_" + positionSide
                                            )

        except Exception as e:
            log = "\n\n{}\nAn ERROR happend while placing a limit order: {} at {}\n{}\n\n".format(self.margin,
                                                                                            e, 
                                                                                            str(datetime.fromtimestamp(current_utc_time())),
                                                                                            self.margin
                                                                                            )
            print(log)
            put_to_log(log, self.__error_log_path)
        
        else:
            self.current_position_dict[uniqueOrderId] = {
                            'uniqueOrderId': uniqueOrderId,
                            'level': level,
                            'positionSide': positionSide,
                            'trigeredPrice': price,
                            'entryPrice': None,
                            'exitPrice': None,
                            'quantity': 0,
                            'relatedOrderID': {},
                            'comission': 0
                        }

    def cancele_order(self, clientOrderId):
        pass
    
    def run(self):
        '''
        https://www.itranslater.com/qa/details/2583623258847314944
        '''

        pre_task_finished = self.make_dir()
        if pre_task_finished:
            self.update_config_info()
            t1 = threading.Thread(target=self.start_subscribing)
            t2 = threading.Thread(target=self.start_analysing)
            t3 = threading.Thread(target=self.start_handler)
            t4 = threading.Thread(target=self.check_if_service_avaliable)
            
            task_list = [t1, t2, t3, t4]

            for task in task_list:
                task.start()
            
            for task in task_list:
                task.join()