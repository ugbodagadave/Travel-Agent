import os
from typing import Optional, Dict
from web3 import Web3
from eth_account import Account

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
        checksum = Web3.to_checksum_address(token_address)
        return self.w3.eth.contract(address=checksum, abi=MINIMAL_ERC20_ABI)

    def get_token_decimals(self, token_address: str) -> int:
        return int(self.erc20_contract(token_address).functions.decimals().call())

    def get_confirmed_block(self, min_confirmations: Optional[int] = None) -> int:
        conf = min_confirmations if min_confirmations is not None else self._safe_int(os.getenv("CIRCLE_LAYER_MIN_CONFIRMATIONS")) or 3
        latest = self.w3.eth.block_number
        return max(0, latest - conf)

    def create_deposit_address(self, index: int) -> Dict[str, str]:
        """Derive an address from mnemonic at index. For now, use ephemeral Account.create()
        as a placeholder to unblock testing; will be replaced with BIP44 derivation in Phase 2.
        Returns: {"address": address, "index": str(index)}
        """
        acct = Account.create()
        return {"address": acct.address, "index": str(index)} 