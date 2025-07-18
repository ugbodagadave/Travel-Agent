# Integrating USDC Payments with Circle

This document outlines the step-by-step plan to integrate USDC as a payment method using the Circle API.

### Production Note

This implementation is designed for a **sandbox environment**. The current flow confirms the booking and generates tickets immediately after receiving a Circle webhook notification for a successful payment. In a production environment, this would be insufficient. Since Amadeus requires payment in fiat currency (e.g., USD, EUR), a real-world system would need a liquidity and settlement mechanism. Once the user's USDC payment is confirmed, the system would need to draw from a fiat liquidity pool to pay Amadeus for the actual flight booking. The collected USDC would then be settled into the company's Circle account. This plan does not include the implementation of such a liquidity pool.

---

### Step-by-Step Implementation Plan

#### Phase 1: Circle Service and API Client

1.  **Create `app/circle_service.py`:** This new service will encapsulate all logic for interacting with the Circle API. It will be initialized with the `CIRCLE_API_KEY` from the environment variables.
2.  **Implement API Client:** The service will use a library like `requests` to make authenticated calls to the Circle Sandbox API (`https://api-sandbox.circle.com`). It will handle setting the `Authorization: Bearer <API_KEY>` header for all requests.
3.  **Implement Wallet Generation:** The service will have a method, `create_payment_wallet()`, which calls the Circle API to create a new, unique wallet for each transaction. This ensures payments are tracked individually. This method will return the unique wallet address to which the user will send funds.

#### Phase 2: Currency Conversion Service

1.  **API Selection:** We will use the free, open-source **Frankfurter.app API** for currency conversions. It requires no API key.
2.  **Create `app/currency_service.py`:** This new service will manage all currency conversion logic.
3.  **Implement `convert_to_usd` Method:** This method will take a source currency (e.g., 'EUR') and an amount, then call the Frankfurter API to get the equivalent amount in USD.

#### Phase 3: Modify Conversation Flow

1.  **Add `AWAITING_PAYMENT_SELECTION` State:** In `app/core_logic.py`, after a user selects a flight in the `FLIGHT_SELECTION` state, we will no longer immediately create a Stripe session. Instead, the state will transition to `AWAITING_PAYMENT_SELECTION`.
2.  **Prompt for Payment Method:** The user will be asked to choose their payment method, for example: "How would you like to pay for your flight? (Reply with 'Card' or 'USDC')".

#### Phase 4: Implement USDC Payment Path

1.  **Handle "USDC" Selection:** In `app/core_logic.py`, if the user chooses "USDC", the application will:
    a.  Use the new **`currency_service`** to convert the flight's total price to USD.
    b.  Call the `circle_service.create_payment_wallet()` to get a unique deposit address.
    c.  Save a mapping of `wallet_id -> user_id` in Redis. This is crucial for the webhook to retrieve the correct session later.
    d.  Display the wallet address and the exact USDC amount to the user.
    e.  Transition the state to `AWAITING_USDC_PAYMENT`.

#### Phase 5: Create Circle Webhook Handler

1.  **Add `/circle-webhook` Endpoint:** In `app/main.py`, create a new endpoint to receive webhook notifications from Circle.
2.  **Handle Payment Notifications:** The webhook will listen for `notifications.transfer.in` events. When a notification is received, it will:
    a.  Parse the payload to get the destination wallet address and the transferred amount.
    b.  Use the wallet address to look up the `user_id` from the Redis mapping.
    c.  Load the user's session.
    d.  Verify that the received USDC amount matches the expected flight cost.
    e.  If everything is correct, trigger the existing post-payment logic: generate personalized PDF tickets for all travelers and send them via the appropriate messaging platform.

#### Phase 6: Testing Strategy

1.  **`CircleService` Unit Tests:** Create `tests/test_circle_service.py` to test the `CircleService` in isolation by mocking the Circle API calls.
2.  **`CurrencyService` Unit Tests:** Create `tests/test_currency_service.py` to test the currency conversion logic, including successful conversions and error handling.
3.  **Core Logic Unit Tests:** Update `tests/test_core_logic.py` to add tests for the new `AWAITING_PAYMENT_SELECTION` and `AWAITING_USDC_PAYMENT` conversation states.
4.  **Webhook Integration Test:** Update `tests/test_app.py` to add a test for the `/circle-webhook` endpoint. This test will send a mock Circle webhook payload and assert that the PDF generation and delivery are triggered correctly.
5.  **Full Test Suite Execution:** After each major change, run the entire `pytest` suite to ensure no existing functionality has been broken. 