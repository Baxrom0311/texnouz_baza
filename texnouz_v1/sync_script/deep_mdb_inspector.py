import os
from access_parser import AccessParser

def deep_inspect():
    mdb_path = r"C:\sync_texnouz\active_copy.mdb" # We already have a copy
    
    if not os.path.exists(mdb_path):
        print("[!] active_copy.mdb not found in C:\\sync_texnouz")
        return

    try:
        db = AccessParser(mdb_path)
        print("[*] Auditing all tables in: %s" % mdb_path)
        
        # Sort tables by the "ID" or whatever it is in catalog to see if it's helpful
        for table in sorted(db.catalog.keys()):
            try:
                data = db.parse_table(table)
                cols = list(data.keys())
                num_rows = len(data[cols[0]]) if cols else 0
                
                # We only care about tables with rows
                if num_rows > 0:
                    print("[+] Table %-20s | Rows: %5d | Columns: %d" % (table, num_rows, len(cols)))
                    
                    # If it's a "MainData" or "History" table, show a recent sample
                    if "MainData" in table or "History" in table or "Operation" in table:
                        # Try to find a Date or DateTime column
                        date_col = next((c for c in cols if "Date" in c), None)
                        
                        # Print last few rows to see if they are recent
                        print("    - First 3 values in %s: %s" % (cols[0], data[cols[0]][:3]))
                        if date_col:
                            print("    - Sample Dates from %s: %s" % (date_col, data[date_col][-3:]))
            except Exception as e:
                # Some system tables might fail, ignore them
                pass
                
    except Exception as e:
        print("[!] Fatal: %s" % str(e))

if __name__ == "__main__":
    deep_inspect()
