import os

def global_jet_hunt():
    print("[*] Starting Global Jet DB Hunt (Byte-level scan)...")
    visited = set()
    found_count = 0
    
    # JET Signature: \x00\x01\x00\x00Standard Jet DB
    jet_sig = b"\x00\x01\x00\x00Standard Jet DB"
    
    # We scan C: and D: roots and typical data folders
    search_roots = ["C:\\", "D:\\"]
    
    for drive in search_roots:
        if not os.path.exists(drive): continue
        print(f"[*] Scanning Drive: {drive}")
        
        for root, dirs, files in os.walk(drive):
            try:
                real_root = os.path.realpath(root).lower()
                if real_root in visited:
                    dirs[:] = []
                    continue
                visited.add(real_root)
            except: continue

            # Exclude only the most extreme system junk to be thorough
            if any(x in real_root for x in ["\\windows\\winsxs", "\\windows\\servicing"]):
                dirs[:] = []
                continue

            for file in files:
                path = os.path.join(root, file)
                try:
                    # Filter by size to avoid scanning small junk (DB should be > 100KB)
                    size = os.path.getsize(path)
                    if size > 100 * 1024:
                        with open(path, "rb") as f:
                            header = f.read(20)
                            if jet_sig in header:
                                print(f"[!!!] JET DATABASE IDENTIFIED: {path} | Size: {size//1024} KB")
                                found_count += 1
                                # Check if it contains tabMainData
                                # (We read a bit more for metadata)
                                try:
                                    f.seek(0)
                                    content = f.read(524288) # Read 512KB
                                    if b"tabMainData" in content:
                                        print("  |-- [MATCH] Contains 'tabMainData'!")
                                except: pass
                except: pass
    
    print(f"\n[*] Global hunt complete. Found {found_count} Jet databases.")

if __name__ == "__main__":
    global_jet_hunt()
