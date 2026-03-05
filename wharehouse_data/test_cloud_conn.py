import sqlitecloud
import os
from dotenv import load_dotenv

load_dotenv()

# Use the API Key from your SQLite Cloud Dashboard
SQLITE_API_KEY = os.getenv("SQLITE_API_KEY") 

# Your supplied connection string
CONNECTION_STRING = f"sqlitecloud://cj9trwxovk.g6.sqlite.cloud:8860?apikey={SQLITE_API_KEY}"

def test_cloud_connection():
    try:
        # 1. Open the connection
        conn = sqlitecloud.connect(CONNECTION_STRING)
        
        # 2. Select the database you uploaded
        # Replace 'inventory.db' with whatever you named it in the dashboard
        conn.execute("USE DATABASE inventory.db") 
        
        # 3. Test a query
        cursor = conn.execute("PRAGMA table_info(customers) ")
        table_info = cursor.fetchall()
        
        
        c_names = [info[1] for info in table_info]
        print(c_names)
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_cloud_connection()