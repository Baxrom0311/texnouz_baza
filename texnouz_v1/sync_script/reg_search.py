import os

def registry_deep_search():
    print("[*] Starting deep registry search for 'tabMainData' and app hash...")
    reg_bin = "C:\\Windows\\System32\\reg.exe"
    app_hash = "c5d60739f84947658a9a144d86548ecc"
    
    queries = [
        "tabMainData",
        app_hash,
        "Texnouz",
        "Texno Uz"
    ]
    
    roots = ["HKCU", "HKLM"]
    
    for q in queries:
        print(f"\n[*] Searching for query: '{q}'")
        for root in roots:
            # We search recursively. This might be slow but we filter for keys.
            # Actually, reg query /f is more efficient.
            cmd = f"\"{reg_bin}\" query {root} /f \"{q}\" /s /e"
            print(f"  Root: {root}...")
            try:
                # Limit output to first 20 matches per query to avoid overflow
                res = os.popen(cmd).read()
                if "End of search" not in res and res.strip():
                    print(f"[FOUND MATCHES in {root}]:\n{res[:2048]}")
                else:
                    print(f"  [-] No matches in {root}.")
            except: pass

if __name__ == "__main__":
    registry_deep_search()
    print("\n[*] Registry deep search complete.")
