# import logging
# from binance_f import RequestClient
# from binance.client import Client
# from binance_f import SubscriptionClient
# from binance_f.constant.test import *
# from binance_f.model import *
# from binance_f.exception.binanceapiexception import BinanceApiException
# from binance_f.base.printobject import *
# import time



# # Start user data stream
# request_client = RequestClient(api_key='N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM', secret_key='m0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI')
# listen_key = request_client.start_user_data_stream()
# # print("listenKey: ", listen_key)

# sub_client = SubscriptionClient(api_key='N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM', secret_key='m0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI')
# client = Client('N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM', 'm0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI')

# orderDetail = client.futures_get_order(origClientOrderId = '1610181159353SELL_LONG_SM', symbol = 'BTCUSDT')
# print(orderDetail)

# def dict2obj(d):
#     '''
#     https://stackoverflow.com/questions/1305532/convert-nested-python-dict-to-object
#     '''
#     if isinstance(d, list):
#         d = [dict2obj(x) for x in d]
#     if not isinstance(d, dict):
#         return d
#     class C(object):
#         pass
#     o = C()
#     for k in d:
#         o.__dict__[k] = dict2obj(d[k])
#     return o

# print(dict2obj(orderDetail).status)

import logging
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from binance_f.base.printobject import *

logger = logging.getLogger("binance-futures")
logger.setLevel(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
g_api_key = "N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM"
g_secret_key = "m0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI"

sub_client = SubscriptionClient(api_key=g_api_key, secret_key=g_secret_key)


def callback(data_type: 'SubscribeMessageType', event: 'any'):
    if data_type == SubscribeMessageType.RESPONSE:
        print("Event ID: ", event)
        PrintBasic.print_obj(event)
    elif  data_type == SubscribeMessageType.PAYLOAD:
        PrintBasic.print_obj(event)
        sub_client.unsubscribe_all()
    else:
        print("Unknown Data:")
    print()


def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

sub_client.subscribe_all_liquidation_event(callback, error)