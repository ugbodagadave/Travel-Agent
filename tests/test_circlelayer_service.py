import os
import builtins
import types
import pytest
from unittest.mock import MagicMock, patch

# Patch web3 import inside module under test

@pytest.fixture
def mock_w3():
    class MockEth:
        def __init__(self):
            self.chain_id = int(os.getenv("CIRCLE_LAYER_CHAIN_ID", "28525"))
            self.block_number = 100

        def contract(self, address=None, abi=None):
            class MockContract:
                class functions:
                    @staticmethod
                    def decimals():
                        class Call:
                            @staticmethod
                            def call():
                                return 6
                        return Call()
            return MockContract()

    class MockWeb3:
        def __init__(self, provider):
            self.eth = MockEth()
        def is_connected(self):
            return True
        @staticmethod
        def to_checksum_address(addr):
            return addr

    return MockWeb3


@patch("app.circlelayer_service.Web3")
def test_service_connects_and_validates_chain_id(mock_web3_cls, monkeypatch, mock_w3):
    mock_web3_cls.HTTPProvider.return_value = object()
    mock_web3_cls.return_value = mock_w3(None)

    from app.circlelayer_service import CircleLayerService

    os.environ.setdefault("CIRCLE_LAYER_RPC_URL", "http://localhost:8545")
    os.environ.setdefault("CIRCLE_LAYER_CHAIN_ID", "28525")

    svc = CircleLayerService()
    assert svc.get_confirmed_block(3) == 97


@patch("app.circlelayer_service.Web3")
def test_get_token_decimals(mock_web3_cls, mock_w3):
    mock_web3_cls.HTTPProvider.return_value = object()
    mock_web3_cls.return_value = mock_w3(None)

    from app.circlelayer_service import CircleLayerService

    svc = CircleLayerService(rpc_url="http://localhost:8545", chain_id=28525)
    assert svc.get_token_decimals("0xToken") == 6


@patch("app.circlelayer_service.Web3")
def test_create_deposit_address_returns_address_and_index(mock_web3_cls, mock_w3):
    mock_web3_cls.HTTPProvider.return_value = object()
    mock_web3_cls.return_value = mock_w3(None)

    from app.circlelayer_service import CircleLayerService

    svc = CircleLayerService(rpc_url="http://localhost:8545", chain_id=28525)
    data = svc.create_deposit_address(index=0)
    assert "address" in data and "index" in data 