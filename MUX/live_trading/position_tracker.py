# %%
import pymysql


# %%
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


# %%
create_table_sql = """
CREATE TABLE gmx (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entire_position DECIMAL(20,8), 
    base_position_taken DECIMAL(20,8), 
    base_position_not_taken DECIMAL(20,8), 
    collateral_usd DECIMAL(20,2), 
    average_open_price DECIMAL(20,8),
    coin VARCHAR(50),
    side ENUM('LONG', 'SHORT'),
    liquidation_price DECIMAL(20,8)
)
"""

cursor.execute(create_table_sql)
connection.commit()

# %%
create_table_sql = """
CREATE TABLE binance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entire_position_base DECIMAL(20,8), 
    base_position_taken DECIMAL(20,8), 
    base_position_not_taken DECIMAL(20,8), 
    collateral_usd DECIMAL(20,2), 
    average_open_price DECIMAL(20,8),
    coin VARCHAR(50),
    side ENUM('long', 'short'),
    stop_loss DECIMAL(20,8)
)
"""

cursor.execute(create_table_sql)
connection.commit()

# %%
drop_table_sql = "DROP TABLE IF EXISTS gmx"
cursor.execute(drop_table_sql)

# %%
drop_table_sql = "DROP TABLE IF EXISTS binance"
cursor.execute(drop_table_sql)

# %%
connection.commit()
connection.close()


