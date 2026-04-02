import os
import subprocess

def explore_drives_and_processes():
    print("[*] Exploring drives and processes...")
    
    # 1. List all logical drives
    print("\n[*] Logical Drives:")
    try:
        # Using fsutil via absolute path
        cmd = "C:\\Windows\\System32\\fsutil.exe fsinfo drives"
        res = os.popen(cmd).read()
        print(res)
    except: pass

    # 2. List all running processes with more detail
    print("\n[*] Running Processes (Full List):")
    try:
        cmd = "C:\\Windows\\System32\\tasklist.exe /V /FO CSV"
        res = os.popen(cmd).read()
        # Filter for anything interesting (SQL, Database, Jet, etc.)
        for line in res.splitlines():
            l = line.lower()
            if "sql" in l or "db" in l or "jet" in l or "engine" in l or "server" in l:
                print(line)
            # Also print Texnouz related
            if "texno" in l:
                print(line)
    except: pass

    # 3. Check for hidden folders in C:\ and common data roots
    print("\n[*] Checking root folders on C:...")
    try:
        for item in os.listdir("C:\\"):
            path = "C:\\" + item
            if os.path.isdir(path):
                # Check for hidden/system folders
                print(f"  Folder: {item}")
    except: pass

    # 4. Check for mapped network drives
    print("\n[*] Checking network connections (net use):")
    try:
        cmd = "C:\\Windows\\System32\\net.exe use"
        res = os.popen(cmd).read()
        print(res)
    except: pass

if __name__ == "__main__":
    explore_drives_and_processes()
    print("\n[*] Exploration complete.")
