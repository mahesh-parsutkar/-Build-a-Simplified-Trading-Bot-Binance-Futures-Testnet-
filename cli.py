from __future__ import annotations

import argparse
import json
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.validators import validate_order
from bot.orders import place_order


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simplified Binance Futures Testnet order placer (USDT-M).")
    p.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    p.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    p.add_argument("--type", required=True, choices=["MARKET", "LIMIT"], dest="order_type", help="Order type")
    p.add_argument("--quantity", required=True, help="Order quantity (positive number)")
    p.add_argument("--price", help="Limit price (required for LIMIT)")
    p.add_argument("--log-level", default="INFO", help="Logging level (INFO, DEBUG, ...)")
    p.add_argument("--log-dir", default="logs", help="Directory for log files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    log_file = setup_logging(log_dir=args.log_dir, log_level=args.log_level)

    try:
        order = validate_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValueError as e:
        print(f"Invalid input: {e}", file=sys.stderr)
        return 2

    print("Order request summary")
    print(json.dumps(order.__dict__, indent=2))

    try:
        client = BinanceFuturesClient.from_env()
        resp = place_order(client, order)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.", file=sys.stderr)
        return 2
    except BinanceAPIError as e:
        print("Order failed")
        print(f"- status_code: {e.status_code}")
        print(f"- message: {str(e)}")
        if e.payload is not None:
            print("- payload:")
            print(json.dumps(e.payload, indent=2))
        print(f"See log file: {log_file}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        print(f"See log file: {log_file}", file=sys.stderr)
        return 1

    # Print key response fields (Binance returns slightly different keys sometimes)
    order_id = resp.get("orderId") if isinstance(resp, dict) else None
    status = resp.get("status") if isinstance(resp, dict) else None
    executed_qty = resp.get("executedQty") if isinstance(resp, dict) else None
    avg_price = resp.get("avgPrice") if isinstance(resp, dict) else resp.get("avgFillPrice") if isinstance(resp, dict) else None

    print("Order response details")
    print(json.dumps(resp, indent=2))
    print("Result")
    print(f"- success: true")
    print(f"- orderId: {order_id}")
    print(f"- status: {status}")
    print(f"- executedQty: {executed_qty}")
    print(f"- avgPrice: {avg_price}")
    print(f"Log file: {log_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
