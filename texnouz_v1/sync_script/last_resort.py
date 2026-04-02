import os

def last_resort_scan():
    print("[*] Starting Last Resort Scan...")
    target_dir = "C:\\TEXNO UZ 1"
    
    # 1. List every file > 100KB with its header
    print("\n[*] Auditing all files > 100KB for signatures...")
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size > 100 * 1024:
                    with open(path, "rb") as f:
                        header = f.read(32)
                        print(f"[FILE]: {path} | Size: {size//1024} KB")
                        print(f"  Header(Hex): {header.hex()}")
                        # Common signatures
                        if b"Standard Jet DB" in header:
                            print("  [!!!] JET DATABASE FOUND!")
                        if b"SQLite format 3" in header:
                            print("  [!!!] SQLITE DATABASE FOUND!")
                        if b"tabMainData" in header:
                            print("  [!!!] tabMainData found in header!")
            except: pass

    # 2. Check for some specific hidden files
    paths = [
        "C:\\TEXNO UZ 1\\db3.mdb",
        "C:\\TEXNO UZ 1\\Base\\db3.mdb",
        "C:\\TEXNO UZ 1\\Texnouz.dat",
        "C:\\TEXNO UZ 1\\Texnouz.bin",
        "C:\\TEXNO UZ 1\\Texno.db"
    ]
    for p in paths:
        if os.path.exists(p):
            print(f"[EXISTS]: {p} | Size: {os.path.getsize(p)}")

if __name__ == "__main__":
    last_resort_scan()
    print("\n[*] Last resort scan complete.")
