import os
from access_parser import AccessParser

def scan_drives():
    drives = []
    # D: diskini birinchi tekshiramiz, chunki ma'lumotlar ko'pincha o'sha yerda bo'ladi
    for letter in ['D', 'E', 'F', 'C']:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    
    print(f"Skanerlash boshlandi: {drives}")
    
    for drive in drives:
        print(f"Tekshirilmoqda: {drive}")
        # os.walk dagi cheksiz sikllarni oldini olish uchun oddiyroq usul
        try:
            for root, dirs, files in os.walk(drive, topdown=True):
                # Tizim papkalarini va cheksiz "Application Data" sikllarini o'tkazib yuboramiz
                low_root = root.lower()
                if any(x in low_root for x in ['windows', 'appdata', 'temp', 'documents and settings']):
                    # Bu papka ichiga kirmaymiz
                    dirs[:] = [] 
                    continue
                
                # Papka juda chuqur bo'lib ketsa (sikllar bo'lishi mumkin)
                if root.count(os.sep) > 7:
                    dirs[:] = []
                    continue

                for file in files:
                    if file.lower().endswith('.mdb'):
                        path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(path)
                            if size < 800000: # 800KB dan kichiklarini tashlab ketamiz
                                continue
                                
                            print(f"... Tekshirilmoqda: {path} ({size // 1024} KB)")
                            db = AccessParser(path)
                            if 'tabmaindata' in [t.lower() for t in db.catalog.keys()]:
                                print("\n" + "="*40)
                                print("!!! MANA TOPILDI !!!")
                                print(f"YO'L: {path}")
                                print(f"O'LCHAMI: {size:,} bayt")
                                print("="*40 + "\n")
                                return # Topilgach to'xtatamiz
                        except:
                            pass
        except Exception as e:
            print(f"Xato {drive} da: {e}")

if __name__ == "__main__":
    scan_drives()
    print("Qidiruv yakunlandi.")
