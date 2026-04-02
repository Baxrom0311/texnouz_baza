import os

def surgical_scan():
    print("[*] Starting surgical scan (Safe version)...")
    base_dirs = [
        "C:\\TEXNO UZ 1",
        "C:\\TEXNO UZ 1\\Texnouz",
        "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software",
        "C:\\TEXNO UZ 1\\fevral 2025",
        "C:\\TEXNO UZ 1\\Март 2025"
    ]
    
    # Files to audit
    files_to_read = [
        "C:\\TEXNO UZ 1\\Texnouz.INI",
        "C:\\TEXNO UZ 1\\Texnouz\\Texnouz.INI",
        "C:\\TEXNO UZ 1\\Texnouz\\conf.inf",
        "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software\\Ini\\Configs.ini"
    ]
    
    for f in files_to_read:
        if os.path.exists(f):
            print(f"\n--- Content of {f} ---")
            try:
                with open(f, "rb") as f_obj:
                    # Read first 1KB and print as text/hex
                    data = f_obj.read(1024).decode('ascii', errors='ignore')
                    print(data)
            except: print("Error reading file")

    print("\n[*] Searching for Lock Files (.ldb / .laccdb) and .mdb in specific folders...")
    for b in base_dirs:
        if not os.path.exists(b): continue
        print(f"Checking: {b}")
        try:
            for item in os.listdir(b):
                path = os.path.join(b, item)
                if os.path.isfile(path):
                    ext = item.lower()
                    if ext.endswith(('.ldb', '.laccdb', '.mdb', '.accdb')):
                        print(f"[FOUND]: {path} | Size: {os.path.getsize(path)} bytes")
                    
                    # Also look for the 03.03.2025 like files and check their headers
                    if "2025" in item:
                        try:
                            with open(path, "rb") as f_obj:
                                header = f_obj.read(16)
                                if b"Standard Jet DB" in header:
                                    print(f"[!!!] JET DB DETECTED: {path}")
                        except: pass
        except: pass

if __name__ == "__main__":
    surgical_scan()
    print("\n[*] Surgical scan complete.")
