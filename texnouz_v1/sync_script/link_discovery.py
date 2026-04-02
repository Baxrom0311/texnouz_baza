import os
from access_parser import AccessParser

def discover_links():
    mdb_path = "C:\\TEXNO UZ 1\\Base\\db3.mdb"
    print(f"[*] Auditing {mdb_path} for linked tables...")
    
    if not os.path.exists(mdb_path):
        print("[-] File not found.")
        return

    try:
        db = AccessParser(mdb_path)
        print(f"[+] Successfully opened {mdb_path}")
        print(f"[*] Available Tables: {db.catalog}")
        
        # In Access, linked tables are stored in MSysObjects
        # Access-parser might not expose MSysObjects directly easily, 
        # but we can try to read all tables.
        for table_name in db.catalog:
            print(f"Checking table: {table_name}")
            try:
                # If we can't fetch data, it might be a link
                data = db.parse_table(table_name)
                print(f"  [v] Local table with {len(data)} records.")
            except Exception as e:
                print(f"  [?] Potential linked table or error: {e}")
                
    except Exception as e:
        print(f"[!] Error opening MDB: {e}")

if __name__ == "__main__":
    discover_links()
