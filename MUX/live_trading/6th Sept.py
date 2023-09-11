from web3 import Web3
import variables

alchemy_url = "https://arb-mainnet.g.alchemy.com/v2/YvS_XN4GJEOEdPOUznbqRCVZ_rD7HvRr"
w3 = Web3(Web3.HTTPProvider(alchemy_url))
print(w3.is_connected())
print(w3.eth.block_number)
balance = w3.eth.get_balance("0xE8cd665913FD899979dA264e1e6F9FfF4809ff27")
ABI = variables.ABI
print(w3.from_wei(balance, "ether"))
print("Working")
address = Web3.to_checksum_address('0x489ee077994b6658eafa855c308275ead8097c4a')
contract = w3.eth.contract(address="0x489ee077994b6658eafa855c308275ead8097c4a", abi=ABI)
# totalSupply = contract.functions.totalSupply().call()
checksum = Web3.to_checksum_address
contract_address = Web3.to_checksum_address('0x489ee077994b6658eafa855c308275ead8097c4a')
account = checksum("0xbe878c39929ed3e79a9fff31a4415da9a45fa73c")
index_token = checksum("0x82af49447d8a07e3bd95bd0d56f35241523fbab1")
collateral_token = checksum("0x82af49447d8a07e3bd95bd0d56f35241523fbab1")
isLong = True
contract = w3.eth.contract(address=contract_address, abi=ABI)
position_details = contract.functions.getPosition(account, index_token, collateral_token, bool).call()
(position_size, position_collateral, position_avg_price) = (position_details[0] / 1e30, position_details[1] / 1e30, position_details[2] / 1e30)
entire_position = position_size / position_avg_price
print(entire_position, position_collateral, position_avg_price)
# return (entire_position, position_collateral, position_avg_price)


# def gmx_info(address, index_coin, collateral_coin, is_long):
#     alchemy_url = "https://arb-mainnet.g.alchemy.com/v2/YvS_XN4GJEOEdPOUznbqRCVZ_rD7HvRr"
#     w3 = Web3(Web3.HTTPProvider(alchemy_url))
#     print(w3.is_connected())

#     contract_address = Web3.to_checksum_address('0x489ee077994b6658eafa855c308275ead8097c4a')

#     ABI = variables.ABI

#     account = Web3.to_checksum_address(address)
#     index_token = Web3.to_checksum_address(index_coin)
#     collateral_token = Web3.to_checksum_address(collateral_coin)
#     bool = is_long

#     contract = w3.eth.contract(address=contract_address, abi=ABI)

#     position_details = contract.functions.getPosition(account, index_token, collateral_token, bool).call()

#     (position_size, position_collateral, position_avg_price) = (position_details[0] / 1e30, position_details[1] / 1e30, position_details[2] / 1e30)

#     entire_position = position_size / position_avg_price
#     print(entire_position, position_collateral, position_avg_price)
#     return (entire_position, position_collateral, position_avg_price)


# # 12 attributes in each tuple on the dashboard 
# size = 12
# send_list = [None] * size
# send_list[1] = address
# send_list[0] = data["transaction"]["hash"]
# send_list[2] = positionSide_var
# send_list[3] = side_var
# send_list[4] = tok_str
# send_list[5] = new_quantity_var
# send_list[6] = unit_price
# usd_volume = round(unit_price*new_quantity_var, 2)
# send_list[7] = usd_volume
# send_list[8] = str(dt_object)
# send_list[9] = Is_in_list
# send_list[10] = 0 # Liquidity not needed for now
# send_list[11] = leverage    