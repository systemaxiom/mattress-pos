import sqlitecloud # The new cloud library
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Your SQLite Cloud Connection String

SQL_CLOUD_URL = "sqlitecloud://<your-project-id>.sqlite.cloud:<port>?apikey=<your-api-key>"

def sync_from_cloud():
    # 1. Connect to the Cloud instead of a local file
    conn = sqlitecloud.connect(SQL_CLOUD_URL)
    conn.execute("USE DATABASE inventory.db") # Replace with your uploaded DB name
    conn.row_factory = sqlitecloud.Row
    cursor = conn.cursor()

    # 2. Pull the Heritage models for the sale
    cursor.execute("SELECT sku, name, size, price, attribute, vendor FROM inventory WHERE name LIKE '%Heritage%'")
    rows = cursor.fetchall()

    # ... The rest of your Shopify REST API logic remains the same ...
    # This keeps your 'Marked Out' price logic working!