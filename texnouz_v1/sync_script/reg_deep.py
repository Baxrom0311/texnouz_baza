import os

def deep_registry_odbc():
    print("[*] Querying System DSNs and WOW6432Node...")
    reg_bin = "C:\\Windows\\System32\\reg.exe"
    
    keys = [
        "HKLM\\Software\\ODBC\\ODBC.INI",
        "HKLM\\Software\\WOW6432Node\\ODBC\\ODBC.INI",
        "HKCU\\Software\\ODBC\\ODBC.INI"
    ]
    
    for k in keys:
        print(f"\n--- Checking {k} ---")
        cmd = f"\"{reg_bin}\" query \"{k}\" /s"
        try:
            res = os.popen(cmd).read()
            # Filter for DBQ (Access file path) or Server (SQL Server)
            for line in res.splitlines():
                if "DBQ" in line or "Server" in line or "Database" in line:
                    print(line.strip())
        except: pass

def find_hidden_appdata():
    print("\n[*] Searching ProgramData and Public for 'Texno' related folders...")
    targets = ["C:\\ProgramData", "C:\\Users\\Public", "C:\\Users\\ids\\AppData\\Roaming"]
    for t in targets:
        if not os.path.exists(t): continue
        print(f"Checking: {t}")
        try:
            for item in os.listdir(t):
                if "texno" in item.lower():
                    print(f"[FOUND FOLDER]: {os.path.join(t, item)}")
        except: pass

if __name__ == "__main__":
    deep_registry_odbc()
    find_hidden_appdata()
    print("\n[*] Deep registry and folder discovery complete.")
