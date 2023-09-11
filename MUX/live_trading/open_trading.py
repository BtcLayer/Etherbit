import get_position_gmx as get_position
from web3 import Web3

# Functions
checksum = Web3.to_checksum_address

# Initial variables
account = checksum("0xbe878c39929ed3e79a9fff31a4415da9a45fa73c")
index_token = checksum("0x82af49447d8a07e3bd95bd0d56f35241523fbab1")
collateral_token = checksum("0x82af49447d8a07e3bd95bd0d56f35241523fbab1")
isLong = True

# First attaining the parameters from gmx's contract
(entire_position, position_collateral, position_avg_price) = get_position.gmx_info(account, index_token, collateral_token, isLong)

# Hash, will be sent to database as primary key.
position_hash = Web3.solidity_keccak(['address', 'address', 'address', 'bool'], [account, collateral_token, index_token, isLong]).hex()

# Database Connection using pymysql
import pymysql

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="defaultdb",
    host="position-tracker-shivamnayyar-288d.aivencloud.com",
    password="AVNS_wlIvjyOqcf91Qig1-TX",
    read_timeout=timeout,
    port=10770,
    user="avnadmin",
    write_timeout=timeout,
)
cursor = connection.cursor()

# Function to fetch old quantity from the database using the position hash
def fetch_old_quantity_from_db(position_hash):
    cursor.execute("SELECT base_position_taken FROM gmx WHERE id = %s", (position_hash,))
    result = cursor.fetchone()
    return result['base_position_taken'] if result else None

# Update or insert new position details into the gmx table
def update_gmx_table(position_hash, base_position_taken, base_position_not_taken):
    old_quantity = fetch_old_quantity_from_db(position_hash)
    
    if old_quantity:
        # Update existing row in the table
        new_quantity = old_quantity + base_position_taken
        cursor.execute("UPDATE gmx SET base_position_taken = %s, base_position_not_taken = %s WHERE id = %s", 
                       (new_quantity, base_position_not_taken, position_hash))
    else:
        # Insert new row in the table
        cursor.execute("INSERT INTO gmx (id, base_position_taken, base_position_not_taken) VALUES (%s, %s, %s)", 
                       (position_hash, base_position_taken, base_position_not_taken))
    connection.commit()

# Calculate Base Position Taken and Base Position Not Taken
old_quantity = fetch_old_quantity_from_db(position_hash)
base_position_taken = entire_position + (old_quantity if old_quantity else 0)
base_position_not_taken = entire_position - base_position_taken

# Update the GMX table
update_gmx_table(position_hash, base_position_taken, base_position_not_taken)
