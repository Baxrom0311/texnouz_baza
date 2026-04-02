import os
from access_parser import AccessParser
import time

def verify_system32_db():
    target = "C:\\Windows\\System32\\System32.mdb"
    print(f"[*] Verifying suspicious database: {target}")
    
    if not os.path.exists(target):
        print("[-] File not found.")
        return

    try:
        # 1. Check File Stats
        stat = os.stat(target)
        print(f"  Size: {stat.st_size//1024} KB")
        print(f"  Last Modified: {time.ctime(stat.st_mtime)}")
        print(f"  Attributes: {stat.st_file_attributes if hasattr(stat, 'st_file_attributes') else 'N/A'}")

        # 2. Try to open and list tables
        print("\n[*] Attempting to read table catalog...")
        db = AccessParser(target)
        print(f"[+] Successfully opened database.")
        print(f"[*] Tables found: {list(db.catalog.keys())}")
        
        if "tabMainData" in db.catalog:
            print("[!!!] BINGO! Found 'tabMainData' in System32.mdb!")
            # Peek at records
            data = db.parse_table("tabMainData")
            print(f"[*] Table has {len(data)} records.")
            if len(data) > 0:
                print(f"[SAMPLE]: {data[0]}")
        else:
            print("[-] 'tabMainData' table not found in this file.")

    except Exception as e:
        print(f"[!] Error during verification: {e}")

if __name__ == "__main__":
    verify_system32_db()
