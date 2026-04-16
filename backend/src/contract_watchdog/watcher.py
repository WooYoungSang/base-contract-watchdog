"""Block watcher — subscribes to Base blocks via WebSocket with HTTP polling fallback."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

logger = logging.getLogger(__name__)


@dataclass
class WatcherConfig:
    rpc_http_url: str
    rpc_ws_url: str | None = None
    max_retries: int = 5
    base_backoff: float = 1.0
    poll_interval: float = 2.0


BlockCallback = Callable[[dict], Awaitable[None]]


class BlockWatcher:
    """Watches Base for new blocks and invokes registered callbacks."""

    def __init__(self, config: WatcherConfig, on_block_callbacks: list[BlockCallback]) -> None:
        self.config = config
        self.on_block_callbacks = on_block_callbacks
        self._running = False
        self._last_block: int = -1
        self._w3: AsyncWeb3 | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the watcher. Uses WSS if configured, falls back to HTTP polling."""
        self._running = True
        self._w3 = AsyncWeb3(AsyncHTTPProvider(self.config.rpc_http_url))

        if self.config.rpc_ws_url:
            await self._ws_loop_with_backoff()
        else:
            await self._poll_loop()

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Internal: WebSocket path
    # ------------------------------------------------------------------

    async def _ws_loop_with_backoff(self) -> None:
        """Try WSS connection with exponential backoff; fall back to polling on exhaustion."""
        attempt = 0
        while attempt < self.config.max_retries:
            try:
                await self._connect_ws()
                return  # clean exit if WSS loop ends normally
            except Exception as exc:
                attempt += 1
                delay = self.config.base_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "WSS connection failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt,
                    self.config.max_retries,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

        logger.error("WSS failed after %d retries; falling back to HTTP polling", self.config.max_retries)
        await self._poll_loop()

    async def _connect_ws(self) -> None:
        """Connect via WebSocket and stream new-head subscriptions."""
        from web3 import AsyncWeb3
        from web3.providers.persistent import WebSocketProvider

        async with AsyncWeb3(WebSocketProvider(self.config.rpc_ws_url)) as ws_w3:
            async for block_data in ws_w3.socket.process_subscriptions():
                if not self._running:
                    break
                block = await ws_w3.eth.get_block(block_data["result"]["number"], full_transactions=False)
                await self._dispatch(dict(block))

    # ------------------------------------------------------------------
    # Internal: HTTP polling path
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Poll for new blocks via HTTP at configured interval."""
        while self._running:
            try:
                await self._poll_once()
            except Exception as exc:
                logger.warning("Poll error: %s", exc)
            await asyncio.sleep(self.config.poll_interval)

    async def _poll_once(self) -> None:
        """Single poll iteration — fetch latest block number and dispatch if new."""
        latest = await self._w3.eth.get_block_number()
        if latest <= self._last_block:
            return

        # Catch up if we missed blocks (e.g. after reconnect)
        for block_num in range(self._last_block + 1, latest + 1):
            try:
                block = await self._w3.eth.get_block(block_num, full_transactions=False)
                await self._dispatch(dict(block))
            except Exception as exc:
                logger.warning("Failed to fetch block %d: %s", block_num, exc)

        self._last_block = latest

    # ------------------------------------------------------------------
    # Internal: dispatch
    # ------------------------------------------------------------------

    async def _dispatch(self, block: dict) -> None:
        """Invoke all registered callbacks with the block data."""
        for cb in self.on_block_callbacks:
            try:
                await cb(block)
            except Exception as exc:
                logger.error("Callback %s raised: %s", cb, exc)
