import os

def check_file_locks():
    print("[*] Starting Lock Detective (Identifying files held by Texnouz.exe)...")
    target_dir = "C:\\TEXNO UZ 1"
    
    found_locks = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            path = os.path.join(root, file)
            # Skip the EXE itself and common reports to reduce noise
            if file.lower().endswith(('.exe', '.htm', '.html', '.rep')):
                continue
                
            try:
                # Try to open file for appending/writing to see if it's locked
                # If another process (Texnouz) has it open for writing/exclusive, this fails.
                with open(path, "a+b") as f:
                    pass
            except IOError as e:
                # PermissionError/IOError often indicates a lock
                print(f"[LOCKED?]: {path} | Error: {e}")
                found_locks.append(path)
            except Exception as e:
                pass
                
    if not found_locks:
        print("[-] No persistent file locks found in the application directory.")
    else:
        print(f"[*] Found {len(found_locks)} locked files.")

if __name__ == "__main__":
    check_file_locks()
