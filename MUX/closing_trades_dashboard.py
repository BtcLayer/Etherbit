# extracts data from closing trades in real time and sends to gsheets dashboard, from where it may be easily retrieved and processed

from flask import Flask, request
from gevent.pywsgi import WSGIServer

from decimal import Decimal
import requests

import json
import time
import datetime

import smtplib
import ssl
from email.message import EmailMessage
from tabulate import tabulate

# Define email sender and receiver
email_sender = 'nitinrajasekar2@gmail.com'
email_password = 'wfshqafmkfrtneyr' #generate an app password for the email id after enabling two-step verification. https://www.youtube.com/watch?v=g_j6ILT-X0k for more details.
email_receiver = ['nitinrajasekar2@gmail.com','sainath@primetrade.ai','shivam@primetrade.ai']

from binance.client import Client


# for writing to gsheets dashboard
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# api keys for google
creds = ServiceAccountCredentials.from_json_keyfile_name('dashboard_key.json', scopes)
gfile = gspread.authorize(creds)
workbook = gfile.open('Closing_Trades_Dashboard')
sheet = workbook.worksheet('Sheet1')

#api keys for binance
api_key = "mOkrZqgbAcssAjxKHTmAztPdPXAasEmiwziZRnUxHl1suz9vYkp0dm007vk05xJB"
api_secret = "bEZ3AW9NYMgoMpdRfzwcItXewwYrorNSFy2UFBvvUCDIQwPzCZdUJG6UaFC9aT9v"
client = Client(api_key, api_secret)
# To obtain token's live 'decimals' values from ethplorer, to get the exponemt_offset value later
link_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x514910771AF9Ca656af840dff83E8264EcF986CA?apiKey=freekey").json()["decimals"])
uni_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984?apiKey=freekey").json()["decimals"])
wbtc_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0x2260fac5e5542a773aa44fbcfedf7c193bc2c599?apiKey=freekey").json()["decimals"])
weth_exp_offset=int(requests.get("https://api.ethplorer.io/getTokenInfo/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2?apiKey=freekey").json()["decimals"])




# Temporary sample list
# will read from a file as no. of traders increase
profitable_traders_list = [

    '0xc97cfd2c3a3e61316e931b784bde21e61ce15b82','0xe2823659be02e0f48a4660e4da008b5e1abfdf29','0xe8c19db00287e3536075114b2576c70773e039bd','0x8e1f868ebb90749dc6fce7e9f0e147fff59125d5','0x99655ca16c742b46a4a05afaf0f7798c336fd279','0xf76b1ed3e35c6e7c04ab2098001bf7909fd252a3','0xdcf711cb8a1e0856ff1cb1cfd52c5084f5b28030','0xe242e864b6770507c77a570967d879b9db9f2c13','0x48202a51c0d5d81b3ebed55016408a0e0a0afaae','0x54a7240cea67b8c41b7c7f2b485360f37331aef4','0x7b7736a2c07c4332ffad45a039d2117ae15e3f66','0x5e3cab8074c647c8f51cb3491fe64c00b2fd8355','0x629ec4737cc3197dad07ece6001b31cddc776f43','0x126ce873371c15a664306a387cc2329f67cc515b','0xe8234fe01139d921a4aa23164ba5e60eb9d1267b','0x28ead95628610b4ee91408cfe1c225c71ab6e7a8','0x3f0fbe29803e6ae8bcba412ab9019aa690be3649','0x68a3df93009670408292f9ba77c2b480cce6de2a','0xe7a71492b82ed632ce9cff137a5248e3af267fdf','0x476551e292547c70bb27307d87df54baeb0f644b','0xac125110bcdb05d784bb9376f904a3592904d0d1','0xb9581d8311cc3b9e677af6b0c55f1b93b69ad6f6'

]

app = Flask(__name__)

# specifies the route, and the http requests the the root will respond to
@app.route('/', methods=['POST'])

# function that will be executed when the route is called
def webhook():

    time_var = time.time()
    time_var = round(time_var)
    dt_object = datetime.datetime.fromtimestamp(time_var)
    dt_object += datetime.timedelta(hours=5, minutes=30) # converting to IST from UTC

    data = request.get_json()
    data = json.dumps(data)
    # print(data) # can do this to see the raw json data that is being processed on below
    data = json.loads(data)


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

    decrease_position_found=0

    for i in data["transaction"]["logs"]: # going thorugh all emitted events

        # Identifies the decrease position event, as it is the only event with 9 arguments (9*64 +2)
        
        if len(i["data"]) == 578:
            decrease_position_found=1
            string = i["data"]
            string = string[2:]
            # array of its parameter values
            array = [string[i:i+64] for i in range(0, len(string), 64)]



            account = array[1]
            account = "0x" + account[-40:]  # account

            col_token = array[2]
            col_token = "0x" + col_token[-40:]  # collateral token

            token = array[3]
            token = "0x" + token[-40:]  # token traded

            isLong = array[6]
            isLong = "0x" + isLong  # long or short position
            if isLong == "0x0000000000000000000000000000000000000000000000000000000000000001":
                positionSide_var = "LONG"
            else:
                positionSide_var = "SHORT"

            col_delta = array[4]
            unit_price = array[7]
            # price of index token is in e30
            unit_price = float(float(int(unit_price, 16))/(10**30))
            col_delta = float(int(col_delta, 16)) # conv from hexa to decimal

            tok_str = "placeholder"
            max_precision = 0 # max precision of the token amount allowed by binance for making trade
            exponent_offset = 0 # exponent offset for the token amount, divide by 10^exponent_offset to get the actual amount
            

            # identifying the token and its precision from the token address

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
                side_var = "SELL"
            elif positionSide_var == "SHORT":
                side_var = "BUY"

    if decrease_position_found==0:
        print("Decrease position event not found")
        return 'OK', 200

    
    if positionSide_var == "LONG":

        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][1] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == token.lower():
                string = i["data"]
                string = string[2:]
                # represents amount of index token
                new_quantity_var = float(int(string, 16))

        new_quantity_var = float(new_quantity_var)/(10**exponent_offset) # get quantity of index token


    elif positionSide_var == "SHORT":
        for i in data["transaction"]["logs"]:
            if len(i["data"]) == 66 and len(i["topics"]) > 2 and i["topics"][1] == "0x000000000000000000000000489ee077994b6658eafa855c308275ead8097c4a" and str(i["address"]).lower() == col_token.lower():
                string = i["data"]
                string = string[2:]
                # represents amount of col token
                new_quantity_var = float(int(string, 16))

        # gets quantity of collateral token (whose value is 1 USD)

        # direct quantity of index token not available for short positions, so we have to calculate it using the collateral token quantity and the index token price

        if col_token == "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1" or col_token=="0x17fc002b466eec40dae837fc4be5c67993ddbd6f":   # if the collateral token is DAI or FRAX coin, then the exponent offset is 18
            new_quantity_var = float(new_quantity_var)/(10**18)

        else:
            new_quantity_var = float(new_quantity_var)/(10**6) # 6 is the exponent offset for other USD tokens ie. USDC or USDT

        new_quantity_var = float(new_quantity_var)/unit_price # divide amount of usd collateral token by index tokens price in usd, to get amount of index tokens



    new_quantity_var = round(new_quantity_var, max_precision)

    Is_in_list = "No"
    if account in profitable_traders_list:
        Is_in_list = "Yes"


    size = 10
    send_list = [None] * size
    send_list[1] = account
    send_list[0] = data["transaction"]["hash"]
    send_list[2] = positionSide_var
    send_list[3] = side_var
    send_list[4] = tok_str
    send_list[5] = new_quantity_var
    send_list[6] = unit_price
    total_price = unit_price*new_quantity_var
    total_price = round(total_price, 2)
    send_list[7] = total_price
    send_list[8] = str(dt_object)
    send_list[9] = Is_in_list

    


    sheet.append_row(send_list, table_range="A1:J1") # send the data to the gsheets dashboard

    if Is_in_list == "Yes":

        ######### module to send an email notification

        mail_col=['Transaction Hash', 'Wallet Address', 'Position Side', 'Side', 'Token', 'Token Quantity',	'Token Price (USD)', 'Volume traded', 'Timestamp', 'Trader In List']													
        mail_list=send_list

        # Set the subject and body of the email
        subject = 'Position decrease by a profitable trader'
        table_data = [[col, send] for col, send in zip(mail_col, mail_list)]
        table_format = tabulate(table_data, headers=['Attributes', 'Values'], tablefmt='simple')
        body = f"""
        Position decrease by a profitable trader
        {table_format}
        """

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())

        ##################

    print(send_list)


    return 'OK', 200

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8000)
    http_server = WSGIServer(('', 20), app)
    http_server.serve_forever()
