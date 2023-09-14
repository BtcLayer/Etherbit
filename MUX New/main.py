from contract_interface import ContractInterface
from position_tracker import PositionTracker
from variables import ABI

# Constants (should be set to actual values)
RPC_URL = "YOUR_ETHEREUM_NODE_RPC_URL"
CONTRACT_ADDRESS = "YOUR_SMART_CONTRACT_ADDRESS"
CONTRACT_ABI = ABI

def main():
    # Initialize contract interface
    contract_interface = ContractInterface(RPC_URL, CONTRACT_ADDRESS, CONTRACT_ABI)
    
    # Initialize position tracker
    position_tracker = PositionTracker(contract_interface)

    # Prompt user for an Ethereum address
    address = input("Please provide the Ethereum address to check position changes: ")

    # Fetch and display position changes for the provided address
    position_changes = position_tracker.track_position_changes(address)
    
    # Display the results to the user
    print("\nResults for address:", position_changes['address'])
    print("Position change type:", position_changes['change'])
    print("Decoded position details:", position_changes['decoded_position'])
    print("Updated position details:", position_changes['updated_details'])

if __name__ == "__main__":
    main()
