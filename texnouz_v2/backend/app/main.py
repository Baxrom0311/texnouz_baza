"""Texnouz v2 — FastAPI asosiy ilova"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.database import init_db
from app.hardware.mariya.driver import get_trk_driver
from app.hardware.shtrih.driver import get_shtrih_driver
from app.api import auth, shifts, trk, dispense, fuel, partners, reports

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ishga tushirish
    log.info("Texnouz v2 ishga tushmoqda... AZS: %s", settings.AZS_NAME)

    # DB jadvallarni yaratish
    await init_db()
    log.info("DB jadvallar tayyor")

    # Seed data
    await seed_initial_data()

    # Hardware
    trk_driver = get_trk_driver()
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.fuel import TRK
    async with AsyncSessionLocal() as db:
        trk_rows = (await db.execute(select(TRK).order_by(TRK.PistoletID))).scalars().all()
        gun_ids = [r.PistoletID for r in trk_rows if r.PistoletID] or [1, 2, 3, 4]
    await trk_driver.start(gun_ids)
    log.info("TRK drayveri ishga tushdi (pistoletlar: %s)", gun_ids)

    printer = get_shtrih_driver()
    await printer.start()
    log.info("Shtrih printer tayyor")

    yield

    log.info("Texnouz v2 to'xtatilmoqda...")


app = FastAPI(
    title="Texnouz v2",
    version="2.0.0",
    description="AZS boshqaruv tizimi",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routerlar
app.include_router(auth.router)
app.include_router(shifts.router)
app.include_router(trk.router)
app.include_router(dispense.router)
app.include_router(fuel.router)
app.include_router(partners.router)
app.include_router(reports.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "azs": settings.AZS_NAME, "version": "2.0.0"}


# Frontend — statik fayllar
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


async def seed_initial_data():
    """Boshlang'ich ma'lumotlarni tekshirish va qo'shish"""
    from app.database import AsyncSessionLocal
    from app.models.operator import Operator, OperatorType
    from app.models.misc import Operation, Version
    from app.models.fuel import GasType, Storage, TRK
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # OperatorType
        if not (await db.execute(select(OperatorType).limit(1))).scalar_one_or_none():
            db.add_all([
                OperatorType(TypeID=1, TypeName="Admin"),
                OperatorType(TypeID=2, TypeName="Operator"),
                OperatorType(TypeID=3, TypeName="Kassir"),
            ])
            await db.flush()

        # Default operator: admin / 1111
        if not (await db.execute(select(Operator).limit(1))).scalar_one_or_none():
            from datetime import datetime
            db.add(Operator(
                OperatorID=1,
                AZSID=settings.AZS_ID,
                Name="Admin",
                Password="1111",
                Type=1,
                Date=datetime.now(),
            ))
            await db.flush()
            log.info("Default operator yaratildi: parol=1111")

        # Operation turlari
        if not (await db.execute(select(Operation).limit(1))).scalar_one_or_none():
            db.add_all([
                Operation(OperationID=1, Name="Gaz sotish (naqd)"),
                Operation(OperationID=2, Name="Gaz sotish (bank)"),
                Operation(OperationID=3, Name="Gaz sotish (talon)"),
                Operation(OperationID=4, Name="Gaz sotish (hamkor)"),
                Operation(OperationID=5, Name="Gaz sotish (karta)"),
                Operation(OperationID=6, Name="Tovar sotish (naqd)"),
                Operation(OperationID=7, Name="Tovar sotish (bank)"),
                Operation(OperationID=8, Name="Hamkor to'lov"),
            ])
            await db.flush()

        # Default gaz turi
        if not (await db.execute(select(GasType).limit(1))).scalar_one_or_none():
            from decimal import Decimal
            from datetime import datetime
            db.add_all([
                GasType(GasID=1, GasName="Benzin A-80",  CheckName="A-80",  Price=Decimal("8500"), GasMetan=0),
                GasType(GasID=2, GasName="Benzin A-92",  CheckName="A-92",  Price=Decimal("9000"), GasMetan=0),
                GasType(GasID=3, GasName="Dizel",        CheckName="Dizel", Price=Decimal("8000"), GasMetan=0),
                GasType(GasID=10, GasName="Metan (CNG)", CheckName="Metan", Price=Decimal("3500"), GasMetan=1),
            ])
            await db.flush()

        # Default sisternalar
        if not (await db.execute(select(Storage).limit(1))).scalar_one_or_none():
            db.add_all([
                Storage(CisternID=1, GasID=1, Volume=500000),   # 5000 litr
                Storage(CisternID=2, GasID=2, Volume=500000),
                Storage(CisternID=3, GasID=3, Volume=500000),
            ])
            await db.flush()

        # Default TRK
        if not (await db.execute(select(TRK).limit(1))).scalar_one_or_none():
            db.add_all([
                TRK(TRKID=1, CisternID=1, PistoletID=1, MPort=1, MBaud=9600),
                TRK(TRKID=1, CisternID=1, PistoletID=2, MPort=1, MBaud=9600),
                TRK(TRKID=2, CisternID=2, PistoletID=3, MPort=1, MBaud=9600),
                TRK(TRKID=2, CisternID=2, PistoletID=4, MPort=1, MBaud=9600),
            ])
            await db.flush()

        # Version
        if not (await db.execute(select(Version).limit(1))).scalar_one_or_none():
            db.add(Version(AZSID=settings.AZS_ID, VersionMajor=2, VersionMinor=0, VersionRelease=0))
            await db.flush()

        await db.commit()
