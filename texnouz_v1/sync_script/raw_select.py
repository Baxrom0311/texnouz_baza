import os
from access_parser import AccessParser

def raw_select_dump():
    target = "C:\\Windows\\System32\\System32.mdb"
    print(f"[*] Raw Data Select: {target}")
    
    if not os.path.exists(target):
        print("[-] File not found.")
        return

    try:
        db = AccessParser(target)
        # We start with tabMainData which is the most important
        table_name = "tabMainData"
        
        if table_name in db.catalog:
            print(f"\n[*] Dumping records for {table_name}:")
            try:
                # We'll try to get the column names manually if possible
                # But let's just dump the row itself
                data_iter = db.parse_table(table_name)
                
                count = 0
                for row in data_iter:
                    if count >= 10: break # Show 10 records
                    
                    print(f"\n--- Record {count + 1} ---")
                    # Handle if row is a dict, string, or list
                    if hasattr(row, "items"):
                        for k, v in row.items():
                            try:
                                # Convert everything to string to avoid "int too large" errors
                                print(f"  {k}: {str(v)}")
                            except:
                                print(f"  {k}: <conversion error>")
                    else:
                        print(f"  [RAW]: {str(row)}")
                    
                    count += 1
                
                print(f"\n[*] Dumped {count} records.")
            except Exception as e:
                print(f"[!] Error during row processing: {e}")
        else:
            print(f"[-] Table {table_name} not found.")

    except Exception as e:
        print(f"[!] Critical error opening DB: {e}")

if __name__ == "__main__":
    raw_select_dump()
