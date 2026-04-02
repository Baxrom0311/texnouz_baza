import sys
import os
import shutil
from access_parser import AccessParser

def get_db_info():
    copy_db = r"C:\sync_texnouz\active_copy.mdb"
    
    if not os.path.exists(copy_db):
        print("[!] Copy not found.")
        return

    try:
        db = AccessParser(copy_db)
        target_tables = ['tabMainData', 'tabOperation']
        
        for table in target_tables:
            if table not in db.catalog:
                continue
                
            print("\n" + "="*40)
            print("[TABLE]: %s" % table)
            
            data = db.parse_table(table)
            cols = list(data.keys())
            
            # Determine number of rows
            num_rows = 0
            if cols:
                num_rows = len(data[cols[0]])
            
            print("[+] Columns: %d | Rows: %d" % (len(cols), num_rows))
            
            # Zip columns into rows
            rows = []
            for i in range(min(num_rows, 5)): # Get first 5 rows
                row = {}
                for col in cols:
                    row[col] = data[col][i]
                rows.append(row)
            
            print("[+] Data Sample (First 5 rows):")
            for idx, r in enumerate(rows):
                print("  ROW %d: ID=%s, Date=%s, Time=%s, Liters=%s, Money=%s" % (
                    idx, 
                    str(r.get('DataID', '?')), 
                    str(r.get('Date', '?')), 
                    str(r.get('Time', '?')), 
                    str(r.get('Liters', '?')), 
                    str(r.get('TotalMoney', '?'))
                ))
                # Print full row for first one
                if idx == 0:
                    print("    FULL DATA: %s" % str(r))
            
    except Exception as e:
        print("[!] Error: %s" % str(e))

if __name__ == "__main__":
    get_db_info()
