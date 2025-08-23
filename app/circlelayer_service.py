import os
from typing import Optional, Dict, List

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
    """Web3 utilities for Circle Layer Testnet with lazy RPC connection.

    - __init__ does not connect; use connect() on-demand.
    - create_deposit_address is classmethod (no RPC needed).
    """

    def __init__(self, rpc_url: Optional[str] = None, chain_id: Optional[int] = None):
        self.rpc_url = rpc_url or os.getenv("CIRCLE_LAYER_RPC_URL")
        self.chain_id_env = chain_id or self._safe_int(os.getenv("CIRCLE_LAYER_CHAIN_ID"))
        self.w3 = None

    def _get_rpc_urls(self) -> List[str]:
        urls = []
        multi = os.getenv("CIRCLE_LAYER_RPC_URLS", "")
        if self.rpc_url:
            urls.append(self.rpc_url)
        if multi:
            for u in multi.split(","):
                u = u.strip()
                if u and u not in urls:
                    urls.append(u)
        return urls

    def connect(self):
        if Web3 is None:
            raise RuntimeError("Web3 is not available in this environment")
        if self.w3 is not None:
            return
        timeout = float(os.getenv("CIRCLE_LAYER_RPC_TIMEOUT", "5"))
        last_error = None
        for url in self._get_rpc_urls():
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": timeout}))
                if not w3.is_connected():
                    raise RuntimeError("RPC not connected")
                if self.chain_id_env is not None:
                    onchain_chain_id = w3.eth.chain_id
                    if onchain_chain_id != self.chain_id_env:
                        raise RuntimeError(f"Chain ID mismatch: expected {self.chain_id_env}, got {onchain_chain_id}")
                self.w3 = w3
                return
            except Exception as e:
                print(f"[CircleLayerService] WARNING: Failed to connect {url}: {e}")
                last_error = e
                continue
        raise RuntimeError(f"Unable to connect to any Circle Layer RPC URL. Last error: {last_error}")

    @staticmethod
    def _safe_int(value: Optional[str]) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def erc20_contract(self, token_address: str):
        self.connect()
        checksum = self.w3.to_checksum_address(token_address)  # type: ignore
        return self.w3.eth.contract(address=checksum, abi=MINIMAL_ERC20_ABI)

    def get_token_decimals(self, token_address: str) -> int:
        return int(self.erc20_contract(token_address).functions.decimals().call())

    def get_confirmed_block(self, min_confirmations: Optional[int] = None) -> int:
        self.connect()
        conf = min_confirmations if min_confirmations is not None else self._safe_int(os.getenv("CIRCLE_LAYER_MIN_CONFIRMATIONS")) or 3
        latest = self.w3.eth.block_number
        return max(0, latest - conf)

    @classmethod
    def derive_address_at_index(cls, index: int) -> str:
        """Deterministically derives an address at BIP44 path m/44'/60'/0'/0/index from mnemonic.
        Returns a checksummed address string. No RPC required.
        """
        mnemonic = os.getenv("CIRCLE_LAYER_MERCHANT_MNEMONIC")
        if not mnemonic:
            raise RuntimeError("CIRCLE_LAYER_MERCHANT_MNEMONIC is not set")
        base_path = os.getenv("CIRCLE_LAYER_DERIVATION_PATH", "m/44'/60'/0'/0/{index}")
        account_path = base_path.format(index=index)
        enable = getattr(Account, "enable_unaudited_hdwallet_features", None)
        if callable(enable):
            enable()
        acct = Account.from_mnemonic(mnemonic, account_path=account_path)  # type: ignore
        if Web3 is None:
            return acct.address
        return Web3.to_checksum_address(acct.address)  # type: ignore

    @classmethod
    def create_deposit_address(cls, index: int) -> Dict[str, str]:
        address = cls.derive_address_at_index(index)
        return {"address": address, "index": str(index)}

    def check_native_balance(self, address: str, min_confirmations: Optional[int] = None) -> int:
        """Check the native token balance for a given address.
        
        Args:
            address: The address to check balance for
            min_confirmations: Minimum confirmations required (default from env or 3)
            
        Returns:
            Balance in wei (smallest unit)
        """
        self.connect()
        checksum_addr = self.w3.to_checksum_address(address)
        
        # Get balance at confirmed block
        confirmed_block = self.get_confirmed_block(min_confirmations)
        balance = self.w3.eth.get_balance(checksum_addr, block_identifier=confirmed_block)
        
        return balance

    def get_transaction_status(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction details and status.
        
        Args:
            tx_hash: Transaction hash to check
            
        Returns:
            Transaction details dict or None if not found
        """
        try:
            self.connect()
            tx = self.w3.eth.get_transaction(tx_hash)
            if tx:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                return {
                    "hash": tx_hash,
                    "from": tx["from"],
                    "to": tx["to"],
                    "value": tx["value"],
                    "block_number": tx["blockNumber"],
                    "status": receipt["status"] if receipt else None,
                    "confirmations": self.w3.eth.block_number - tx["blockNumber"] if tx["blockNumber"] else 0
                }
        except Exception as e:
            print(f"[CircleLayerService] ERROR getting transaction status: {e}")
        return None

    def get_address_info(self, address: str) -> Dict:
        """Get comprehensive address information including balance and transaction count.
        
        Args:
            address: The address to get information for
            
        Returns:
            Dictionary with address information
        """
        try:
            self.connect()
            checksum_addr = self.w3.to_checksum_address(address)
            
            # Get current balance
            balance = self.w3.eth.get_balance(checksum_addr)
            
            # Get transaction count (nonce)
            nonce = self.w3.eth.get_transaction_count(checksum_addr)
            
            return {
                "address": checksum_addr,
                "balance": balance,
                "nonce": nonce,
                "balance_eth": self.w3.from_wei(balance, 'ether')
            }
        except Exception as e:
            print(f"[CircleLayerService] ERROR getting address info: {e}")
            return {
                "address": address,
                "balance": 0,
                "nonce": 0,
                "balance_eth": 0
            } 