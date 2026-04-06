"""
Shtrih printer drayveri — chek chiqarish.
Real hardware yoki simulyator (SIMULATE_HARDWARE=true).
"""
import asyncio
import logging
import struct
from dataclasses import dataclass

from app.config import settings

log = logging.getLogger(__name__)

# Shtrih buyruqlari
CMD_OPEN_CHECK    = 0x8D
CMD_SALE          = 0x80
CMD_CLOSE_CHECK   = 0x85
CMD_CANCEL_CHECK  = 0x88
CMD_GET_STATUS    = 0x3B
CMD_CUT           = 0x25
CMD_PRINT_TEXT    = 0x17

# To'lov turlari
PAY_CASH = 1
PAY_CARD = 2
PAY_TALON = 3

PRINTER_PASSWORD = b"\x1E\x00\x00\x00"  # default 30


@dataclass
class PrintLine:
    name: str
    quantity: float
    price: float
    total: float
    tax_code: int = 0
    unit: str = "l"


class ShtrihDriver:
    def __init__(self):
        self._sim = settings.SIMULATE_HARDWARE
        self._serial = None
        self._lock = asyncio.Lock()

    async def start(self):
        if self._sim:
            log.info("Shtrih: simulyator rejimi")
            return
        try:
            import serial_asyncio
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=settings.PRINTER_PORT,
                baudrate=settings.PRINTER_BAUD,
            )
            log.info("Shtrih: %s portiga ulandi", settings.PRINTER_PORT)
        except Exception as e:
            log.error("Shtrih port ochmadi: %s", e)

    async def print_fuel_receipt(
        self,
        *,
        receipt_num: int,
        operator_name: str,
        gas_name: str,
        liters: float,
        price: float,
        total: float,
        payment_type: int = PAY_CASH,
        header: str | None = None,
    ) -> bool:
        if self._sim:
            log.info(
                "[CHEK SIMULYATOR] #%d | %s: %.2fL x %.2f = %.2f",
                receipt_num, gas_name, liters, price, total,
            )
            return True

        async with self._lock:
            try:
                await self._open_check(operator_name)
                await self._add_line(PrintLine(
                    name=gas_name,
                    quantity=liters,
                    price=price,
                    total=total,
                ))
                await self._close_check(payment_type, total)
                return True
            except Exception as e:
                log.error("Chek chiqarishda xato: %s", e)
                await self._cancel_check()
                return False

    async def print_goods_receipt(
        self,
        *,
        receipt_num: int,
        operator_name: str,
        items: list[dict],
        total: float,
        payment_type: int = PAY_CASH,
    ) -> bool:
        if self._sim:
            log.info("[CHEK SIMULYATOR] Tovar #%d: %d ta mahsulot, jami=%.2f", receipt_num, len(items), total)
            return True

        async with self._lock:
            try:
                await self._open_check(operator_name)
                for item in items:
                    await self._add_line(PrintLine(
                        name=item["name"],
                        quantity=item["count"],
                        price=item["price"],
                        total=item["total"],
                        unit="шт",
                    ))
                await self._close_check(payment_type, total)
                return True
            except Exception as e:
                log.error("Tovar chek xatosi: %s", e)
                await self._cancel_check()
                return False

    async def _open_check(self, operator: str = ""):
        frame = PRINTER_PASSWORD + bytes([0x01])  # operator 1
        await self._cmd(CMD_OPEN_CHECK, frame)

    async def _add_line(self, line: PrintLine):
        # name (40 chars), qty (5 digits * 1000), price (5 digits * 100), total, tax
        name_bytes = line.name.encode("cp1251", errors="replace")[:40].ljust(40)
        qty = int(line.quantity * 1000)
        prc = int(line.price * 100)
        total = int(line.total * 100)
        data = (
            PRINTER_PASSWORD
            + name_bytes
            + struct.pack("<I", qty)
            + struct.pack("<I", prc)
            + struct.pack("<I", total)
            + bytes([line.tax_code, 0])
        )
        await self._cmd(CMD_SALE, data)

    async def _close_check(self, payment_type: int, total: float):
        total_int = int(total * 100)
        data = PRINTER_PASSWORD + bytes([payment_type]) + struct.pack("<I", total_int)
        await self._cmd(CMD_CLOSE_CHECK, data)

    async def _cancel_check(self):
        await self._cmd(CMD_CANCEL_CHECK, PRINTER_PASSWORD)

    async def _cmd(self, cmd: int, data: bytes = b""):
        if not self._writer:
            return
        frame = bytes([0x02, cmd]) + data + bytes([0x03])
        self._writer.write(frame)
        await self._writer.drain()
        await asyncio.sleep(0.05)


_driver: ShtrihDriver | None = None


def get_shtrih_driver() -> ShtrihDriver:
    global _driver
    if _driver is None:
        _driver = ShtrihDriver()
    return _driver
