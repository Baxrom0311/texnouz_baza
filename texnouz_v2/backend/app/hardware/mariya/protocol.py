"""
Mariya protokoli — CIS davlatlarida ishlatiluvchi TRK (yoqilg'i kolonkasi) protokoli.
Frame tuzilishi: STX | ADDR | CMD | LEN | DATA... | CHECKSUM | ETX
"""
import struct
from dataclasses import dataclass

STX = 0x02
ETX = 0x03


@dataclass
class MFrame:
    address: int      # TRK manzili (1-based)
    command: int      # Buyruq kodi
    data: bytes = b""


def build_frame(frame: MFrame) -> bytes:
    body = bytes([frame.address, frame.command, len(frame.data)]) + frame.data
    checksum = _xor_checksum(body)
    return bytes([STX]) + body + bytes([checksum, ETX])


def parse_response(raw: bytes) -> MFrame | None:
    """Javob frameni parse qilish. None = noto'g'ri frame"""
    if len(raw) < 5:
        return None
    if raw[0] != STX or raw[-1] != ETX:
        return None

    body = raw[1:-2]
    checksum = raw[-2]

    if _xor_checksum(body) != checksum:
        return None

    if len(body) < 3:
        return None

    address = body[0]
    command = body[1]
    data_len = body[2]
    data = body[3:3 + data_len]

    return MFrame(address=address, command=command, data=data)


def _xor_checksum(data: bytes) -> int:
    result = 0
    for b in data:
        result ^= b
    return result


def decode_counter(data: bytes) -> int:
    """4 baytli little-endian schetchik"""
    if len(data) >= 4:
        return struct.unpack_from("<I", data, 0)[0]
    return 0


def decode_liters(data: bytes) -> float:
    """4 baytli litr qiymati (integer, /100 = float litr)"""
    if len(data) >= 4:
        raw = struct.unpack_from("<I", data, 0)[0]
        return raw / 100.0
    return 0.0


def encode_preset_liters(liters: float) -> bytes:
    """Litr preset uchun 4 bayt (liters * 100, little-endian)"""
    val = int(liters * 100)
    return struct.pack("<I", val)


def encode_preset_money(money: float) -> bytes:
    """Pul preset uchun 4 bayt (tiyin, little-endian)"""
    val = int(money * 100)
    return struct.pack("<I", val)
