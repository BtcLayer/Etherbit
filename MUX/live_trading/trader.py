import pandas as pd
from libs import BinanceOrder
import api
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google API scopes and credentials
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    'dashboard_key.json', scopes)

gfile = gspread.authorize(creds)
workbook = gfile.open('Trades Replicated')
sheet = workbook.worksheet('Data')

# Read data from CSV
df = pd.read_csv(os.getcwd() + "\chosen_trades.csv")
initial_balance = 10000

class Trader:
    def __init__(self, trading_pair):
        # Initialize the BinanceOrder class
        self.binance = BinanceOrder(api.binance_api, api.binance_secret, trading_pair)
        self.trading_pair = trading_pair

    def replicate_trade(self, trader_address, volume, trade_direction, leverage):
        # Retrieve trader's trade parameters
        max_trade_volume = df.loc[trader_address, "Max Volume"]
        trader_weight = df.loc[trader_address, "Weighted Score"]
        stop_loss_percent = df.loc[trader_address, "Stop Loss"]
        take_profit_percent = df.loc[trader_address, "Take Profit"]

        # Calculate the proportion of the trader's score
        score_proportion = (trader_weight * volume) / max_trade_volume
        
        # Calculate collateral usage and quote volume
        risk_coefficient = 0.8
        collateral_used = round(initial_balance * score_proportion * risk_coefficient)
        quote_volume = round(collateral_used * leverage)
        
        # Get the current market price
        current_price = self.binance.get_price(self.trading_pair)

        # Calculate the final quantity to trade
        final_quantity = self.binance.adjust_quantity_precision(quote_volume / current_price)

        print(score_proportion, collateral_used, final_quantity)

        # Determine the trade side
        side = "BUY" if trade_direction == "LONG" else "SELL"
        counter_side = "SELL" if trade_direction == "LONG" else "BUY"

        # Open a market order
        self.binance.market_order(self.trading_pair, trade_direction, side, final_quantity)

        # Place stop loss and take profit orders
        sl_price = self.calculate_stop_loss(leverage, stop_loss_percent, current_price, trade_direction)
        tp_price = self.calculate_take_profit(take_profit_percent, current_price, trade_direction)

        sl_order_id = self.binance.stop_order(self.trading_pair, trade_direction, counter_side, final_quantity, sl_price)['orderId']
        tp_order_id = self.binance.place_limit_order(self.trading_pair, trade_direction, counter_side, final_quantity, tp_price)['orderId']

        # Update the dashboard
        dashboard_entry = [str(self.trading_pair), str(trade_direction), str(counter_side), str(final_quantity), str(sl_price), str(tp_price)]
        sheet.append_row(dashboard_entry, table_range="A1:F1")

    def calculate_stop_loss(self, leverage, stop_loss_percent, current_price, trade_direction):
        # Calculate the stop loss price
        leverage_sl_percent = 100 / leverage
        sl_percent = min(stop_loss_percent, leverage_sl_percent)

        if trade_direction == "LONG":
            stop_loss_price = round(current_price * (1 - sl_percent / 100), self.binance.price_precision)
        else:
            stop_loss_price = round(current_price * (1 + sl_percent / 100), self.binance.price_precision)

        return stop_loss_price

    def calculate_take_profit(self, take_profit_percent, current_price, trade_direction):
        # Calculate the take profit price
        if trade_direction == "LONG":
            take_profit_price = round(current_price * (1 + take_profit_percent / 100), self.binance.price_precision)
        else:
            take_profit_price = round(current_price * (1 - take_profit_percent / 100), self.binance.price_precision)

        return take_profit_price

# Example usage
Trader("BTCUSDT").replicate_trade("0xac125110bcdb05d784bb9376f904a3592904d0d1", 10000, "SHORT", 100)
