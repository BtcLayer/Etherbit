# extracts data from opening trades in real time and sends to gsheets dashboard, from where it may be easily retrieved and processed

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
import gmx_get_position as get

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
workbook = gfile.open('Trades_being_replicated')
sheet = workbook.worksheet('Sheet1')

# Api keys for binance
api_key = "UvsLH9YOdEZJnk6yEyceDhMQIHAIhV1C1BEMI37GfXGU2y81MD55ic4E9D0iaUns"
api_secret = "RzgGyPV59iejem1y10PghWrMtsfBIfNHqaRAv2oh2VxxjBxPSsqfJZM0CtM3Uspj"

client = Client(api_key, api_secret)

# To obtain token's live 'decimals' values from ethplorer, to get the exponemt_offset value later
link_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x514910771AF9Ca656af840dff83E8264EcF986CA?apiKey=freekey").json()["decimals"])
uni_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984?apiKey=freekey").json()["decimals"])
wbtc_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x2260fac5e5542a773aa44fbcfedf7c193bc2c599?apiKey=freekey").json()["decimals"])
weth_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2?apiKey=freekey").json()["decimals"])


# All profitable trader -> weighted scores

profitable_traders = {}
df = pd.read_csv('./chosen_ones.csv', index_col=0)

for index, row in df.iterrows():
    profitable_traders[index] = row["Weighted Score"]


app = Flask(__name__)

# Specifies the route, and the http requests the root will respond to

@app.route('/', methods=['POST'])

# Function that will be executed when the route is called
def webhook():
    time_var = time.time()
    time_var = round(time_var)
    dt_object = datetime.datetime.fromtimestamp(time_var) 

    # converting to IST from UTC
    dt_object += datetime.timedelta(hours=5, minutes=30)

    data = request.get_json() # Extracting json file

    # print(data) # can do this to see the raw json data that is being processed on below

    data = json.loads(json.dumps(data))

    tx_hash=data["transaction"]["hash"]

    with open("tx_hash_store.txt", "r") as f:
        content = f.read()
        values = content.splitlines()
        if tx_hash in values:
            return 'OK', 200 # the transaction has already been processed before

        else:
            with open("tx_hash_store.txt", "a") as f2:
                f2.write(tx_hash+"\n")

    print(data["transaction"]["hash"])
    increase_position_found=0

    

    for i in data["transaction"]["logs"]:  # Going thorugh all emitted events of a specific tx

        if len(i["data"]) == 578: # Identifies the increase position event, as it is the only event with 9 arguments (9*64 +2)
            increase_position_found=1
            string = i["data"]
            string = string[2:]

            # Array of its parameter values, I guess it splits it up into 1 array.
            array = [string[i:i+64] for i in range(0, len(string), 64)]

            address = array[1]
            address = "0x" + address[-40:]  # Address

            col_token = array[2]
            col_token = "0x" + col_token[-40:]  # Collateral token

            token = array[3]
            token = "0x" + token[-40:]  # Token traded

            isLong = array[6]
            isLong = "0x" + isLong  # Long or Short position
            if isLong == "0x0000000000000000000000000000000000000000000000000000000000000001":
                positionSide_var = "LONG"
            else:
                positionSide_var = "SHORT"

            col_delta = array[4]
            size_delta=array[5]
            unit_price = array[7]

            # price of index token is in e30
            unit_price = float(float(int(unit_price, 16))/(10**30))
            col_delta = float(int(col_delta, 16))  # conv from hexa to decimal
            size_delta = float(int(size_delta, 16))  # conv from hexa to decimal

            leverage=size_delta/col_delta

            tok_str = "placeholder"
            max_precision = 0  # max precision of the token amount allowed by binance for making trade
            # exponent offset for the token amount, divide by 10^exponent_offset to get the actual amount

            exponent_offset = 0

            # Identifying the token and its precision from the token address

            if token == "0x82af49447d8a07e3bd95bd0d56f35241523fbab1":
                tok_str = "ETH"
                exponent_offset = weth_exp_offset
                max_precision=4

            elif token == "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f":
                tok_str = "BTC"
                exponent_offset = wbtc_exp_offset
                max_precision=5

            elif token == "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0":
                tok_str = "UNI"
                exponent_offset = uni_exp_offset
                max_precision=2

            elif token == "0xf97f4df75117a78c1a5a0dbb814af92458539fb4":
                tok_str = "LINK"
                exponent_offset = link_exp_offset
                max_precision=2

            symbol_var = tok_str+"USDT"

            if positionSide_var == "LONG":
                side_var = "BUY"
            elif positionSide_var == "SHORT":
                side_var = "SELL"

    if increase_position_found==0:
        print("Increase position event not found")
        return 'OK', 200

    if positionSide_var == "LONG":

        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][2] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == token.lower():
                string = i["data"]
                string = string[2:]
                # represents amount of index token
                new_quantity_var = float(int(string, 16))

        # get quantity of index token
        new_quantity_var = float(new_quantity_var)/(10**exponent_offset)


    elif positionSide_var == "SHORT":
        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][2] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == col_token.lower():
                string = i["data"]
                string = string[2:]
                # Represents amount of col token
                new_quantity_var = float(int(string, 16))

        # gets quantity of collateral token (whose value is 1 USD)

        # direct quantity of index token not available for short positions, so we have to calculate it using the collateral token quantity and the index token price

        # if the collateral token is DAI or FRAX coin, then the exponent offset is 18
        if col_token == "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1" or col_token == "0x17fc002b466eec40dae837fc4be5c67993ddbd6f":
            new_quantity_var = float(new_quantity_var)/(10**18)

        # if the collateral token is USDC or USDT, then the exponent offset is 6
        else:
            # 6 is the exponent offset for other USD tokens ie. USDC or USDT
            new_quantity_var = float(new_quantity_var)/(10**6)

        # divide amount of usd collateral token by index tokens price in usd, to get amount of index tokens
        new_quantity_var = float(new_quantity_var)/unit_price



    new_quantity_var = round(new_quantity_var, max_precision)

    Is_in_list = "No"
    if address in profitable_traders:
        Is_in_list = "Yes"

    # 12 attributes in each tuple on the dashboard 
    size = 12
    send_list = [None] * size
    send_list[1] = address
    send_list[0] = data["transaction"]["hash"]
    send_list[2] = positionSide_var
    send_list[3] = side_var
    send_list[4] = tok_str
    send_list[5] = new_quantity_var
    send_list[6] = unit_price
    usd_volume = round(unit_price*new_quantity_var, 2)
    send_list[7] = usd_volume
    send_list[8] = str(dt_object)
    send_list[9] = Is_in_list
    send_list[10] = 0 # Liquidity not needed for now
    send_list[11] = leverage


    if address in profitable_traders:

        # Before taking the trade, we will update the GMX side of the database.

        # Take the open trade
        # Params to use: positionSide_var (open long or open short), tok_str, new_quantity_var (exact token qty, not required).
        instance = t.Trader(tok_str + "USDT")
        instance.copyOpenTrade(address, usd_volume, tok_str + "USDT", positionSide_var, leverage) # Takes the actual trade

        # Later:- 
        # Later on we also need the price he took it on, so we can take it reasonably around that price itself. 
        # Time, keep track of it also, there can be one case when he instantly closes his trade and we haven't even taken it yet. So take care of that too. 

        # V2 mein limit orders jayenge to make sure that we've taken it around the price he got itself.. And if he closes it before we're filled, we cancel any of the position. 


        # Update the database here after trade is successful. 



        # Send it to excel
        sheet.append_row(send_list, table_range="A1:L1")

        # Record the open trade in the database
        
         

    print(send_list)

    return 'OK', 200
    
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=80)
    http_server = WSGIServer(('', 80), app)
    http_server.serve_forever()