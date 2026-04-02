import os

def check_recent_mru():
    print("[*] Checking Registry MRU and Recent Items...")
    reg_bin = "C:\\Windows\\System32\\reg.exe"
    
    # 1. Access MRU
    # Try different Office versions
    for v in ["16.0", "15.0", "14.0", "12.0"]:
        path = f"Software\\Microsoft\\Office\\{v}\\Access\\File MRU"
        print(f"[*] Querying Access {v} MRU...")
        cmd = f"\"{reg_bin}\" query \"HKCU\\{path}\" /s"
        try:
            res = os.popen(cmd).read()
            if "Item" in res or ".mdb" in res.lower() or ".accdb" in res.lower():
                print(f"[FOUND MRU]:\n{res}")
        except: pass

    # 2. Windows MRU (ComDlg32)
    path = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\LastVisitedPidlMRU"
    print("[*] Checking LastVisitedPidlMRU...")
    cmd = f"\"{reg_bin}\" query \"HKCU\\{path}\" /s"
    try:
        res = os.popen(cmd).read()
        print(f"[FOUND LAST VISITED]:\n{res}")
    except: pass

    # 3. Recent Items Folder
    recent_path = os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Recent")
    print(f"[*] Checking Recent Items: {recent_path}")
    if os.path.exists(recent_path):
        try:
            items = os.listdir(recent_path)
            for item in items:
                if "texno" in item.lower() or ".mdb" in item.lower() or ".accdb" in item.lower():
                    print(f"[FOUND RECENT ITEM]: {item}")
        except: pass

if __name__ == "__main__":
    check_recent_mru()
    print("[*] Scan complete.")
