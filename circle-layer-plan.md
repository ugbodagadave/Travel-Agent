# Circle Layer Integration Plan (Testnet)

This document is the authoritative, step-by-step plan to integrate on-chain payments via Circle Layer Testnet into the AI Travel Agent. It follows the Test → Document → Commit → Push workflow.

## Objectives
- Add a third payment option: Circle Layer on-chain payment (ERC-20 on testnet).
- Maintain non-blocking UX via background polling.
- Reuse unified payment success handler to deliver tickets.
- Provide robust tests for services, tasks, and conversation state flows.

## Prerequisites
- Env vars added:
  - `CIRCLE_LAYER_RPC_URL`, `CIRCLE_LAYER_CHAIN_ID`
  - `CIRCLE_LAYER_TOKEN_ADDRESS`, `CIRCLE_LAYER_TOKEN_SYMBOL`, `CIRCLE_LAYER_TOKEN_DECIMALS`
  - `CIRCLE_LAYER_MERCHANT_MNEMONIC` (or `CIRCLE_LAYER_MERCHANT_PRIVATE_KEY`)
  - `CIRCLE_LAYER_MIN_CONFIRMATIONS` (default 3), `CIRCLE_LAYER_POLL_INTERVAL` (default 15)
  - `CIRCLE_LAYER_EXPLORER_BASE_URL` (optional)
- Dependencies to add to `requirements.txt`:
  - `web3==6.19.0`
  - `eth-account==0.13.3`

## High-Level Design
1. New service `app/circlelayer_service.py` using Web3:
   - Connect to RPC with chain ID validation.
   - Create deposit addresses per order (HD derivation from mnemonic, index-based).
   - Read token `decimals()` and decode `Transfer` events.
   - Utility for computing confirmed block (latest - confirmations).
2. Redis mappings in `app/new_session_manager.py`:
   - `save_evm_mapping(address, user_id)` / `get_user_id_from_evm_address(address)` with TTL.
   - Store per-order info in session under `flight_details['circlelayer']`.
3. Background task in `app/tasks.py`:
   - `poll_circlelayer_payment_task(user_id, address, token_address, amount_units, decimals, poll_interval, min_conf)`
   - Loop: get confirmed block window → query ERC-20 `Transfer` logs → sum to `address` → compare against target amount (units * 10**decimals) → on success call `handle_successful_payment(user_id)`.
   - Timeout and log on failure.
4. Extend `app/core_logic.py` in `AWAITING_PAYMENT_SELECTION`:
   - Accept "Circle Layer" / "CLAYER".
   - Compute expected amount (initially fixed test amount, e.g., 10.00).
   - Derive deposit address, save mapping + details, start poller, set state `AWAITING_CIRCLE_LAYER_PAYMENT` and message user.
5. Docs updates in `README.md` and `how-it-works.md`.

## Security Considerations
- Never log secrets. Keep mnemonic/private key only in env.
- Use separate testnet wallet; rotate if leaked.
- Use 3 confirmations by default.
- Optionally sweep deposit addresses later (not in scope).

## Testing Strategy

### Unit Tests
- `test_circlelayer_service.py`
  - Mocks Web3 provider.
  - Validates checksum conversion, decimals retrieval, derivation index behavior.
  - Decodes `Transfer` event logs to expected values.
- `test_tasks_circlelayer.py`
  - Mocks service to return crafted logs and block numbers.
  - Verifies polling detects payment, calls `handle_successful_payment` exactly once.
  - Tests underpayment and timeout paths.
- `test_core_logic_circlelayer.py`
  - Simulates conversation up to `AWAITING_PAYMENT_SELECTION` and chooses "Circle Layer".
  - Asserts session state changes to `AWAITING_CIRCLE_LAYER_PAYMENT`, mapping saved, and messages include address.

### Integration Tests (optional if RPC available)
- Requires real RPC and faucet funds.
- Send token to generated deposit address; assert success handler triggered.

### Non-regression Tests
- Ensure existing Stripe and Circle USDC flows remain green.

## Step-by-Step Phases

### Phase 1: Dependencies & Service Skeleton (Test First)
1. Add `web3` and `eth-account` to `requirements.txt`.
2. Create `app/circlelayer_service.py` skeleton with:
   - RPC connect, chain ID check, ERC‑20 ABI, `get_decimals`, `get_confirmed_block`, stub `derive_address(index)`.
3. Write unit tests for the service (with mocks).
4. Run tests; fix until green.

### Phase 2: Deposit Address Derivation
1. Implement HD derivation from mnemonic (BIP44 m/44'/60'/0'/0/index).
2. Expose `create_deposit_address(order_index)` returning `{address, index}`; do not store private key.
3. Tests: deterministic derivation for known mnemonic; checksum addresses.

### Phase 3: Poller Implementation
1. Implement `poll_circlelayer_payment_task` reading env defaults.
2. Sum ERC‑20 transfers to deposit address across block windows; compare to target.
3. Tests for: success, underpayment, no events, and timeout.

### Phase 4: Core Logic Wiring
1. Update `app/core_logic.py` payment selection branch for "Circle Layer".
2. Save details in session, send address message, start poller thread.
3. Tests: state transition, messages, session persistence.

### Phase 5: Docs & Examples
1. Update `README.md` and `how-it-works.md` with Circle Layer flow.
2. Provide sample `.env` snippet and troubleshooting.

### Phase 6: Manual Test (Optional)
1. Deploy to test env; trigger flow; pay with faucet token; verify receipt.

## Rollback Plan
- Feature is isolated behind new branch and payment path; revert by removing path and tests.

## Acceptance Criteria
- All tests pass (existing + new).
- Users can select "Circle Layer", receive deposit address, pay test token, and get tickets (in integration test or mocked path).
- Documentation updated with env and flow. 