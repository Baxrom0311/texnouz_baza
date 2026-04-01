import os
import time
from access_parser import AccessParser

# Hacker Mode: Forensic discovery script
# Targeted search for active databases

EXTENSIONS = ['.mdb', '.accdb', '.db', '.sqlite', '.fdb', '.gdb', '.dat']
KEYWORDS = ['main', 'base', 'data', 'texnouz', 'db3']
TARGET_TABLE = 'tabmaindata'

def get_modified_today(path):
    try:
        mtime = os.path.getmtime(path)
        # Check if modified in the last 48 hours
        if (time.time() - mtime) < (48 * 3600):
            return True
    except:
        pass
    return False

def scan():
    drives = ['D:\\', 'C:\\'] 
    print("[*] Hacker Mode Discovery started...")
    
    for drive in drives:
        if not os.path.exists(drive): continue
        print(f"[*] Scanning {drive} drive...")
        
        for root, dirs, files in os.walk(drive):
            # Skip infinite loops and system dirs
            low_root = root.lower()
            if any(x in low_root for x in ['windows', 'application data', 'temp', 'recycle.bin']):
                dirs[:] = []
                continue
            
            # Depth limit to avoid getting stuck
            if root.count(os.sep) > 10:
                dirs[:] = []
                continue

            for file in files:
                low_file = file.lower()
                path = os.path.join(root, file)
                
                is_db_ext = any(low_file.endswith(ext) for ext in EXTENSIONS)
                is_modified_today = get_modified_today(path)
                
                # Report if it's a DB extension OR a large file modified today
                if is_db_ext or (is_modified_today and os.path.getsize(path) > 1000000):
                    try:
                        size = os.path.getsize(path)
                        print(f"[+] Found: {path} | Size: {size//1024} KB | Mod: {time.ctime(os.path.getmtime(path))}")
                        
                        # If it's MDB, check for the table
                        if low_file.endswith('.mdb'):
                            try:
                                db = AccessParser(path)
                                tables = [t.lower() for t in db.catalog.keys()]
                                if TARGET_TABLE in tables:
                                    print(f"!!! CRITICAL HIT: '{TARGET_TABLE}' found in {path} !!!")
                                    return path
                            except:
                                pass
                    except:
                        pass

if __name__ == "__main__":
    result = scan()
    if result:
        print(f"\n[!] SUCCESS! Operational database identified at: {result}")
    else:
        print("\n[-] No operational database found. Checking remote registry...")
