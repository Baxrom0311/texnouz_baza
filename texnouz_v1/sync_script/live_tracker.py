import os
import time

def high_res_tracker():
    print("[*] Starting high-resolution activity tracker...")
    # Monitor for 60 seconds and watch for ANY file change in C:\TEXNO UZ 1
    # or C:\Users\ids\AppData
    target_dirs = ["C:\\TEXNO UZ 1", os.path.expandvars("%LOCALAPPDATA%\\VirtualStore")]
    
    print(f"[*] Monitoring {target_dirs} for 30 seconds... (Please trigger a report in the app if possible!)")
    
    initial_snapshot = {}
    for d in target_dirs:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            for file in files:
                path = os.path.join(root, file)
                try: initial_snapshot[path] = os.path.getmtime(path)
                except: pass
    
    time.sleep(30)
    
    print("[*] Checking for changes...")
    for d in target_dirs:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            for file in files:
                path = os.path.join(root, file)
                try:
                    new_mtime = os.path.getmtime(path)
                    if path not in initial_snapshot or new_mtime > initial_snapshot[path]:
                        print(f"[CHANGE DETECTED]: {path} | Size: {os.path.getsize(path)} bytes")
                except: pass

def check_modules():
    print("\n[*] Checking loaded modules for Texnouz.exe...")
    try:
        cmd = "C:\\Windows\\System32\\tasklist.exe /M /FI \"IMAGENAME eq Texnouz.exe\""
        res = os.popen(cmd).read()
        print(res)
    except: pass

if __name__ == "__main__":
    check_modules()
    high_res_tracker()
