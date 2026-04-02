import os
import time

def find_recent_changes_safe():
    print("[*] Searching for files modified in the last 10 minutes (Loop-Safe)...")
    now = time.time()
    ten_mins = 10 * 60
    
    found_count = 0
    visited = set()
    
    # Focused search paths
    search_roots = ["C:\\TEXNO UZ 1", "C:\\Users\\ids\\AppData", "C:\\ProgramData", "C:\\Windows\\System32"]
    
    for r in search_roots:
        if not os.path.exists(r): continue
        print(f"[*] Scanning: {r}")
        for root, dirs, files in os.walk(r, followlinks=False):
            try:
                # Junction bypass
                real_path = os.path.realpath(root).lower()
                if real_path in visited:
                    dirs[:] = []
                    continue
                visited.add(real_path)
            except: continue

            for file in files:
                path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(path)
                    if (now - mtime) < ten_mins:
                        size = os.path.getsize(path)
                        # Filter for potential DB files (> 50KB)
                        if size > 50 * 1024:
                            print(f"[ACTIVE]: {time.ctime(mtime)} | {path} | {size//1024} KB")
                            found_count += 1
                except: pass

    print(f"\n[*] Found {found_count} active files.")

if __name__ == "__main__":
    find_recent_changes_safe()
