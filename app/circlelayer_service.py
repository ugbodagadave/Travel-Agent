import os
from typing import Optional, Dict

# Lazy/forgiving imports so tests can run without native wheels
try:
    from web3 import Web3  # type: ignore
except Exception:  # ImportError or environment issues
    Web3 = None  # type: ignore

try:
    from eth_account import Account  # type: ignore
    from eth_account.hdaccount import ETHEREUM_DEFAULT_PATH  # type: ignore
except Exception:  # ImportError or environment issues
    class _StubAccount:
        @staticmethod
        def create():
            class _A:
                address = "0x0000000000000000000000000000000000000000"
                key = b""
            return _A()

        @staticmethod
        def from_mnemonic(mnemonic: str, account_path: str):
            class _A:
                address = "0x0000000000000000000000000000000000000000"
                key = b""
            return _A()

        @staticmethod
        def enable_unaudited_hdwallet_features():
            return None
    Account = _StubAccount()  # type: ignore
    ETHEREUM_DEFAULT_PATH = "m/44'/60'/0'/0/0"  # type: ignore

MINIMAL_ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class CircleLayerService:
    """Minimal Web3 service for Circle Layer Testnet operations.

    Responsibilities:
    - Connect to RPC, validate chain id.
    - Provide ERC-20 contract accessors and utilities.
    - Derive deposit addresses (index-based) without exposing private keys.
    - Compute confirmed block numbers.
    """

    def __init__(self, rpc_url: Optional[str] = None, chain_id: Optional[int] = None):
        if Web3 is None:
            raise RuntimeError("Web3 is not available in this environment")
        self.rpc_url = rpc_url or os.getenv("CIRCLE_LAYER_RPC_URL")
        self.chain_id_env = chain_id or self._safe_int(os.getenv("CIRCLE_LAYER_CHAIN_ID"))
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError("Cannot connect to Circle Layer RPC URL")
        if self.chain_id_env is not None:
            onchain_chain_id = self.w3.eth.chain_id
            if onchain_chain_id != self.chain_id_env:
                raise RuntimeError(f"Chain ID mismatch: expected {self.chain_id_env}, got {onchain_chain_id}")

    @staticmethod
    def _safe_int(value: Optional[str]) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def erc20_contract(self, token_address: str):
        checksum = Web3.to_checksum_address(token_address)  # type: ignore
        return self.w3.eth.contract(address=checksum, abi=MINIMAL_ERC20_ABI)

    def get_token_decimals(self, token_address: str) -> int:
        return int(self.erc20_contract(token_address).functions.decimals().call())

    def get_confirmed_block(self, min_confirmations: Optional[int] = None) -> int:
        conf = min_confirmations if min_confirmations is not None else self._safe_int(os.getenv("CIRCLE_LAYER_MIN_CONFIRMATIONS")) or 3
        latest = self.w3.eth.block_number
        return max(0, latest - conf)

    def derive_address_at_index(self, index: int) -> str:
        """Deterministically derives an address at BIP44 path m/44'/60'/0'/0/index from mnemonic.
        Returns a checksummed address string.
        """
        mnemonic = os.getenv("CIRCLE_LAYER_MERCHANT_MNEMONIC")
        if not mnemonic:
            raise RuntimeError("CIRCLE_LAYER_MERCHANT_MNEMONIC is not set")
        base_path = os.getenv("CIRCLE_LAYER_DERIVATION_PATH", "m/44'/60'/0'/0/{index}")
        account_path = base_path.format(index=index)
        # enable hdwallet features if required by eth-account
        enable = getattr(Account, "enable_unaudited_hdwallet_features", None)
        if callable(enable):
            enable()
        acct = Account.from_mnemonic(mnemonic, account_path=account_path)  # type: ignore
        # Normalize as checksum address
        return Web3.to_checksum_address(acct.address)  # type: ignore

    def create_deposit_address(self, index: int) -> Dict[str, str]:
        """Create a deposit address record for a given index.
        Returns: {"address": address, "index": str(index)}
        """
        address = self.derive_address_at_index(index)
        return {"address": address, "index": str(index)} 