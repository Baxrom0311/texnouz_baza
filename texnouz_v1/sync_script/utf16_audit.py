import os

def utf16_scan():
    print("[*] Starting UTF-16 and OLE2 audit...")
    target_dir = "C:\\TEXNO UZ 1"
    search_string = "tabMainData"
    
    # 1. Search for UTF-16 encoded string
    # In UTF-16LE, "t" is "t\x00", "a" is "a\x00", etc.
    utf16_le = search_string.encode('utf-16le')
    print(f"[*] Searching for UTF-16LE signature: {utf16_le.hex()}")
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size > 10*1024 and size < 100*1024*1024: # 10KB to 100MB
                    with open(path, "rb") as f:
                        # Read in chunks
                        chunk = f.read(1024 * 1024) # 1MB
                        if utf16_le in chunk:
                            print(f"[!!!] UTF-16 MATCH FOUND: {path}")
            except: pass

    # 2. Try to peek inside the .doc file if it's an OLE container
    doc_path = "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software.doc"
    if os.path.exists(doc_path):
        print(f"\n[*] Auditing {doc_path} for database evidence...")
        try:
            with open(doc_path, "rb") as f:
                content = f.read(1024 * 64) # 64KB
                if b"tabMainData" in content or utf16_le in content:
                    print(f"[!!!] SIGNATURE FOUND IN .DOC FILE!")
                if b"Standard Jet DB" in content:
                    print(f"[!!!] JET DB SIGNATURE IN .DOC FILE!")
        except: pass

if __name__ == "__main__":
    utf16_scan()
    print("\n[*] Audit complete.")
