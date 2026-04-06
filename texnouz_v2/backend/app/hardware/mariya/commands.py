"""Mariya protokoli buyruq kodlari"""

# Asosiy buyruqlar
CMD_GET_STATUS      = 0x01   # TRK holatini so'rash
CMD_ARM             = 0x10   # Gaz berishni boshlash uchun qurollantirish
CMD_START           = 0x11   # Qurollangandan keyin ishga tushirish
CMD_STOP            = 0x12   # To'xtatish
CMD_GET_LITERS      = 0x20   # Hozirgi dispense litrlari
CMD_GET_COUNTER     = 0x21   # Kumulyativ schetchik
CMD_SET_PRESET_L    = 0x30   # Litr preset o'rnatish
CMD_SET_PRESET_M    = 0x31   # Pul preset o'rnatish
CMD_SET_PRESET_FULL = 0x32   # To'liq tank (preset yo'q)
CMD_ACK             = 0x06   # Tasdiqlash

# TRK holat kodlari (GetStatus javobi)
STATUS_IDLE         = 0x00   # Bo'sh, kutish
STATUS_ARMED        = 0x01   # Qurollangan, kutish
STATUS_DISPENSING   = 0x02   # Gaz quyilmoqda
STATUS_COMPLETE     = 0x03   # Tugadi, qaytim kutilmoqda
STATUS_ERROR        = 0x04   # Xato
STATUS_BUSY         = 0x05   # Band (boshqa jarayon)

STATUS_NAMES = {
    STATUS_IDLE:       "bo'sh",
    STATUS_ARMED:      "qurollangan",
    STATUS_DISPENSING: "quyilmoqda",
    STATUS_COMPLETE:   "tugadi",
    STATUS_ERROR:      "xato",
    STATUS_BUSY:       "band",
}
