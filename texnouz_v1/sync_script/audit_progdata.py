import os
import time

def audit_programdata():
    print("[*] Auditing C:\\ProgramData for Texno Uz data...")
    target = "C:\\ProgramData"
    now = time.time()
    
    if not os.path.exists(target):
        print("[-] C:\\ProgramData not found.")
        return

    found_any = False
    for root, dirs, files in os.walk(target):
        # Focus on anything with 'Texno' or 'MMS'
        root_lower = root.lower()
        if "texno" in root_lower or "mms" in root_lower:
            print(f"\n[FOUND APP DIR]: {root}")
            for file in files:
                path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(path)
                    size = os.path.getsize(path)
                    print(f"  - {file} | Size: {size//1024} KB | Mod: {time.ctime(mtime)}")
                    found_any = True
                except: pass
        
        # Also check for ANY large MDB/DB file in ProgramData
        for file in files:
            if file.lower().endswith((".mdb", ".db", ".dbf", ".dat")):
                path = os.path.join(root, file)
                try:
                    size = os.path.getsize(path)
                    if size > 500 * 1024:
                        mtime = os.path.getmtime(path)
                        # If modified today
                        if (now - mtime) < 24 * 3600:
                            print(f"\n[FOUND RECENT DB]: {path} | Size: {size//1024} KB | Mod: {time.ctime(mtime)}")
                            found_any = True
                except: pass

    if not found_any:
        print("[-] No obvious Texno Uz data found in C:\\ProgramData.")

if __name__ == "__main__":
    audit_programdata()
