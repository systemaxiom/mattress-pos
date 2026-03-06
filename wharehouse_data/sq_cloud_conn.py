import sqlitecloud # The new cloud library
import requests
import os
from dotenv import load_dotenv

load_dotenv()



SQL_CLOUD_URL = "sqlitecloud://<your-project-id>.sqlite.cloud:<port>?apikey=<your-api-key>"

def sync_from_cloud():
    
    conn = sqlitecloud.connect(SQL_CLOUD_URL)
    conn.execute("USE DATABASE inventory.db") 
    conn.row_factory = sqlitecloud.Row
    cursor = conn.cursor()

     
    cursor.execute("SELECT sku, name, size, price, attribute, vendor FROM inventory WHERE name LIKE '%Heritage%'")
    rows = cursor.fetchall()

    