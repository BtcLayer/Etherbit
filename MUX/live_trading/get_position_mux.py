from web3 import Web3
import confidential

def get_mux_details(addr, idx_coin, col_coin, is_long):
    alchemy_endpoint = "https://arb-mainnet.g.alchemy.com/v2/YvS_XN4GJEOEdPOUznbqRCVZ_rD7HvRr"
    w3 = Web3(Web3.HTTPProvider(alchemy_endpoint))
    print(w3.is_connected())

    contract_addr = Web3.to_checksum_address('0x489ee077994b6658eafa855c308275ead8097c4a')

    contract_abi = confidential.ABI

    wallet_addr = Web3.to_checksum_address(addr)
    index_tok = Web3.to_checksum_address(idx_coin)
    collateral_tok = Web3.to_checksum_address(col_coin)
    is_long_pos = is_long

    contract = w3.eth.contract(address=contract_addr, abi=contract_abi)

    pos_details = contract.functions.getPosition(wallet_addr, index_tok, collateral_tok, is_long_pos).call()

    (pos_size, pos_collateral, pos_avg_price) = (pos_details[0] / 1e30, pos_details[1] / 1e30, pos_details[2] / 1e30)

    entire_pos = pos_size / pos_avg_price
    print(entire_pos, pos_collateral, pos_avg_price)
    return (entire_pos, pos_collateral, pos_avg_price)
