import os
import re

def resolve_lnk_files():
    recent_path = os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Recent")
    print(f"[*] Resolving .lnk files in {recent_path}...")
    
    if not os.path.exists(recent_path):
        print("[-] Recent path not found.")
        return

    # Pattern for Windows paths (e.g., C:\...)
    # Using regex to find strings that look like absolute paths
    path_regex = re.compile(br'[a-zA-Z]:\\[^ \x00-\x1f\x7f-\xff]*')

    for file in os.listdir(recent_path):
        if file.lower().endswith(".lnk"):
            path = os.path.join(recent_path, file)
            print(f"\n--- Link: {file} ---")
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    # Find all path-like byte strings
                    matches = path_regex.findall(content)
                    found_any = False
                    for m in matches:
                        try:
                            decoded = m.decode('ascii', errors='ignore')
                            if len(decoded) > 5:
                                print(f"  [POTENTIAL TARGET]: {decoded}")
                                found_any = True
                        except: pass
                    if not found_any:
                        print("  [-] No clear path found in content.")
            except Exception as e:
                print(f"  [!] Error reading {file}: {e}")

if __name__ == "__main__":
    resolve_lnk_files()
    print("\n[*] Resolution complete.")
