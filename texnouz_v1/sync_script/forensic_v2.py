import os
import sys
import time

def check_env():
    print("[*] System Environment Check:")
    print(f"Python: {sys.version}")
    print(f"CWD: {os.getcwd()}")
    print(f"PATH: {os.environ.get('PATH', 'NOT SET')}")
    
    potential_system32 = "C:\\Windows\\System32"
    if os.path.exists(potential_system32):
        print(f"[+] System32 exists at {potential_system32}")
        files = ["tasklist.exe", "net.exe", "reg.exe", "findstr.exe"]
        for f in files:
            path = os.path.join(potential_system32, f)
            if os.path.exists(path):
                print(f"  [v] {f} exists")
            else:
                print(f"  [x] {f} NOT FOUND")

def check_registry():
    print("[*] Checking registry for potential database paths...")
    reg_bin = "C:\\Windows\\System32\\reg.exe"
    # Standard 32-bit ODBC locations
    reg_paths = [
        "Software\\ODBC\\ODBC.INI",
        "Software\\Wow6432Node\\ODBC\\ODBC.INI",
        "Software\\Texno Uz",
        "Software\\Texnouz"
    ]
    for p in reg_paths:
        for hive in ["HKCU", "HKLM"]:
            cmd = f"\"{reg_bin}\" query \"{hive}\\{p}\" /s"
            print(f"[*] Querying {hive}: {p}")
            try:
                res = os.popen(cmd).read()
                if ".mdb" in res.lower() or "dbq" in res.lower():
                    print(f"[!] HINT FOUND in Registry ({hive}\\{p}):\n{res}")
            except: pass

def get_process_info():
    print("[*] Checking running processes...")
    tasklist_bin = "C:\\Windows\\System32\\tasklist.exe"
    commands = [
        f"\"{tasklist_bin}\" /V /FI \"IMAGENAME eq Texnouz.exe\"",
        f"\"{tasklist_bin}\" /M /FI \"IMAGENAME eq Texnouz.exe\""
    ]
    for cmd in commands:
        print(f"[*] Running: {cmd}")
        try:
            res = os.popen(cmd).read()
            if "Texnouz.exe" in res:
                print(f"[+] FOUND:\n{res}")
            else:
                print("[-] Not found in this output.")
        except Exception as e:
            print(f"[!] Error: {e}")

def scan_hot_files():
    print("[*] Scanning for recently modified database candidates...")
    drives = ['C:\\', 'D:\\']
    # Exclude directories to speed up and avoid permission issues/junction loops
    exclude_dirs = set(['windows', 'system volume information', '$recycle.bin', 'program files', 'program files (x86)', 'temp', 'documents and settings'])
    
    candidates = []
    
    for drive in drives:
        if not os.path.exists(drive): continue
        print(f"[*] Scanning {drive}...")
        for root, dirs, files in os.walk(drive, followlinks=False):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs]
            
            # Avoid deep recursion loops (Application Data junction madness)
            if root.count(os.sep) > 8:
                dirs[:] = []
                continue

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.mdb', '.accdb', '.dat', '.db']:
                    path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(path)
                        # Modified in last 72 hours
                        if (time.time() - mtime) < (72 * 3600):
                            size = os.path.getsize(path)
                            if size > 1024: # Skip empty ones
                                candidates.append((path, size, mtime))
                                print(f"[?] Candidate: {path} | Size: {size//1024}KB | Mod: {time.ctime(mtime)}")
                    except:
                        pass
    return candidates

if __name__ == "__main__":
    check_env()
    check_registry()
    get_process_info()
    scan_hot_files()
    print("[*] Forensic scan complete.")
