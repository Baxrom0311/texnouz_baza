import os

def discovery_d_drive():
    print("[*] Starting discovery on D: drive...")
    findstr_bin = "C:\\Windows\\System32\\findstr.exe"
    target_dir = "D:\\TEXNO UZ 1"
    
    if not os.path.exists(target_dir):
        print(f"[-] Directory {target_dir} not found on D:")
        return

    # 1. Search for 'tabMainData' string on D:
    print(f"\n[*] Searching for 'tabMainData' in {target_dir}...")
    cmd = f"\"{findstr_bin}\" /s /m /i /c:\"tabMainData\" \"{target_dir}\\*.*\""
    try:
        res = os.popen(cmd).read()
        print(f"[SEARCH RESULTS D:]:\n{res}")
    except: pass

    # 2. Find ANY file on D: modified in 2026
    print("\n[*] Searching for ANY file on D: modified in 2026...")
    for root, dirs, files in os.walk("D:\\"):
        for file in files:
            path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(path)
                import time
                mtime_struct = time.localtime(mtime)
                if mtime_struct.tm_year == 2026:
                    print(f"[2026 FILE]: {path} | Size: {os.path.getsize(path)//1024} KB | Mod: {time.ctime(mtime)}")
            except: pass

    # 3. Check for any .INI files on D:
    print("\n[*] Checking for configuration files on D:...")
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.ini'):
                print(f"[INI ON D:]: {os.path.join(root, file)}")

if __name__ == "__main__":
    discovery_d_drive()
    print("\n[*] D: drive discovery complete.")
