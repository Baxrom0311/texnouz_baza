import os

def find_string_systemwide():
    print("[*] Performing deep string search for 'tabMainData'...")
    # Using findstr via absolute path to bypass PATH issues
    findstr_bin = "C:\\Windows\\System32\\findstr.exe"
    
    # We'll search in C:\TEXNO UZ 1 and C:\sync_texnouz just in case
    target_dir = "C:\\TEXNO UZ 1"
    
    # /s = recursive, /m = only filename, /i = case insensitive, /c: = literal string
    cmd = f"\"{findstr_bin}\" /s /m /i /c:\"tabMainData\" \"{target_dir}\\*.*\""
    print(f"[*] Executing: {cmd}")
    
    try:
        res = os.popen(cmd).read()
        print(f"[SEARCH RESULTS]:\n{res}")
    except Exception as e:
        print(f"[!] Error: {e}")

def check_html_content():
    html_report = "C:\\TEXNO UZ 1\\Reports\\1005StorageAllToday.htm"
    if os.path.exists(html_report):
        print(f"\n[*] Peeking at recent report: {html_report}")
        try:
            with open(html_report, "r", encoding='utf-8', errors='ignore') as f:
                content = f.read(2048) # Read first 2KB
                print(content)
        except: pass

if __name__ == "__main__":
    find_string_systemwide()
    check_html_content()
    print("\n[*] Search complete.")
