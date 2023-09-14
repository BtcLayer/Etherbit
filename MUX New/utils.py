def decode_sub_account_id(sub_account_id):
    """
    Decode the subAccountId to extract trader's details and specifics of the trade.
    This logic is based on the provided Solidity function. 
    """
    decoded = {}
    
    # Extracting the various components from the subAccountId based on bit operations
    decoded['account'] = (sub_account_id >> 96) & 0xFFFFFFFFFFFFFFFFFFFFFFFF
    decoded['collateralId'] = (sub_account_id >> 88) & 0xFF
    decoded['assetId'] = (sub_account_id >> 80) & 0xFF
    decoded['isLong'] = ((sub_account_id >> 72) & 0xFF) > 0
    
    return decoded

def encode_sub_account_id(account, collateral_id, asset_id, is_long):
    """
    Generates a subAccountId based on provided details.
    This logic is the reverse of the decoding function.
    """
    encoded = account << 96
    encoded |= collateral_id << 88
    encoded |= asset_id << 80
    if is_long:
        encoded |= 1 << 72

    return encoded

# Additional utility functions can be added as needed, 
# such as data validation, error handling, etc.