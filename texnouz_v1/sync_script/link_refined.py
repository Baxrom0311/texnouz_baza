import os
import re

def resolve_lnk_refined():
    recent_path = os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Recent")
    print(f"[*] Refining resolution for .lnk files in {recent_path}...")
    
    # Path regex that allows spaces but stops at null or certain non-path chars
    # Windows paths don't allow certain chars.
    path_regex = re.compile(br'[a-zA-Z]:\\[^\|\<\>\?\"\x00-\x1f]*', re.IGNORECASE)

    for file in os.listdir(recent_path):
        if file.lower().endswith(".lnk"):
            path = os.path.join(recent_path, file)
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    matches = path_regex.findall(content)
                    print(f"\n--- {file} ---")
                    seen = set()
                    for m in matches:
                        try:
                            # Clean up trailing special chars that might be picked up
                            decoded = m.decode('ascii', errors='ignore').strip()
                            # Often paths in LNK are followed by some junk, we take until the first nul if found manually
                            # but regex already helps. Let's filter for realistic lengths and content.
                            if len(decoded) > 5 and "C:\\" in decoded:
                                # Further cleaning: stop at double nul or common LNK junk
                                if decoded not in seen:
                                    print(f"  [PATH]: {decoded}")
                                    seen.add(decoded)
                        except: pass
            except Exception as e:
                print(f"  [!] Error: {e}")

def check_specific_locations():
    print("\n[*] Checking specific suspicious locations manually...")
    locs = [
        "C:\\TEXNO UZ 1\\db3.mdb",
        "C:\\TEXNO UZ 1\\Base\\db3.mdb",
        "C:\\TEXNO UZ 1\\Texnouz\\db3.mdb",
        "C:\\TEXNO UZ 1\\Mass Flowmeter Communications Management software\\db3.mdb",
        "C:\\TEXNO UZ 1\\Март 2025\\03.03.2025"
    ]
    for l in locs:
        if os.path.exists(l):
            print(f"[FOUND]: {l} | Size: {os.path.getsize(l)//1024} KB | Mod: {time.ctime(os.path.getmtime(l)) if 'time' in globals() else 'N/A'}")
        else:
            print(f"[-] Not at {l}")

if __name__ == "__main__":
    import time
    resolve_lnk_refined()
    check_specific_locations()
