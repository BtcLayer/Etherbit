from flask import Flask, request
from gevent.pywsgi import WSGIServer
from decimal import Decimal
import requests
import json
import time
import datetime
from binance.client import Client
import pandas as pd
import trader as t
import get_position_mux as get

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    'dashboard_key.json', scopes)
gfile = gspread.authorize(creds)
workbook = gfile.open('Replicated Trades')
sheet = workbook.worksheet('Sheet1')

api_key = "UvsLH9YOdEZJnk6yEyceDhMQIHAIhV1C1BEMI37GfXGU2y81MD55ic4E9D0iaUns"
api_secret = "RzgGyPV59iejem1y10PghWrMtsfBIfNHqaRAv2oh2VxxjBxPSsqfJZM0CtM3Uspj"

client = Client(api_key, api_secret)

link_exp_offset = int(requests.get("https://api.ethplorer.io/getTokenInfo/0x514910771AF9Ca656af840dff83E8264EcF986CA?apiKey=freekey").json()["decimals"])
uni_exp_offset = int(requests.get("https://api.ethplorer.io/getTokenInfo/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984?apiKey=freekey").json()["decimals"])
wbtc_exp_offset = int(requests.get("https://api.ethplorer.io/getTokenInfo/0x2260fac5e5542a773aa44fbcfedf7c193bc2c599?apiKey=freekey").json()["decimals"])
weth_exp_offset = int(requests.get("https://api.ethplorer.io/getTokenInfo/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2?apiKey=freekey").json()["decimals"])

profitable_traders = {}
df = pd.read_csv('./chosen_traders.csv', index_col=0)

for index, row in df.iterrows():
    profitable_traders[index] = row["Weighted Score"]

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    time_var = time.time()
    time_var = round(time_var)
    dt_object = datetime.datetime.fromtimestamp(time_var)
    dt_object += datetime.timedelta(hours=5, minutes=30)

    data = request.get_json()
    data = json.loads(json.dumps(data))

    tx_hash = data["transaction"]["hash"]

    with open("tx_hash_store.txt", "r") as f:
        content = f.read()
        values = content.splitlines()
        if tx_hash in values:
            return 'OK', 200
        else:
            with open("tx_hash_store.txt", "a") as f2:
                f2.write(tx_hash + "\n")

    print(data["transaction"]["hash"])
    increase_position_found = 0

    for i in data["transaction"]["logs"]:
        if len(i["data"]) == 578:
            increase_position_found = 1
            string = i["data"]
            string = string[2:]

            array = [string[i:i+64] for i in range(0, len(string), 64)]

            address = array[1]
            address = "0x" + address[-40:]

            col_token = array[2]
            col_token = "0x" + col_token[-40:]

            token = array[3]
            token = "0x" + token[-40:]

            is_long = array[6]
            is_long = "0x" + is_long
            if is_long == "0x0000000000000000000000000000000000000000000000000000000000000001":
                position_side_var = "LONG"
            else:
                position_side_var = "SHORT"

            col_delta = array[4]
            size_delta = array[5]
            unit_price = array[7]

            unit_price = float(float(int(unit_price, 16)) / (10**30))
            col_delta = float(int(col_delta, 16))
            size_delta = float(int(size_delta, 16))
            leverage = size_delta / col_delta

            tok_str = "placeholder"
            max_precision = 0
            exponent_offset = 0

            if token == "0x82af49447d8a07e3bd95bd0d56f35241523fbab1":
                tok_str = "ETH"
                exponent_offset = weth_exp_offset
                max_precision = 4

            elif token == "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f":
                tok_str = "BTC"
                exponent_offset = wbtc_exp_offset
                max_precision = 5

            elif token == "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0":
                tok_str = "UNI"
                exponent_offset = uni_exp_offset
                max_precision = 2

            elif token == "0xf97f4df75117a78c1a5a0dbb814af92458539fb4":
                tok_str = "LINK"
                exponent_offset = link_exp_offset
                max_precision = 2

            symbol_var = tok_str + "USDT"

            if position_side_var == "LONG":
                side_var = "BUY"
            elif position_side_var == "SHORT":
                side_var = "SELL"

    if increase_position_found == 0:
        print("Increase position event not found")
        return 'OK', 200

    if position_side_var == "LONG":
        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][2] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == token.lower():
                string = i["data"]
                string = string[2:]
                new_quantity_var = float(int(string, 16))

        new_quantity_var = float(new_quantity_var) / (10**exponent_offset)

    elif position_side_var == "SHORT":
        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][2] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == col_token.lower():
                string = i["data"]
                string = string[2:]
                new_quantity_var = float(int(string, 16))

        if col_token == "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1" or col_token == "0x17fc002b466eec40dae837fc4be5c67993ddbd6f":
            new_quantity_var = float(new_quantity_var) / (10**18)
        else:
            new_quantity_var = float(new_quantity_var) / (10**6)

        new_quantity_var = float(new_quantity_var) / unit_price

    new_quantity_var = round(new_quantity_var, max_precision)

    Is_in_list = "No"
    if address in profitable_traders:
        Is_in_list = "Yes"

    size = 12
    send_list = [None] * size
    send_list[1] = address
    send_list[0] = data["transaction"]["hash"]
    send_list[2] = position_side_var
    send_list[3] = side_var
    send_list[4] = tok_str
    send_list[5] = new_quantity_var
    send_list[6] = unit_price
    usd_volume = round(unit_price * new_quantity_var, 2)
    send_list[7] = usd_volume
    send_list[8] = str(dt_object)
    send_list[9] = Is_in_list
    send_list[10] = 0
    send_list[11] = leverage

    if address in profitable_traders:
        instance = t.Trader(tok_str + "USDT")
        instance.replicate_trade(address, usd_volume, tok_str + "USDT", position_side_var, leverage)
        sheet.append_row(send_list, table_range="A1:L1")

    print(send_list)

    return 'OK', 200

if __name__ == '__main__':
    http_server = WSGIServer(('', 80), app)
    http_server.serve_forever()
