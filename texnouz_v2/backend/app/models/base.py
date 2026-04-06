from app.database import Base

# Barcha modellarni import qilish — metadata.create_all uchun
from app.models.operator import OperatorType, Operator  # noqa
from app.models.shift import Change  # noqa
from app.models.fuel import GasType, Storage, TRK, LevelMeter  # noqa
from app.models.transaction import MainData, MainDataHistory  # noqa
from app.models.counters import SummCounter  # noqa
from app.models.partner import Partner, PartnerAccount, PartnerInHistory, PartnerOutHistory  # noqa
from app.models.card import CardType, CardNumber  # noqa
from app.models.goods import Goods, GoodsHistory, GoodsPriceHistory  # noqa
from app.models.car import CarPassport  # noqa
from app.models.history import GasHistory, PriceHistory  # noqa
from app.models.misc import Operation, Error, Tax, TaxType, Schema, Version  # noqa
