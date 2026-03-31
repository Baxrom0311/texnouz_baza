# TexnoUz v1 (MS Access) dan PostgreSQL ga Sinxronizatsiya Qilish Yo'riqnomasi

Ushbu yo'riqnoma `texnouz_v1` (eski dastur) ishlayotgan Windows kompyuterida tranzaksiyalarni markaziy serverga (PostgreSQL) yuborishni o'rnatish uchun mo'ljallangan.

## 1. Dastlabki tayyorgarlik

1. **Python O'rnatish:** 
   Windows kompyuterda [Python 3.10+](https://www.python.org/downloads/windows/) o'rnatilgan bo'lishi shart. O'rnatish jarayonida **"Add Python to PATH"** tugmachasiga pitichka (✅) qo'yishni unutmang.
2. **Fayllarni ko'chirish:**
   Biz tayyorlagan `texnouz_v1` papkasini (ichida `app` va `sync_script` bor) kompyuterga (masalan, `C:\TexnoUz_V1`) ko'chirib o'tkazing.
3. **Kutubxonalarni o'rnatish:**
   Loyihani ishga tushirish uchun CMD (Buyruqlar qatori) ni ochib quyidagilarni yozing:
   ```cmd
   pip install pyodbc psycopg2
   ```

## 2. Serverni tayyorlash (PostgreSQL)

Markaziy serverdagi ma'lumotlar bazasida v1 uchun yangi jadval yaratilishi kerak:
- `sync_script` papkasidagi **`create_operation_operation_texnouz_v1.sql`** faylidagi barcha kodni serveringiz (mms_localhost) dagi SQL ishga tushirgich orqali bajaring. Bu v1 uchun xavfsiz jadval yaratadi.

## 3. Skriptni Test Qilish

Ulanish tog'riligini va ma'lumotlar keta boshlaganini tekshirish uchun:
1. CMD ni ochib, `sync_script` joylashgan papkaga kiring:
   ```cmd
   cd C:\TexnoUz_V1\sync_script
   ```
2. So'ng bevosita bitta sinov (once) yurgizib ko'ring:
   ```cmd
   python sync_v1.py --once
   ```
*(Hech qanday qizil xato yozuv chiqmasa va "Sync done. Total=X" deb chiqsa ulanish mantiqan mos kelganini bildiradi).*

## 4. Orqa fonda (NSSM orqali) avtomatlashtirish

Skript kompyuter yonganda avto-ishga tushishi va orqa fonda (ko'rinmas) ishlashi uchun NSSM ishlatamiz:

1. NSSM fayl joylashgan papkadan CMD ni **Administrator** sifatida oching.
2. NSSM oynasini chaqiring:
   ```cmd
   nssm install MMSBridgeV1
   ```
3. Oynada quyidagilarni to'ldiring:
   - **Path:** `C:\Ozingizdagi\Python\Yoli\python.exe`
   - **Arguments:** `C:\TexnoUz_V1\sync_script\sync_v1.py`
   - **Details bo'limi (Display name):** `TexnoUz V1 Sync Bridge`
4. **"Install service"** ni bosing.
5. So'ngra xizmatni ishga tushiring:
   ```cmd
   nssm start MMSBridgeV1
   ```

Tabriklaymiz! Endi dastur o'zi avtomatik ravishda so'nggi ma'lumotlarni markaziy bazaga tashlab turadi.
