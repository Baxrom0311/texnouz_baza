import os
from access_parser import AccessParser
from tabulate import tabulate

def inspect_db_data():
    target = "C:\\Windows\\System32\\System32.mdb"
    print(f"[*] Inspecting Data in: {target}")
    
    if not os.path.exists(target):
        print("[-] File not found.")
        return

    try:
        db = AccessParser(target)
        # Main operational tables
        tables = ["tabMainData", "tabOperation", "tabPartner", "tabStorage", "tabGasType"]
        
        for table_name in tables:
            if table_name in db.catalog:
                print(f"\n[TABLE]: {table_name}")
                try:
                    # Robust iteration to handle generators or lists
                    data_iter = db.parse_table(table_name)
                    
                    rows = []
                    total_count = 0
                    for row in data_iter:
                        if total_count < 5:
                            # Clean up row for display
                            clean_row = {}
                            for k, v in row.items():
                                if isinstance(v, bytes):
                                    clean_row[k] = f"<binary {len(v)}b>"
                                elif len(str(v)) > 50:
                                    clean_row[k] = str(v)[:47] + "..."
                                else:
                                    clean_row[k] = v
                            rows.append(clean_row)
                        total_count += 1
                    
                    print(f"[*] Total Records Found: {total_count}")
                    if rows:
                        print(tabulate(rows, headers="keys", tablefmt="grid"))
                    else:
                        print("[-] Table is empty.")
                except Exception as table_err:
                    print(f"[!] Error reading table {table_name}: {table_err}")
            else:
                print(f"\n[-] Table {table_name} not found in database.")

    except Exception as e:
        print(f"[!] Critical error during inspection: {e}")

if __name__ == "__main__":
    inspect_db_data()
