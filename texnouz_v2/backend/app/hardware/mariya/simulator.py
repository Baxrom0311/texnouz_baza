"""
Mariya TRK simulyatori — real hardware bo'lmagan holda test qilish uchun.
SIMULATE_HARDWARE=true bo'lsa ishlatiladi.
"""
import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime

from app.hardware.mariya.commands import (
    STATUS_IDLE, STATUS_ARMED, STATUS_DISPENSING, STATUS_COMPLETE, STATUS_ERROR
)


@dataclass
class SimGun:
    pist_id: int
    status: int = STATUS_IDLE
    liters: float = 0.0
    counter: int = 0
    preset_liters: float | None = None
    preset_money: float | None = None
    _task: asyncio.Task | None = field(default=None, repr=False)


class MarijaSimulator:
    """
    Har bir pistolet uchun holat mashinasi.
    arm() → STATUS_ARMED → dispense() → STATUS_DISPENSING (sekin litr o'sadi)
    → preset yetganda STATUS_COMPLETE
    """

    def __init__(self, gun_ids: list[int]):
        self.guns: dict[int, SimGun] = {pid: SimGun(pist_id=pid) for pid in gun_ids}

    def get_status(self, pist_id: int) -> dict:
        g = self.guns.get(pist_id)
        if not g:
            return {"status": STATUS_ERROR, "liters": 0.0, "counter": 0}
        return {"status": g.status, "liters": g.liters, "counter": g.counter}

    def get_all_statuses(self) -> list[dict]:
        return [
            {"pist_id": g.pist_id, **self.get_status(g.pist_id)}
            for g in self.guns.values()
        ]

    def arm(self, pist_id: int, preset_liters: float | None = None, preset_money: float | None = None) -> bool:
        g = self.guns.get(pist_id)
        if not g or g.status != STATUS_IDLE:
            return False
        g.status = STATUS_ARMED
        g.liters = 0.0
        g.preset_liters = preset_liters
        g.preset_money = preset_money
        return True

    def start_dispense(self, pist_id: int) -> bool:
        g = self.guns.get(pist_id)
        if not g or g.status != STATUS_ARMED:
            return False
        g.status = STATUS_DISPENSING
        # simulyatsiya: arqon ushlab dispense boshlanadi
        asyncio.create_task(self._sim_dispense(g))
        return True

    async def _sim_dispense(self, gun: SimGun):
        """Sekin-sekin litr oshirish simulyatsiyasi"""
        target = gun.preset_liters or 20.0   # default 20 litr
        rate = random.uniform(0.8, 1.2)      # litr/sekund

        while gun.liters < target and gun.status == STATUS_DISPENSING:
            gun.liters = min(gun.liters + rate * 0.5, target)
            gun.counter += int(rate * 0.5 * 100)
            await asyncio.sleep(0.5)

        if gun.status == STATUS_DISPENSING:
            gun.status = STATUS_COMPLETE

    def stop(self, pist_id: int) -> float:
        """To'xtatish — hozirgi litr qaytariladi"""
        g = self.guns.get(pist_id)
        if not g:
            return 0.0
        liters = g.liters
        g.status = STATUS_IDLE
        if g._task:
            g._task.cancel()
        return liters

    def acknowledge(self, pist_id: int) -> float:
        """STATUS_COMPLETE dan keyin yakuniy litrni olish va IDLE ga qaytish"""
        g = self.guns.get(pist_id)
        if not g or g.status != STATUS_COMPLETE:
            return 0.0
        liters = g.liters
        g.status = STATUS_IDLE
        g.liters = 0.0
        return liters


# Global instance (main.py dan import qilinadi)
_simulator: MarijaSimulator | None = None


def get_simulator(gun_ids: list[int] | None = None) -> MarijaSimulator:
    global _simulator
    if _simulator is None:
        _simulator = MarijaSimulator(gun_ids or [1, 2, 3, 4])
    return _simulator
