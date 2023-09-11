import bybit
from binance.client import Client
import api
import time
import requests
import hashlib
import hmac
import datetime
import pytz

class BinanceOrder:
    def __init__(self, api_key, api_secret, symbol):
        self.client = Client(api_key, api_secret)
        self.price_precision = self.get_price_precision(symbol) if symbol != "BTCUSDT" else 1

        self.quantity_precision = self.get_quantity_precision(symbol)
        # self.client.futures_change_position_mode(dualSidePosition='true')

    def market_order(self, symbol, position_side, side, qty): # Designed for hedge mode only. 
        return self.client.futures_create_order(symbol=symbol, positionSide=position_side, side=side, type=Client.FUTURE_ORDER_TYPE_MARKET, quantity=qty)

    def get_price(self, symbol):
        avg_price = self.client.futures_mark_price(symbol=symbol)
        return float(avg_price['markPrice'])

    def adjust_price_precision(self, value):
        return round(value, self.price_precision)
    
    def adjust_quantity_precision(self, value):
        return round(value, self.quantity_precision)

    def get_price_precision(self, symbol):
        exchange_info = self.client.futures_exchange_info()

        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s['pricePrecision']
        
        return None
    
    def get_quantity_precision(self, symbol):
        exchange_info = self.client.futures_exchange_info()

        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s['quantityPrecision']
        
        return None

    def stop_order(self, symbol, positionSide, side, qty, stop_price):
        if self.price_precision is not None:
            stop_price = self.adjust_price_precision(stop_price)
        
        return self.client.futures_create_order(symbol=symbol, positionSide=positionSide, side=side, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET, quantity=qty, stopPrice=stop_price)

    def place_limit_order(self, symbol, positionSide, side, qty, price):
        if self.price_precision is not None:
            price = self.adjust_price_precision(price)

        return self.client.futures_create_order(symbol=symbol, positionSide=positionSide, side=side, type=Client.FUTURE_ORDER_TYPE_LIMIT, quantity=qty, price=price, timeInForce="GTC")