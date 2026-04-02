import os
import subprocess

def check_process_wmic():
    print("[*] Trying to get process info via absolute wmic path...")
    wmic_bin = "C:\\Windows\\System32\\wbem\\wmic.exe"
    if not os.path.exists(wmic_bin):
        print(f"[-] wmic not at {wmic_bin}")
        wmic_bin = "wmic" # Fallback
    
    cmd = f"\"{wmic_bin}\" process where \"name='Texnouz.exe'\" get ExecutablePath, WorkingDirectory, CommandLine /format:list"
    print(f"[*] Running: {cmd}")
    try:
        res = os.popen(cmd).read()
        print(f"[PROCESS INFO]:\n{res}")
    except Exception as e:
        print(f"[!] Error: {e}")

def scan_folders_exhaustively():
    base_dir = "C:\\TEXNO UZ 1"
    print(f"[*] Exhaustive scan of {base_dir} for any MDB or large files...")
    
    for root, dirs, files in os.walk(base_dir):
        print(f"  Scanning: {root}")
        for file in files:
            path = os.path.join(root, file)
            try:
                ext = os.path.splitext(file)[1].lower()
                size = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                
                # Check for MDB/ACCDB regardless of date
                # Or any file modified in the last 24 hours
                import time
                is_recent = (time.time() - mtime) < (24 * 3600)
                
                if ext in ['.mdb', '.accdb', '.db'] or is_recent or size > 1024*1024:
                    print(f"[!!!] INTERESTING: {path} | Size: {size//1024} KB | Mod: {time.ctime(mtime)}")
                    
                    # If it's a recent file but not an MDB, let's peek at the first few bytes
                    if is_recent and ext not in ['.exe', '.dll', '.htm', '.log']:
                        with open(path, "rb") as f:
                            header = f.read(16)
                            print(f"      Header: {header.hex()}")
            except:
                pass

if __name__ == "__main__":
    check_process_wmic()
    scan_folders_exhaustively()
    print("[*] Scan complete.")
