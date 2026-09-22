"""Thin, read-only async client for the HORIZON API (horizon-api v2.x).

Facts about the API this client encodes (discovered empirically, the vendor
documentation does not describe response schemas):

* Auth: header ``x-api-key``. Missing key -> JSON 401 ``{"message": "API key requerida"}``.
* Cloudflare WAF in front: non-browser User-Agents get an HTML 403 (error 1010).
* Every list endpoint answers with the envelope
  ``{"ok": bool, "error": str, "hits": int, "size": int, "data": [...], "scroll_id": str|null}``.
* Pages hold at most 1000 rows. The first request omits ``scroll_id``; following
  requests pass the previous one. The last page with data still carries a
  ``scroll_id``; the terminating page has ``size == 0`` and ``scroll_id == null``.
* Filters: ``ip`` (single IP or CIDR) XOR ``domain``; optional ``new_only``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from .config import Settings

log = logging.getLogger(__name__)

PAGE_SIZE = 1000


class HorizonError(RuntimeError):
    """A request to HORIZON failed in a way the caller should see."""


class HorizonClient:
    """Async HTTP client with polite rate limiting and scroll pagination."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.api_url,
            headers={
                "x-api-key": settings.api_key,
                "Accept": "application/json",
                "User-Agent": settings.user_agent,
            },
            timeout=settings.timeout_seconds,
            transport=transport,
        )
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ low level

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET one endpoint and return the parsed JSON envelope (or object)."""
        async with self._lock:
            wait = self._settings.min_request_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                response = await self._client.get(path, params=params)
            except httpx.HTTPError as exc:
                raise HorizonError(f"network error calling HORIZON {path}: {exc}") from exc
            finally:
                self._last_request = time.monotonic()

        content_type = response.headers.get("content-type", "")
        if response.status_code == 403 and "text/html" in content_type:
            raise HorizonError(
                "HORIZON's WAF (Cloudflare) blocked the request with HTTP 403. This usually "
                "means the User-Agent is rejected; set HORIZON_USER_AGENT to a browser-like "
                "value. It can also be an IP-based block."
            )
        if response.status_code == 401:
            raise HorizonError("HORIZON rejected the API key (HTTP 401). Check HORIZON_API_KEY.")
        if response.status_code == 422:
            raise HorizonError(f"HORIZON rejected the parameters (HTTP 422): {response.text[:300]}")
        if response.status_code != 200:
            raise HorizonError(f"HORIZON returned HTTP {response.status_code} for {path}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise HorizonError(f"HORIZON returned non-JSON content for {path}") from exc

        if isinstance(payload, dict) and payload.get("ok") is False:
            raise HorizonError(f"HORIZON returned an error for {path}: {payload.get('error')!r}")
        return payload

    async def fetch_all(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        max_rows: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Follow scroll pagination and return ``(rows, total_hits)``.

        Rows are capped at *max_rows* if given (the total still reflects the full
        result set, so callers can tell the model that the list was truncated).
        Stops on an empty page, a missing ``scroll_id``, or once ``hits`` rows
        have been read, which saves the final empty request.
        """
        rows: list[dict[str, Any]] = []
        total: int | None = None
        params = dict(params or {})
        scroll_id: str | None = None
        while True:
            if scroll_id:
                params["scroll_id"] = scroll_id
            page = await self.get(path, params)
            if total is None:
                total = int(page.get("hits") or 0)
            data = page.get("data") or []
            for row in data:
                if max_rows is not None and len(rows) >= max_rows:
                    return rows, total
                rows.append(row)
            scroll_id = page.get("scroll_id")
            if not data or not scroll_id or len(rows) >= total:
                return rows, total

    # ------------------------------------------------------------------ endpoints

    async def root(self) -> dict[str, Any]:
        return await self.get("/")

    async def account(self) -> dict[str, Any]:
        return await self.get("/account")

    async def inventory_nets(self) -> list[dict[str, Any]]:
        rows, _ = await self.fetch_all("/inventory-nets")
        return rows

    async def inventory_fqdns(self) -> list[dict[str, Any]]:
        rows, _ = await self.fetch_all("/inventory-fqdns")
        return rows

    async def ports(self, ip: str, *, max_rows: int | None = None, new_only: bool = False):
        return await self.fetch_all("/ports", _q(ip, new_only), max_rows=max_rows)

    async def cves(self, ip: str, *, max_rows: int | None = None, new_only: bool = False):
        return await self.fetch_all("/cves", _q(ip, new_only), max_rows=max_rows)

    async def eol(self, ip: str, *, max_rows: int | None = None):
        return await self.fetch_all("/eol", _q(ip), max_rows=max_rows)

    async def vulns_web(self, ip: str, *, max_rows: int | None = None, new_only: bool = False):
        return await self.fetch_all("/vulns_web", _q(ip, new_only), max_rows=max_rows)

    async def httpinfo(self, ip: str, *, max_rows: int | None = None):
        return await self.fetch_all("/httpinfo", _q(ip), max_rows=max_rows)

    async def tls(self, ip: str, *, max_rows: int | None = None):
        return await self.fetch_all("/tls", _q(ip), max_rows=max_rows)


def _q(ip: str, new_only: bool = False) -> dict[str, Any]:
    params: dict[str, Any] = {"ip": ip}
    if new_only:
        params["new_only"] = "true"
    return params
