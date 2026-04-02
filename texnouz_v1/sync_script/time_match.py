import os
import time

def find_concurrent_files():
    # Today's report was modified around 17:40 (17:40:13)
    # Let's find anything modified in that window or generally in the last hour
    print("[*] Searching for files modified concurrently with reports (around 17:40)...")
    
    current_time = time.time()
    # We'll check the last 3 hours to be safe
    base_dir = "C:\\TEXNO UZ 1"
    
    found = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(path)
                if (current_time - mtime) < (4 * 3600): # Last 4 hours
                    found.append((mtime, path))
            except: pass
    
    # Sort by time
    found.sort()
    for mt, p in found:
        print(f"[TIME MATCH]: {time.ctime(mt)} | {p} | Size: {os.path.getsize(p)//1024} KB")

def audit_configs_extra():
    files = [
        "C:\\TEXNO UZ 1\\Texnouz\\TexnoNew.INI",
        "C:\\TEXNO UZ 1\\Texnouz\\Texnouz.INI",
        "C:\\TEXNO UZ 1\\Texnouz\\Configs.ini"
    ]
    for f in files:
        if os.path.exists(f):
            print(f"\n--- {f} ---")
            try:
                with open(f, "r", encoding='ascii', errors='ignore') as f_obj:
                    print(f_obj.read())
            except: pass

if __name__ == "__main__":
    find_concurrent_files()
    audit_configs_extra()
    print("\n[*] Concurrent discovery complete.")
