import os
from access_parser import AccessParser

def advanced_select():
    target = "C:\\Windows\\System32\\System32.mdb"
    print(f"[*] Advanced Data Selection: {target}")
    
    if not os.path.exists(target):
        return

    try:
        db = AccessParser(target)
        table_name = "tabMainData"
        
        if table_name in db.catalog:
            print(f"\n[*] Sampling {table_name}...")
            data_iter = db.parse_table(table_name)
            
            count = 0
            for row in data_iter:
                # Based on previous results, if row is a string, it might be a header
                if isinstance(row, str):
                    print(f"  [HEADER?]: {row}")
                    count += 1
                    if count > 50: break # Safety
                    continue
                
                # If we reach here, it's hopefully a dictionary (data row)
                print(f"\n--- Data Row Found at Index {count} ---")
                for k, v in row.items():
                    try:
                        print(f"  {k}: {str(v)}")
                    except Exception as ve:
                        print(f"  {k}: <VALUE ERROR: {ve}>")
                
                count += 1
                if count > 45: break # Only show first few data rows after headers
            
            print(f"\n[*] Finished scanning {count} items.")
        else:
            print(f"[-] Table {table_name} not found.")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    advanced_select()
