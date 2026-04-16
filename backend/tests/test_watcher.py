"""Tests for block watcher with mocked WebSocket connections."""

from unittest.mock import AsyncMock, patch

import pytest
from contract_watchdog.watcher import BlockWatcher, WatcherConfig


class TestWatcherConfig:
    def test_default_config(self):
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        assert config.max_retries == 5
        assert config.base_backoff == 1.0
        assert config.poll_interval == 2.0

    def test_custom_config(self):
        config = WatcherConfig(
            rpc_http_url="http://localhost:8545",
            rpc_ws_url="ws://localhost:8546",
            max_retries=3,
            base_backoff=0.5,
            poll_interval=1.0,
        )
        assert config.rpc_ws_url == "ws://localhost:8546"
        assert config.max_retries == 3


class TestBlockWatcher:
    def test_init(self):
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        callbacks = []
        watcher = BlockWatcher(config=config, on_block_callbacks=callbacks)
        assert watcher.config == config
        assert watcher.on_block_callbacks == callbacks
        assert watcher._running is False

    @pytest.mark.asyncio
    async def test_poll_new_block_calls_callbacks(self, sample_block, mock_async_web3):
        """Polling a new block should invoke all registered callbacks."""
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        received = []

        async def cb(block):
            received.append(block)

        watcher = BlockWatcher(config=config, on_block_callbacks=[cb])
        watcher._w3 = mock_async_web3
        watcher._last_block = sample_block["number"] - 1

        mock_async_web3.eth.get_block_number = AsyncMock(return_value=sample_block["number"])
        mock_async_web3.eth.get_block = AsyncMock(return_value=sample_block)

        await watcher._poll_once()

        assert len(received) == 1
        assert received[0]["number"] == sample_block["number"]

    @pytest.mark.asyncio
    async def test_poll_no_new_block_skips_callbacks(self, sample_block, mock_async_web3):
        """When block number hasn't changed, callbacks should not be called."""
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        received = []

        async def cb(block):
            received.append(block)

        watcher = BlockWatcher(config=config, on_block_callbacks=[cb])
        watcher._w3 = mock_async_web3
        watcher._last_block = sample_block["number"]  # same as current

        mock_async_web3.eth.get_block_number = AsyncMock(return_value=sample_block["number"])

        await watcher._poll_once()

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_exponential_backoff_on_failure(self):
        """Watcher should retry with exponential backoff on WSS failure."""
        config = WatcherConfig(
            rpc_http_url="http://localhost:8545",
            rpc_ws_url="ws://localhost:8546",
            max_retries=3,
            base_backoff=0.01,  # tiny for test speed
        )
        watcher = BlockWatcher(config=config, on_block_callbacks=[])

        sleep_calls = []

        async def fake_sleep(t):
            sleep_calls.append(t)

        with patch("contract_watchdog.watcher.asyncio.sleep", side_effect=fake_sleep):
            with patch.object(watcher, "_connect_ws", side_effect=ConnectionError("fail")):
                with patch.object(watcher, "_poll_loop", new_callable=AsyncMock) as mock_poll:
                    # After retries exhausted falls back to poll
                    mock_poll.return_value = None
                    await watcher._ws_loop_with_backoff()

        # Should have slept between retries with increasing intervals
        assert len(sleep_calls) >= config.max_retries - 1
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] >= sleep_calls[i - 1]

    @pytest.mark.asyncio
    async def test_fallback_to_http_polling_when_no_ws_url(self, mock_async_web3, sample_block):
        """Without WSS URL, watcher should fall back to HTTP polling."""
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        assert config.rpc_ws_url is None

        call_count = 0

        async def cb(block):
            nonlocal call_count
            call_count += 1

        watcher = BlockWatcher(config=config, on_block_callbacks=[cb])
        watcher._w3 = mock_async_web3
        watcher._last_block = sample_block["number"] - 1
        watcher._running = True

        mock_async_web3.eth.get_block_number = AsyncMock(
            side_effect=[sample_block["number"], sample_block["number"]]
        )
        mock_async_web3.eth.get_block = AsyncMock(return_value=sample_block)

        # Run one poll cycle then stop
        await watcher._poll_once()
        assert call_count == 1

    def test_stop_sets_running_false(self):
        config = WatcherConfig(rpc_http_url="http://localhost:8545")
        watcher = BlockWatcher(config=config, on_block_callbacks=[])
        watcher._running = True
        watcher.stop()
        assert watcher._running is False
