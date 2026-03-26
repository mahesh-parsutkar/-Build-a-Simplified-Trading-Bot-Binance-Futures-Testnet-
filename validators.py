from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal


Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]


@dataclass(frozen=True)
class ValidatedOrder:
    symbol: str
    side: Side
    order_type: OrderType
    quantity: str  # send as string to preserve precision
    price: str | None = None


_SYMBOL_RE = re.compile(r"^[A-Z0-9]{3,20}$")


def _as_decimal_str(value: str, *, field: str) -> str:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"{field} must be a valid number") from e
    if d <= 0:
        raise ValueError(f"{field} must be > 0")
    # Normalize without scientific notation
    return format(d.normalize(), "f")


def validate_order(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None,
) -> ValidatedOrder:
    sym = (symbol or "").strip().upper()
    if not _SYMBOL_RE.match(sym):
        raise ValueError("symbol must be like BTCUSDT (A-Z/0-9, 3-20 chars)")

    s = (side or "").strip().upper()
    if s not in ("BUY", "SELL"):
        raise ValueError("side must be BUY or SELL")

    t = (order_type or "").strip().upper()
    if t not in ("MARKET", "LIMIT"):
        raise ValueError("order type must be MARKET or LIMIT")

    qty_str = _as_decimal_str(quantity, field="quantity")

    if t == "LIMIT":
        if price is None:
            raise ValueError("price is required for LIMIT orders")
        price_str = _as_decimal_str(price, field="price")
    else:
        if price is not None:
            raise ValueError("price is only allowed for LIMIT orders")
        price_str = None

    return ValidatedOrder(
        symbol=sym,
        side=s, 
        order_type=t,  
        quantity=qty_str,
        price=price_str,
    )
