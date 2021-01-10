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

sub_client = SubscriptionClient(api_key='N3DhZ0J5E2eUrcZtAn6AIr3KQsxlFSqJWktSjlNJd3JgvUfFuLrZjOO3iCfT7MpM', secret_key='m0j8oulpL81IrcO2sYRJ2M5NiAfFlkLK5QbPV2EfcJythfbGhJ17hfNVoBg5FXoI')


def callback(data_type: 'SubscribeMessageType', event: 'any'):
    if data_type == SubscribeMessageType.RESPONSE:
        print("Event ID: ", event)
    elif  data_type == SubscribeMessageType.PAYLOAD:
        print("Event type: ", event.eventType)
        print("Event time: ", event.eventTime)
        print("Symbol: ", event.symbol)
        print("Data:")
        PrintBasic.print_obj(event.data)
        # sub_client.unsubscribe_all()
    else:
        print("Unknown Data:")
    print()


def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

sub_client.subscribe_candlestick_event("btcusdt", CandlestickInterval.MIN1, callback, error)