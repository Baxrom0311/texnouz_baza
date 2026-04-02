import os

def check_headers_and_network():
    print("[*] Starting detective work (Phase 4)...")
    
    # 1. Check network connections for Texnouz.exe (PID 11876)
    print("\n[*] Checking network connections for PID 11876...")
    try:
        netstat_cmd = "C:\\Windows\\System32\\netstat.exe -ano"
        res = os.popen(netstat_cmd).read()
        for line in res.splitlines():
            if "11876" in line:
                print(line.strip())
    except: pass

    # 2. Check headers of suspicious files
    suspicious_files = [
        "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software.doc",
        "C:\\TEXNO UZ 1\\Март 2025\\03.03.2025",
        "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software\\Ini\\Configs.ini"
    ]
    
    # Also scan Март 2025 and 2025 folders for ANY file and check header
    extra_folders = ["C:\\TEXNO UZ 1\\Март 2025", "C:\\TEXNO UZ 1\\fevral 2025", "C:\\TEXNO UZ 1\\ 2025"]
    
    for f in suspicious_files:
        if os.path.exists(f):
            print(f"\n--- Header of {f} ---")
            try:
                with open(f, "rb") as f_obj:
                    header = f_obj.read(100)
                    print(f"Hex: {header[:32].hex()}")
                    print(f"ASCII: {header[:64].decode('ascii', errors='ignore')}")
                    if b"Standard Jet DB" in header:
                        print("[!!!] JET DB DETECTED")
            except: pass

    print("\n[*] Scanning monthly folders for JET DB signature...")
    for folder in extra_folders:
        if os.path.exists(folder):
            print(f"Folder: {folder}")
            try:
                for item in os.listdir(folder):
                    path = os.path.join(folder, item)
                    if os.path.isfile(path) and os.path.getsize(path) > 10*1024:
                        try:
                            with open(path, "rb") as f_obj:
                                header = f_obj.read(100)
                                if b"Standard Jet DB" in header:
                                    print(f"  [!!!] JET DB FOUND: {path}")
                        except: pass
            except: pass

if __name__ == "__main__":
    check_headers_and_network()
    print("\n[*] Detective work complete.")
