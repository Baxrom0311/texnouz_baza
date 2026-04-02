import os

def master_scan():
    print("[*] Starting Master Scan (Junction-Safe)...")
    visited = set()
    found_count = 0
    
    # We will scan C: and D: excluding only the most obvious system junk
    for drive in ["C:\\", "D:\\"]:
        if not os.path.exists(drive): continue
        print(f"[*] Scanning Drive: {drive}")
        
        for root, dirs, files in os.walk(drive):
            # Resolve real path to avoid junction loops
            try:
                real_root = os.path.realpath(root).lower()
                if real_root in visited:
                    dirs[:] = [] # Don't descend
                    continue
                visited.add(real_root)
            except: continue

            # Skip common heavy system folders to save time
            if any(x in real_root for x in ["\\windows\\winsxs", "\\windows\\servicing", "\\program files\\microsoft"]):
                dirs[:] = []
                continue

            for file in files:
                path = os.path.join(root, file)
                try:
                    # Look for ANY file > 1MB that is NOT a common system extension
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".exe", ".dll", ".sys", ".msi", ".zip", ".rar", ".iso", ".htm", ".html", ".log"]:
                        continue
                        
                    size = os.path.getsize(path)
                    if size > 500 * 1024: # > 500KB
                        mtime = os.path.getmtime(path)
                        print(f"[FOUND]: {path} | Size: {size//1024} KB | Mod: {time.ctime(mtime)}")
                        found_count += 1
                        
                        # Check header for database signatures
                        with open(path, "rb") as f:
                            header = f.read(16)
                            if b"Standard Jet DB" in header:
                                print(f"  [!!!] ACCESS DATABASE IDENTIFIED!")
                            elif b"SQLite format 3" in header:
                                print(f"  [+] SQLite Database identified.")
                except: pass
    
    print(f"\n[*] Master scan complete. Found {found_count} interesting files.")

if __name__ == "__main__":
    import time
    master_scan()
