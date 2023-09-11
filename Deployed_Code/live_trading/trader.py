import pandas as pd
from libs import BinanceOrder
import api

# for writing to gsheets dashboard
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Api keys for google
creds = ServiceAccountCredentials.from_json_keyfile_name(
    'dashboard_key.json', scopes)
gfile = gspread.authorize(creds)
workbook = gfile.open('Replicated Trades')
sheet = workbook.worksheet('Sheet1')

# Calculate the size to take for them.

df = pd.read_csv("./chosen_ones.csv", index_col=0)
binance_balance = 10000

class Trader: # Different for each pair
    def __init__(self, pair):
        # Initiate binance class
        self.binance = BinanceOrder(api.binance_api, api.binance_secret, pair)
        self.pair = pair

    def copyOpenTrade(self, address, volume, position_side, leverage): # Gets the correct pair
        # Instantiated Trader class
        # Figure out how much base quantity to take, based on the volume copy strategy. 

        # There is a case where I will have to calculate current weight usage of a trader where it goes over and bot is not supposed to trade there. 

        pair = self.pair

        max_vol = df.loc[address, "Max Volume"]
        max_weight = df.loc[address, "Weighted Score"]
        sl_percent = df.loc[address, "Stop Loss"]
        tp_percent = df.loc[address, "Take Profit"]

        # Important variable to calculate how much volume we should take. 
        # Formula -> Max volume: Max weight:: Volume taken by him: !!Corresponding partial score!!, for himself only though. 
        partial_score = (max_weight * volume) / max_vol
        
        # In percentage
        trade_weight = round(partial_score / df["Weighted Score"].sum(), 6)

        # Taking half risk on liquidation for now. 
        risk_coefficient = 10 # From 0 to 1, higher means we take more risk. Generally more for traders with better sortino ratio. Don't exceed 1, otherwise total collateral usage may exceed 100%. 
        trade_collateral = round(binance_balance * trade_weight * risk_coefficient)

        quote_volume = round(trade_collateral * leverage)
        
        price = self.binance.get_price(pair) # I could calcuate price once in 4 hours and use that for a while. 

        final_qty = self.binance.adjust_quantity_precision(quote_volume / price)

        print(trade_weight, trade_collateral, final_qty)

        side = "BUY" if position_side == "LONG" else "SELL"
        counter_side = "SELL" if position_side == "LONG" else "BUY" # Used for SL and TP

        # Open position
        self.binance.market_order(pair, position_side, side, final_qty)

        # Place stop loss
        sl = self.getSL(leverage, sl_percent, price, position_side)
        tp = self.getTP(tp_percent, price, position_side)

        slorderid = self.binance.stop_order(pair, position_side, counter_side, final_qty, sl)['orderId']
        tporderid = self.binance.place_limit_order(pair, position_side, counter_side, final_qty, tp)['orderId']

        dashboard_list=[str(pair), str(position_side), str(counter_side), str(final_qty), str(sl), str(tp)]
        sheet.append_row(dashboard_list, table_range="A1:F1") # Send to dashboard

        # Rajashri's work from here. 

    def getSL(self, leverage, stop_loss_percent, current_price, position_side):
        # Calculate both stop losses to find the better one
        leverage_sl_percent = 100 / leverage
        sl_percent = stop_loss_percent if stop_loss_percent < leverage_sl_percent else leverage_sl_percent # Whichever is lower

        if position_side == "LONG":
            # SL price will be below

            SL_price = round(current_price * (1 - sl_percent / 100), self.binance.price_precision)
        elif position_side == "SHORT":
            # SL price will be above

            SL_price = round(current_price * (1 + sl_percent / 100), self.binance.price_precision)

        return SL_price


    def getTP(self, tp_percent, current_price, position_side):
        # Calculate both stop losses to find the better one
        if position_side == "LONG":
            # SL price will be below

            TP_price = round(current_price * (1 + tp_percent / 100), self.binance.price_precision)
        elif position_side == "SHORT":
            # SL price will be above

            TP_price = round(current_price * (1 - tp_percent / 100), self.binance.price_precision)


        return TP_price

    # def recordInCSV():

Trader("BTCUSDT").copyOpenTrade("0xac125110bcdb05d784bb9376f904a3592904d0d1", 10000, "SHORT", 100)