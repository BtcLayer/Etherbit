from utils import decode_sub_account_id

class PositionTracker:
    def __init__(self, contract_interface):
        self.contract_interface = contract_interface

    def track_position_changes(self, address):
        # Fetch position changes or details for the address using the contract interface
        position_data = self.contract_interface.get_position_changes_by_address(address)

        # Decode the subAccountId to get position details
        decoded_position = decode_sub_account_id(position_data['subAccountId'])

        # Determine if the position has increased or decreased based on the data
        # This logic is hypothetical and would depend on the specific data structure returned
        if position_data['change'] > 0:
            change = "Increased"
        elif position_data['change'] < 0:
            change = "Decreased"
        else:
            change = "No change"

        return {
            'address': address,
            'decoded_position': decoded_position,
            'change': change,
            'updated_details': position_data['updated_details']
        }

    # Additional methods for further processing or displaying data can be added as needed
