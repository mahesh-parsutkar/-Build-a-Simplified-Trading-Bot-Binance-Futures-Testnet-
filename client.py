from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests


log = logging.getLogger("trading_bot.binance")


class BinanceAPIError(RuntimeError):
    def __init__(self, *, status_code: int | None, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(frozen=True)
class BinanceFuturesClientConfig:
    base_url: str = "https://testnet.binancefuture.com"
    recv_window: int = 5000
    timeout_s: int = 15


class BinanceFuturesClient:
    """
    Minimal signed REST client for Binance Futures (USDT-M).
    """

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        config: BinanceFuturesClientConfig | None = None,
        session: requests.Session | None = None,
    ):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret are required")
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or BinanceFuturesClientConfig()
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls) -> "BinanceFuturesClient":
        api_key = os.getenv("BINANCE_API_KEY", "").strip()
        api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        return cls(api_key=api_key, api_secret=api_secret)

    def _sign(self, query_string: str) -> str:
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _headers(self) -> dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    def _request(
        self,
        method: str,
        path: str,
        *,
        signed: bool = False,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = self.config.base_url.rstrip("/") + path
        params = dict(params or {})

        if signed:
            params.setdefault("recvWindow", self.config.recv_window)
            params["timestamp"] = int(time.time() * 1000)
            qs = urlencode(params, doseq=True)
            params["signature"] = self._sign(qs)

        # Log request (without secrets)
        safe_params = {k: ("***" if k == "signature" else v) for k, v in params.items()}
        start = time.time()
        log.info("request method=%s path=%s params=%s signed=%s", method.upper(), path, safe_params, signed)

        try:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=self._headers(),
                timeout=self.config.timeout_s,
            )
        except requests.RequestException as e:
            log.exception("network_error method=%s path=%s", method.upper(), path)
            raise BinanceAPIError(status_code=None, message=f"Network error: {e}") from e
        finally:
            elapsed_ms = int((time.time() - start) * 1000)

        content_type = (resp.headers.get("Content-Type") or "").lower()
        data: Any
        if "application/json" in content_type:
            try:
                data = resp.json()
            except ValueError:
                data = {"raw": resp.text}
        else:
            data = {"raw": resp.text}

        log.info("response status=%s elapsed_ms=%s body=%s", resp.status_code, elapsed_ms, data)

        if resp.status_code >= 400:
            # Binance style: {"code": -1021, "msg": "..."}
            msg = None
            if isinstance(data, dict):
                msg = data.get("msg") or data.get("message")
            raise BinanceAPIError(status_code=resp.status_code, message=msg or f"HTTP {resp.status_code}", payload=data)

        return data

    def place_order(self, *, params: dict[str, Any]) -> Any:
        return self._request("POST", "/fapi/v1/order", signed=True, params=params)
