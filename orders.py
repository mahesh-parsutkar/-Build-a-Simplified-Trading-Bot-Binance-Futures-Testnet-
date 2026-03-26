from __future__ import annotations

import logging
from typing import Any

from .client import BinanceFuturesClient
from .validators import ValidatedOrder


log = logging.getLogger("trading_bot.orders")


def place_order(client: BinanceFuturesClient, order: ValidatedOrder) -> Any:
    params: dict[str, Any] = {
        "symbol": order.symbol,
        "side": order.side,
        "type": order.order_type,
        "quantity": order.quantity,
    }

    if order.order_type == "LIMIT":
        params["price"] = order.price
        params["timeInForce"] = "GTC"

    log.info("placing_order symbol=%s side=%s type=%s quantity=%s price=%s", order.symbol, order.side, order.order_type, order.quantity, order.price)
    return client.place_order(params=params)
