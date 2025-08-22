import os
import time
import types
import pytest
from unittest.mock import patch, MagicMock


class DummyEvent:
    def __init__(self, to_addr, value):
        self.args = {"to": to_addr, "value": value}

    def __getitem__(self, k):
        return getattr(self, k)


class DummyTransferEvent:
    def process_log(self, log):
        return DummyEvent(log["to"], log["value"])


@pytest.fixture
def mock_circlelayer_service():
    class MockEth:
        def __init__(self):
            self.block_number = 123
        def get_logs(self, params):
            return []
    class MockW3:
        def __init__(self):
            self.eth = MockEth()
        @staticmethod
        def to_checksum_address(a):
            return a
    class MockContract:
        class events:
            Transfer = DummyTransferEvent
    class MockSvc:
        def __init__(self):
            self.w3 = MockW3()
        def get_confirmed_block(self, conf):
            return self.w3.eth.block_number - conf
        def erc20_contract(self, token):
            return MockContract()
    return MockSvc


@patch("app.circlelayer_service.CircleLayerService")
@patch("app.main.handle_successful_payment")
def test_poller_succeeds_on_transfer(mock_handle, mock_svc_cls, mock_circlelayer_service):
    svc = mock_svc_cls.return_value = mock_circlelayer_service()
    to_addr = "0xabc"
    svc.w3.eth.get_logs = lambda params: [{"to": to_addr, "value": 1000000}]

    from app.tasks import poll_circlelayer_payment_task
    poll_circlelayer_payment_task("telegram:1", to_addr, "0xToken", amount_units=1.0, decimals=6, poll_interval=0, timeout_seconds=1)

    mock_handle.assert_called_once()


@patch("app.circlelayer_service.CircleLayerService")
@patch("app.main.handle_successful_payment")
def test_poller_times_out_without_payment(mock_handle, mock_svc_cls, mock_circlelayer_service):
    svc = mock_svc_cls.return_value = mock_circlelayer_service()
    svc.w3.eth.get_logs = lambda params: []

    from app.tasks import poll_circlelayer_payment_task
    poll_circlelayer_payment_task("telegram:1", "0xaddr", "0xToken", amount_units=2.0, decimals=6, poll_interval=0, timeout_seconds=0.2)

    mock_handle.assert_not_called() 