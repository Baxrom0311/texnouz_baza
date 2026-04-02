import os

def audit_documents_folder():
    print("[*] Auditing User Documents and potential data folders...")
    
    # 1. Check the path from registry
    target_docs = "C:\\Users\\MMS PREMIUM\\Documents"
    if os.path.exists(target_docs):
        print(f"\n[*] Found Registry Documents folder: {target_docs}")
        for root, dirs, files in os.walk(target_docs):
            for file in files:
                path = os.path.join(root, file)
                try:
                    size = os.path.getsize(path)
                    if size > 100*1024:
                        mtime = os.path.getmtime(path)
                        import time
                        print(f"[DOCS MATCH]: {time.ctime(mtime)} | {path} | {size//1024} KB")
                        
                        # Check for JET/SQLite signature
                        with open(path, "rb") as f:
                            header = f.read(16)
                            if b"Standard Jet DB" in header:
                                print("  [!!!] DATABASE FOUND IN DOCUMENTS!")
                except: pass
    else:
        print(f"[-] Path {target_docs} not found.")

    # 2. Check for ANY 'Texno' related folder in C:\Users
    print("\n[*] Searching for 'Texno' in all User profiles...")
    for user_dir in os.listdir("C:\\Users"):
        path = os.path.join("C:\\Users", user_dir)
        if os.path.isdir(path):
            # Check for common subfolders
            for sub in ["AppData\\Local", "AppData\\Roaming", "Documents"]:
                target = os.path.join(path, sub)
                if os.path.exists(target):
                    for item in os.listdir(target):
                        if "texno" in item.lower():
                            print(f"[FOUND PROBABLE DIR]: {os.path.join(target, item)}")

if __name__ == "__main__":
    audit_documents_folder()
    print("\n[*] Documents audit complete.")
