import os
import time

def find_recent_changes():
    print("[*] Searching for files modified in the last 60 minutes...")
    now = time.time()
    one_hour = 60 * 60
    
    found_count = 0
    # Scan C: root and typical data folders
    search_roots = ["C:\\TEXNO UZ 1", "C:\\Users\\ids\\AppData\\Local", "C:\\Windows\\System32"]
    
    for r in search_roots:
        if not os.path.exists(r): continue
        print(f"[*] Scanning Folder: {r}")
        for root, dirs, files in os.walk(r):
            for file in files:
                path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(path)
                    if (now - mtime) < one_hour:
                        size = os.path.getsize(path)
                        # We want data files, so > 1KB
                        if size > 1024:
                            print(f"[RECENT]: {time.ctime(mtime)} | {path} | {size//1024} KB")
                            found_count += 1
                except: pass

    print(f"\n[*] Search complete. Found {found_count} files.")

if __name__ == "__main__":
    find_recent_changes()
