import os
import time

def find_recent_files_broad():
    print("[*] Searching for ANY file modified in the last 2 hours on C:...")
    drive = "C:\\"
    exclude = ['windows', 'program files', 'program files (x86)', 'appdata', 'documents and settings']
    
    current_time = time.time()
    count = 0
    
    for root, dirs, files in os.walk(drive):
        # Skip excluded
        dirs[:] = [d for d in dirs if d.lower() not in exclude]
        
        # Deep loop protection
        if root.count(os.sep) > 10:
            dirs[:] = []
            continue

        for file in files:
            path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(path)
                if (current_time - mtime) < (2 * 3600): # 2 hours
                    size = os.path.getsize(path)
                    print(f"[RECENT]: {path} | Size: {size//1024} KB | Mod: {time.ctime(mtime)}")
                    count += 1
                    
                    # If it's a suspicious file (>100KB, not common junk), check header
                    if size > 100*1024 and not file.lower().endswith(('.log', '.tmp', '.htm', '.xml', '.txt', '.evtx')):
                        with open(path, "rb") as f:
                            header = f.read(100)
                            if b"Standard Jet DB" in header:
                                print(f"  [!!!] DATABASE SIGNATURE MATCH AT: {path}")
                            else:
                                print(f"  Header Start: {header[:16].hex()}")
            except: pass
            
    print(f"[*] Found {count} recent files.")

if __name__ == "__main__":
    find_recent_files_broad()
