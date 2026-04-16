"""Shared fixtures and sample event data for contract watchdog tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Sample EIP-1967 Upgraded event log
UPGRADED_EVENT = {
    "address": "0x4200000000000000000000000000000000000010",
    "topics": [
        # keccak256("Upgraded(address)")
        "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b",
        # new implementation address (padded)
        "0x000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    ],
    "data": "0x",
    "blockNumber": 12345678,
    "transactionHash": "0xabc123def456abc123def456abc123def456abc123def456abc123def456abc1",
    "transactionIndex": 0,
    "blockHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "logIndex": 0,
    "removed": False,
}

# Sample AdminChanged event
ADMIN_CHANGED_EVENT = {
    "address": "0x4200000000000000000000000000000000000010",
    "topics": [
        # keccak256("AdminChanged(address,address)")
        "0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f",
        # previous admin
        "0x000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        # new admin
        "0x000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    ],
    "data": "0x",
    "blockNumber": 12345679,
    "transactionHash": "0xdef456abc123def456abc123def456abc123def456abc123def456abc123def4",
    "transactionIndex": 1,
    "blockHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "logIndex": 1,
    "removed": False,
}

# Sample OwnershipTransferred event
OWNERSHIP_TRANSFERRED_EVENT = {
    "address": "0x3333333333333333333333333333333333333333",
    "topics": [
        # keccak256("OwnershipTransferred(address,address)")
        "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0",
        # previous owner
        "0x000000000000000000000000cccccccccccccccccccccccccccccccccccccccc",
        # new owner
        "0x0000000000000000000000000000000000000000000000000000000000000000",  # zero = renounced
    ],
    "data": "0x",
    "blockNumber": 12345680,
    "transactionHash": "0x111222333444555666777888999aaabbbcccdddeeefffabc123def456abc123",
    "transactionIndex": 2,
    "blockHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "logIndex": 2,
    "removed": False,
}

# Sample RoleGranted event (AccessControl)
ROLE_GRANTED_EVENT = {
    "address": "0x4444444444444444444444444444444444444444",
    "topics": [
        # keccak256("RoleGranted(bytes32,address,address)")
        "0x2f8788117e7eff1d82e926ec794901d17c78024a50270940304540a733656f0d",
        # role (MINTER_ROLE)
        "0x9f2df0fed2c77648de5860a4cc508cd0818c85b8b8a1ab4ceeef8d981c8956a6",
        # account
        "0x000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        # sender
        "0x000000000000000000000000ffffffffffffffffffffffffffffffffffffffff",
    ],
    "data": "0x",
    "blockNumber": 12345681,
    "transactionHash": "0xaabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    "transactionIndex": 3,
    "blockHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "logIndex": 3,
    "removed": False,
}

# Sample block with logs
SAMPLE_BLOCK = {
    "number": 12345678,
    "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "parentHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "timestamp": 1713312000,
    "transactions": [],
}

# Known top-10 TVL protocol addresses on Base (sample)
TOP_TVL_PROTOCOLS = {
    "0x4200000000000000000000000000000000000010",  # Base Bridge
    "0x3154cf16ccdb4c6d922629664174b904d80f2c35",  # Aerodrome
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC on Base
}


@pytest.fixture
def upgraded_event():
    return UPGRADED_EVENT.copy()


@pytest.fixture
def admin_changed_event():
    return ADMIN_CHANGED_EVENT.copy()


@pytest.fixture
def ownership_transferred_event():
    return OWNERSHIP_TRANSFERRED_EVENT.copy()


@pytest.fixture
def role_granted_event():
    return ROLE_GRANTED_EVENT.copy()


@pytest.fixture
def sample_block():
    return SAMPLE_BLOCK.copy()


@pytest.fixture
def top_tvl_protocols():
    return TOP_TVL_PROTOCOLS.copy()


@pytest.fixture
def mock_web3():
    """Mock Web3 instance for testing."""
    w3 = MagicMock()
    w3.eth = MagicMock()
    w3.eth.get_block = MagicMock(return_value=SAMPLE_BLOCK)
    w3.eth.get_logs = MagicMock(return_value=[])
    w3.is_connected = MagicMock(return_value=True)
    return w3


@pytest.fixture
def mock_async_web3():
    """Async mock Web3 instance."""
    w3 = AsyncMock()
    w3.eth = AsyncMock()
    w3.eth.get_block = AsyncMock(return_value=SAMPLE_BLOCK)
    w3.eth.get_logs = AsyncMock(return_value=[])
    return w3
