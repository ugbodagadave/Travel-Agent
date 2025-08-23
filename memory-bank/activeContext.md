# Active Context

## Current Focus
- Add Circle Layer on-chain payment option (testnet) alongside Stripe and Circle USDC.

## Recent Changes
- Defined env vars and architecture for Circle Layer EVM payments via background polling.

## Next Steps
- Add `circlelayer_service.py` and Web3 dependency.
- Implement `poll_circlelayer_payment_task`.
- Extend `AWAITING_PAYMENT_SELECTION` state to support "Circle Layer".
- Add Redis mappings for EVM deposit addresses.

## Decisions
- Start with fixed test amount and ERC-20 token for simplicity.
- Poll with 3 confirmations; 15s interval; 1h timeout.

## Risks
- RPC instability; explorer/token availability on testnet.
- Secret management for mnemonic/private key.
