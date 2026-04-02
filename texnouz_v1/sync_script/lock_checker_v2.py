import os
import time

def check_for_ldb():
    print("[*] Checking for active LDB (Lock) files...")
    
    # Paths where we found MDBs
    check_paths = [
        "C:\\Windows\\System32\\System32.mdb",
        "C:\\TEXNO UZ 1\\Base\\db3.mdb",
        "C:\\TEXNO UZ 1\\Texnouz\\Base\\db3.mdb",
        "C:\\sync_texnouz\\sync_temp_db3.mdb"
    ]
    
    found_ldb = False
    for mdb in check_paths:
        ldb = mdb.replace(".mdb", ".ldb")
        if os.path.exists(ldb):
            print(f"[!!!] ACTIVE LOCK FOUND: {ldb}")
            found_ldb = True
            try:
                mtime = os.path.getmtime(ldb)
                size = os.path.getsize(ldb)
                print(f"      Modified: {time.ctime(mtime)} | Size: {size} bytes")
            except: pass
        else:
            # Also check for .accdb lock (.laccdb)
            laccdb = mdb.replace(".mdb", ".laccdb")
            if os.path.exists(laccdb):
                print(f"[!!!] ACTIVE ACCDB LOCK FOUND: {laccdb}")
                found_ldb = True
    
    if not found_ldb:
        print("[-] No active lock files found at common locations.")
    
    # Broad check in C:\TEXNO UZ 1
    print("\n[*] Broad check in application directories...")
    for root, dirs, files in os.walk("C:\\TEXNO UZ 1"):
        for file in files:
            if file.lower().endswith((".ldb", ".laccdb")):
                print(f"[FOUND LOCK]: {os.path.join(root, file)}")

if __name__ == "__main__":
    check_for_ldb()
