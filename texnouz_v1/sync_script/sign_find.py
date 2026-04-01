import os

def find_signature():
    target_dir = "C:\\TEXNO UZ 1"
    signature = b"tabMainData"
    print(f"[*] Searching for '{signature.decode()}' signature in {target_dir}...")
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            path = os.path.join(root, file)
            try:
                # FAQ: Some DBs might be large, so we read in chunks or just the beginning/middle
                # But here we'll check the first 1MB which usually contains the catalog
                with open(path, "rb") as f:
                    content = f.read(1024 * 1024) # 1MB
                    if signature.lower() in content.lower():
                        print(f"[!!!] SIGNATURE FOUND: {path} (Size: {os.path.getsize(path)//1024} KB)")
                        # Also check if it's an Jet DB
                        if b"Standard Jet DB" in content:
                            print(f"[+] Verified as Jet Database: {path}")
            except:
                pass

if __name__ == "__main__":
    find_signature()
    print("[*] Signature search complete.")
