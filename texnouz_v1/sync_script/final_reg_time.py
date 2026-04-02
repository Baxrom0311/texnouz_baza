import os
import time

def audit_texnouz_registry():
    print("[*] Auditing HKCU\\Texnouz in detail...")
    reg_bin = "C:\\Windows\\System32\\reg.exe"
    key = "HKCU\\Texnouz"
    
    cmd = f"\"{reg_bin}\" query \"{key}\" /s"
    try:
        res = os.popen(cmd).read()
        print(f"[REGISTRY VALUES for {key}]:\n{res}")
    except: pass

def broad_time_match():
    # Reports updated at ~17:40 on April 1, 2026
    # Target: Apr 1 2026 17:35:00 to 17:45:00
    # Current system time is ~19:35, so we look back 2 hours.
    print("\n[*] Broad system-wide time matching (Safe Scan)...")
    
    # Target window (approximate timestamps for 17:35-17:45)
    # We'll use current time - delta to be robust.
    current_time = time.time()
    report_time_delta = current_time - (19*3600 + 35*60) + (17*3600 + 40*60) # Rough estimate
    # Actually let's just find ANYTHING modified in the last 4 hours on the whole disk, 
    # but filter for non-standard paths.
    
    found = []
    visited = set()
    for drive in ["C:\\"]:
        for root, dirs, files in os.walk(drive):
            try:
                real_root = os.path.realpath(root).lower()
                if real_root in visited:
                    dirs[:] = []
                    continue
                visited.add(real_root)
            except: continue
            
            # Skip massive system junk
            if any(x in real_root for x in ["\\windows", "\\program files", "\\appdata\\local\\google"]):
                dirs[:] = []
                continue
                
            for file in files:
                path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(path)
                    # Window: Modified today after 17:00
                    mt_struct = time.localtime(mtime)
                    if mt_struct.tm_year == 2026 and mt_struct.tm_mon == 4 and mt_struct.tm_mday == 1 and mt_struct.tm_hour >= 17:
                        size = os.path.getsize(path)
                        if size > 100*1024: # > 100KB
                            found.append((mtime, path, size))
                except: pass
    
    found.sort()
    for mt, p, sz in found:
        print(f"[BROAD MATCH]: {time.ctime(mt)} | {p} | {sz//1024} KB")

if __name__ == "__main__":
    audit_texnouz_registry()
    broad_time_match()
    print("\n[*] Final discovery scan complete.")
