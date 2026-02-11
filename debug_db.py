import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import sqlite3
import os
from src.config_manager import ConfigManager

try:
    config_manager = ConfigManager("config.yaml")
    config = config_manager.load_config()
    db_path = config.database.path
    
    print(f"Config DB Path: {db_path}")
    abs_path = os.path.abspath(db_path)
    print(f"Absolute DB Path: {abs_path}")
    
    if not os.path.exists(abs_path):
        print("[FAIL] ERROR: Database file does not exist at this path!")
    else:
        print(f"[OK] File exists. Size: {os.path.getsize(abs_path)} bytes")
        
        conn = sqlite3.connect(abs_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables found: {tables}")
        
        if 'projects' not in tables:
            print("[FAIL] 'projects' table MISSING! Attempting to create...")
            try:
                from src.database import get_database_manager
                db_url = f"sqlite:///{abs_path}"
                print(f"Creating tables at: {db_url}")
                db = get_database_manager(db_url)
                db.create_tables()
                print("[OK] Tables created successfully.")
            except Exception as e:
                print(f"[FAIL] Failed to create tables: {e}")
        else:
            print("[OK] 'projects' table found.")
        conn.close()

except Exception as e:
    print(f"Error: {e}")
