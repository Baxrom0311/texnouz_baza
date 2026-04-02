import os

def find_lock_files():
    print("[*] Searching for active Access lock files (.ldb, .laccdb)...")
    drives = ['C:\\', 'D:\\']
    exclude = ['windows', 'program files', 'program files (x86)']
    
    for drive in drives:
        if not os.path.exists(drive): continue
        print(f"[*] Checking drive {drive}...")
        for root, dirs, files in os.walk(drive):
            # Skip system folders
            dirs[:] = [d for d in dirs if d.lower() not in exclude]
            
            for file in files:
                if file.lower().endswith(('.ldb', '.laccdb')):
                    path = os.path.join(root, file)
                    print(f"[FOUND LOCK FILE]: {path}")
                    # If we find a lock file, the DB is likely the same name but with .mdb/.accdb
                    base = os.path.splitext(path)[0]
                    for ext in ['.mdb', '.accdb']:
                        db_path = base + ext
                        if os.path.exists(db_path):
                            print(f"  [!] MATCHING DB FOUND: {db_path} (Size: {os.path.getsize(db_path)//1024} KB)")

def check_virtualstore():
    print("[*] Checking VirtualStore for redirected app data...")
    vs_path = os.path.expanduser("~\\AppData\\Local\\VirtualStore")
    if os.path.exists(vs_path):
        print(f"[+] VirtualStore exists at {vs_path}")
        for root, dirs, files in os.walk(vs_path):
            for file in files:
                if file.lower().endswith(('.mdb', '.accdb')):
                    path = os.path.join(root, file)
                    print(f"[!] REDIRECTED DB FOUND: {path} (Size: {os.path.getsize(path)//1024} KB)")
    else:
        print("[-] VirtualStore not found.")

if __name__ == "__main__":
    find_lock_files()
    check_virtualstore()
    print("[*] Search complete.")
