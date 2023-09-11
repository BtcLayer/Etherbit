from web3 import Web3
import variables

def gmx_info(address, index_coin, collateral_coin, is_long):
    alchemy_url = "https://arb-mainnet.g.alchemy.com/v2/YvS_XN4GJEOEdPOUznbqRCVZ_rD7HvRr"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    print(w3.is_connected())

    contract_address = Web3.to_checksum_address('0x489ee077994b6658eafa855c308275ead8097c4a')

    ABI = variables.ABI

    account = Web3.to_checksum_address(address)
    index_token = Web3.to_checksum_address(index_coin)
    collateral_token = Web3.to_checksum_address(collateral_coin)
    bool = is_long

    contract = w3.eth.contract(address=contract_address, abi=ABI)

    position_details = contract.functions.getPosition(account, index_token, collateral_token, bool).call()

    (position_size, position_collateral, position_avg_price) = (position_details[0] / 1e30, position_details[1] / 1e30, position_details[2] / 1e30)

    entire_position = position_size / position_avg_price
    print(entire_position, position_collateral, position_avg_price)
    return (entire_position, position_collateral, position_avg_price)