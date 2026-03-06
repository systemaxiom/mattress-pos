"""
================================================================================
MODULE: Universal SQLite Data Engine (data_helper.py)
AUTHOR: [Your Name/Busby Mattress POS]
VERSION: 2.1.0
DESCRIPTION:
    A portable, high-level wrapper for SQLite3. This module provides 
    universal CRUD (Create, Read, Update, Delete) capabilities for Python 
    applications, featuring dictionary-mapped inserts and updates.

KEY FEATURES:
    - Context Management: Automatic connection handling via 'with' statements.
    - sq.Row Integration: Enables seamless dictionary and tuple row access.
    - Transaction Safety: Automated commit/rollback logic for data integrity.
    - Security: Parameterized queries to prevent SQL injection.

COMPATIBILITY:
    - Python 3.8+
    - SQLite 3.x
================================================================================
"""

import sqlitecloud as sqcloud
from dotenv import load_dotenv
import sqlite3 as sq
import os

class Data_Helper:
    def __init__(self):
        
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        load_dotenv()
        SQLITE_API_KEY = os.getenv("SQLITE_API_KEY") 
        DB_NAME = os.getenv("DBNAME")
        try:
            CONNECTION_STRING = f"sqlitecloud://cj9trwxovk.g6.sqlite.cloud:8860/{DB_NAME}?apikey={SQLITE_API_KEY}"
            self.conn = sqcloud.connect(CONNECTION_STRING)
            
            # 1. Select the database context
            self.conn.execute(f"USE DATABASE {DB_NAME}")
            
           
            self.cursor = self.conn.cursor()
            
            print(f"DEBUG: Attempting to connect to DB at: {CONNECTION_STRING}")
            print("✅ SQLITE Cloud Connection successful.")

        except Exception as e:
            clean_path =  str(self.db_path).strip()
            print(f"Cloud connection failed: Attempting to connect to DB at: {clean_path}")
            try:
                self.conn = sq.connect(clean_path, timeout=20)
                # sq.Row is magic: It lets you access data as row[0] OR row['price']
                self.conn.row_factory = sq.Row 
                self.cursor = self.conn.cursor()
                print("✅ Local Database Connection successful.")
            except sq.OperationalError as e:
                print(f"❌ Connection failed. Error: {e}")
                print(f"DEBUG: File exists? {os.path.exists(clean_path)}")
                

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.conn:
            self.conn.close()

    # ==========================================
    # UNIVERSAL CRUD OPERATIONS
    # ==========================================
    
    def create_table(self, table_name, columns_dict):
        """
        Universal Table Creator.
        Usage: db.create_table('inventory', {'sku': 'TEXT PRIMARY KEY', 'price': 'REAL'})
        """
        try:
            cols = ", ".join([f"{name} {dtype}" for name, dtype in columns_dict.items()])
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
            self.cursor.execute(sql)
            self.conn.commit()
            print(f"✅ Table '{table_name}' verified/created.")
            return True
        except sq.Error as e:
            print(f"❌ Create Table Error: {e}")
            return False
        
    def table_exists(self, table_name):
        """
        Universal Utility.
        Checks if a specific table exists in the current database.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_manual_query(query, (table_name,))
        return len(result) > 0

    def get_column_names(self, table_name):
        """Helper to see what's actually in a table (Universal for debugging)."""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in self.cursor.fetchall()]
    
    def add_column_if_missing(self, table_name, column_name, column_type="TEXT"):
        """Adds a column to an existing table only if it doesn't exist."""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            if column_name not in columns:
                self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                self.conn.commit()
                print(f"✅ Added column '{column_name}' to '{table_name}'.")
        except sq.Error as e:
            print(f"❌ Alter Table Error: {e}")
            
    
    def get_count(self, table_name, where_clause=None, where_args=()):
        """Returns the number of rows matching a criteria."""
        sql = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        self.cursor.execute(sql, where_args)
        return self.cursor.fetchone()[0]
    

    def select_data(self, table_name, columns="*", where_clause=None, where_args=()):
        
       try:
            sql = f"SELECT {columns} FROM {table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            
            self.cursor.execute(sql, where_args)
            rows = self.cursor.fetchall()
            
            # If no data found, return an empty list safely
            if not rows:
                return []
                
           
            column_names = [col[0] for col in self.cursor.description]
            dict_results = [dict(zip(column_names, row)) for row in rows]
            
            return dict_results
            
        except Exception as e:
            print(f"❌ Select Error: {e}")
            return []


    def insert_data(self, table_name, data):
        """
        Universal Insert. 
        Accepts Dictionaries OR Tuples seamlessly.
        """
        try:
            if isinstance(data, dict):
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                values = list(data.values())
                sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
                self.cursor.execute(sql, values)
            else:
              
                placeholders = ",".join(["?"] * len(data))
                sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                self.cursor.execute(sql, data)
                
            self.conn.commit()
            return self.cursor.lastrowid
        except sq.Error as e:
            print(f"❌ Insert Error ({table_name}): {e}")
            self.conn.rollback()
            return None

    def update_table(self, table_name, data, where_clause, where_args=()):
        """
        Universal Update.
        Accepts Dictionaries: data={"price": 10}
        Accepts Strings: data="count = count - 1"
        """
        try:
            if isinstance(data, dict):
                set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
                all_values = list(data.values()) + list(where_args)
            else:
              
                set_clause = data
                all_values = list(where_args)

            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            self.cursor.execute(sql, all_values)
            self.conn.commit()
            return True
        except sq.Error as e:
            print(f"❌ Update Error: {e}")
            self.conn.rollback()
            return False

    def delete_data(self, table_name, where_clause, where_args=()):
        """
        Universal Delete.
        Added args tuple for secure parameterized deletion.
        """
        try:
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            self.cursor.execute(sql, where_args)
            self.conn.commit()
            return True
        except sq.Error as e:
            print(f"❌ Delete Error: {e}")
            return False
        
    def ensure_db_directory(self):
        """Universal tool to make sure the DB folder exists on any OS."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"📁 Created missing directory: {db_dir}")
        

    def execute_manual_query(self, query, params=(), commit=True):
        """For complex JOINS or custom math queries."""
        try:
            self.cursor.execute(query, params)
            if commit:
                self.conn.commit()
            return self.cursor.fetchall()
        except sq.Error as e:
            print(f"❌ Query Error: {e}")
            return None
