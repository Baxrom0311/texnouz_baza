import os
from access_parser import AccessParser

def explore_all_tables():
    target = "C:\\Windows\\System32\\System32.mdb"
    print(f"[*] Exploring Tables in: {target}")
    
    if not os.path.exists(target):
        return

    try:
        db = AccessParser(target)
        all_tables = list(db.catalog.keys())
        print(f"[*] Found {len(all_tables)} tables.")
        
        for table_name in all_tables:
            # Skip system tables
            if table_name.startswith("MSys"): continue
            
            try:
                # Try to get count without full parse if possible
                # But access_parser usually needs iteration
                count = 0
                first_row = None
                
                # We use a very fast iteration
                data_iter = db.parse_table(table_name)
                for row in data_iter:
                    if count == 0:
                        first_row = row
                    count += 1
                
                if count > 0:
                    print(f"  [+] {table_name}: {count} items found.")
                    print(f"      - First item type: {type(first_row)}")
                    print(f"      - First item peek: {str(first_row)[:100]}")
            except Exception as e:
                print(f"  [-] {table_name}: Error {e}")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    explore_all_tables()
