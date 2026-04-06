"""To'lov hisoblash va chegirma logikasi"""
from decimal import Decimal, ROUND_HALF_UP


def apply_discount(price: Decimal, discount1: int, discount2: int) -> Decimal:
    """
    Chegirmani narxga qo'llash.
    discount1, discount2 — foiz * 100 (masalan: 500 = 5.00%)
    """
    d1 = Decimal(str(discount1)) / Decimal("10000")  # /100 foiz, /100 foiz unit
    d2 = Decimal(str(discount2)) / Decimal("10000")
    total_discount = d1 + d2
    effective = price * (Decimal("1") - total_discount)
    return effective.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calc_liters_from_money(money: Decimal, price: Decimal, discount1: int = 0, discount2: int = 0) -> float:
    """Pul miqdori bo'yicha necha litr quyiladi"""
    effective_price = apply_discount(price, discount1, discount2)
    if effective_price <= 0:
        return 0.0
    return float((money / effective_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calc_money_from_liters(liters: float, price: Decimal, discount1: int = 0, discount2: int = 0) -> Decimal:
    """Litr miqdori bo'yicha qancha pul to'lanadi"""
    effective_price = apply_discount(price, discount1, discount2)
    total = Decimal(str(liters)) * effective_price
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def split_payment(
    total: Decimal,
    cash: float = 0,
    bank: float = 0,
    talon: float = 0,
    credit: float = 0,
) -> dict:
    """
    To'lov bo'linishini tekshirish va qaytarish.
    Qaytim = kiritilgan pul - umumiy narx
    """
    paid = Decimal(str(cash)) + Decimal(str(bank)) + Decimal(str(talon)) + Decimal(str(credit))
    change_back = paid - total
    return {
        "total": float(total),
        "paid": float(paid),
        "change_back": float(max(change_back, Decimal("0"))),
        "money_cash": cash,
        "money_bank": bank,
        "money_talon": talon,
        "money_fut": credit,
    }
