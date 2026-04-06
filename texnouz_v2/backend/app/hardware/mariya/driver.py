"""
Mariya TRK drayveri — real COM port yoki simulyator orqali ishlaydi.
SIMULATE_HARDWARE=true bo'lsa simulator ishlatiladi.
"""
import asyncio
import logging
from dataclasses import dataclass

from app.config import settings
from app.hardware.mariya.commands import (
    CMD_GET_STATUS, CMD_ARM, CMD_START, CMD_STOP,
    CMD_GET_LITERS, CMD_GET_COUNTER, CMD_SET_PRESET_L, CMD_SET_PRESET_M, CMD_SET_PRESET_FULL,
    STATUS_IDLE, STATUS_ARMED, STATUS_DISPENSING, STATUS_COMPLETE, STATUS_ERROR,
)
from app.hardware.mariya.protocol import (
    MFrame, build_frame, parse_response, encode_preset_liters, encode_preset_money,
    decode_liters, decode_counter,
)

log = logging.getLogger(__name__)


@dataclass
class GunStatus:
    pist_id: int
    status: int
    status_name: str
    liters: float
    counter: int


class TRKDriver:
    def __init__(self):
        self._sim = None
        self._serial = None
        self._lock = asyncio.Lock()

    async def start(self, gun_ids: list[int]):
        if settings.SIMULATE_HARDWARE:
            from app.hardware.mariya.simulator import get_simulator
            self._sim = get_simulator(gun_ids)
            log.info("TRK: simulyator rejimi, pistoletlar: %s", gun_ids)
        else:
            await self._open_serial()

    async def _open_serial(self):
        try:
            import serial_asyncio
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=settings.TRK_PORT,
                baudrate=settings.TRK_BAUD,
            )
            log.info("TRK: %s portiga ulandi (%d baud)", settings.TRK_PORT, settings.TRK_BAUD)
        except Exception as e:
            log.error("TRK port ochmadi: %s", e)

    async def get_all_statuses(self) -> list[GunStatus]:
        if self._sim:
            return [
                GunStatus(
                    pist_id=s["pist_id"],
                    status=s["status"],
                    status_name=_status_name(s["status"]),
                    liters=s["liters"],
                    counter=s["counter"],
                )
                for s in self._sim.get_all_statuses()
            ]
        return []

    async def arm(self, pist_id: int, preset_liters: float | None = None, preset_money: float | None = None) -> bool:
        if self._sim:
            ok = self._sim.arm(pist_id, preset_liters, preset_money)
            if ok:
                self._sim.start_dispense(pist_id)
            return ok

        # Real hardware
        async with self._lock:
            if preset_liters is not None:
                cmd = CMD_SET_PRESET_L
                data = encode_preset_liters(preset_liters)
            elif preset_money is not None:
                cmd = CMD_SET_PRESET_M
                data = encode_preset_money(preset_money)
            else:
                cmd = CMD_SET_PRESET_FULL
                data = b""
            await self._send(MFrame(pist_id, cmd, data))
            await asyncio.sleep(0.1)
            await self._send(MFrame(pist_id, CMD_ARM))
        return True

    async def stop(self, pist_id: int) -> float:
        if self._sim:
            return self._sim.stop(pist_id)
        async with self._lock:
            await self._send(MFrame(pist_id, CMD_STOP))
        return 0.0

    async def acknowledge(self, pist_id: int) -> float:
        """STATUS_COMPLETE keyin yakuniy litr va IDLE ga qaytish"""
        if self._sim:
            return self._sim.acknowledge(pist_id)
        # Real: counter o'qish
        async with self._lock:
            resp = await self._send_recv(MFrame(pist_id, CMD_GET_LITERS))
            if resp:
                return decode_liters(resp.data)
        return 0.0

    async def get_counter(self, pist_id: int) -> int:
        if self._sim:
            return self._sim.get_status(pist_id).get("counter", 0)
        async with self._lock:
            resp = await self._send_recv(MFrame(pist_id, CMD_GET_COUNTER))
            if resp:
                return decode_counter(resp.data)
        return 0

    async def _send(self, frame: MFrame):
        if self._writer:
            self._writer.write(build_frame(frame))
            await self._writer.drain()

    async def _send_recv(self, frame: MFrame, timeout: float = 0.5) -> MFrame | None:
        if not self._writer or not self._reader:
            return None
        self._writer.write(build_frame(frame))
        await self._writer.drain()
        try:
            raw = await asyncio.wait_for(self._reader.read(256), timeout=timeout)
            return parse_response(raw)
        except asyncio.TimeoutError:
            return None


def _status_name(status: int) -> str:
    names = {
        STATUS_IDLE: "idle",
        STATUS_ARMED: "armed",
        STATUS_DISPENSING: "dispensing",
        STATUS_COMPLETE: "complete",
        STATUS_ERROR: "error",
    }
    return names.get(status, "unknown")


# Global singleton
_driver: TRKDriver | None = None


def get_trk_driver() -> TRKDriver:
    global _driver
    if _driver is None:
        _driver = TRKDriver()
    return _driver
