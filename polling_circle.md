# Polling for Circle Payments: Implementation Plan

This document outlines the step-by-step plan to implement a reliable polling mechanism for confirming Circle USDC payments, moving away from the currently unreliable webhook system.

## How It Will Work

The core idea is to shift from a "push" model (webhooks) to a "pull" model (polling). Instead of waiting for Circle to notify us of a successful payment, we will proactively ask Circle for the payment status at regular intervals.

1.  **User Pays with USDC**: The user selects USDC as their payment method. The application generates a unique payment address and displays it to the user.
2.  **Background Polling Starts**: As soon as the address is generated, a new background task is started.
3.  **Regular Status Checks**: This task will make an API call to Circle's `GET /v1/paymentIntents/{id}` endpoint every 30 seconds to check the status of the payment.
4.  **Confirmation and Ticket Generation**:
    *   If the status is `pending`, the poller waits and tries again.
    *   If the status is `complete`, the poller knows the payment was successful. It then triggers the existing logic to generate the PDF flight itinerary and sends it to the user.
5.  **Task Completion**: The polling task stops once the payment is confirmed or after a reasonable timeout period (e.g., 1 hour) to prevent it from running indefinitely.

## Step-by-Step Implementation Plan

### Phase 1: Core Logic Refactoring and Polling Implementation

#### 1. Refactor Ticket Generation Logic

*   **Goal**: Create a single, reusable function that handles all the logic for a successful payment, regardless of the method (Stripe, Circle webhook, or Circle polling).
*   **File**: `app/main.py`
*   **Action**:
    1.  Create a new function `handle_successful_payment(user_id)`.
    2.  Move the entire body of the `if event['type'] == 'checkout.session.completed':` block from the `stripe_webhook` function into `handle_successful_payment`.
    3.  Modify the function to take `user_id` as an argument instead of extracting it from the Stripe event.
    4.  Update the `stripe_webhook` to call `handle_successful_payment(user_id)`.
    5.  Update the `circle_webhook` to also call `handle_successful_payment(user_id)` after successfully retrieving the `user_id` from the payment intent ID.

#### 2. Create a Status-Checking Function in `CircleService`

*   **Goal**: Add a dedicated function to check the status of a payment intent.
*   **File**: `app/circle_service.py`
*   **Action**:
    1.  Create a new method `get_payment_intent_status(self, intent_id)`.
    2.  This method will make a `GET` request to `https://api-sandbox.circle.com/v1/paymentIntents/{intent_id}`.
    3.  It will parse the JSON response and return the value of the `status` field from the latest entry in the `timeline` array (e.g., `complete`, `pending`).

#### 3. Create the Background Polling Task

*   **Goal**: Create the background task that will periodically poll Circle for the payment status.
*   **File**: `app/tasks.py`
*   **Action**:
    1.  Create a new function `poll_usdc_payment_task(user_id, intent_id)`.
    2.  Inside this function, create a loop that runs for a set duration (e.g., up to 1 hour, checking every 30 seconds).
    3.  In each iteration, call the `circle_service.get_payment_intent_status(intent_id)` function.
    4.  If the status is `complete`:
        *   Call the `handle_successful_payment(user_id)` function (this will require importing it from `app.main`).
        *   Break the loop.
    5.  If the loop finishes without a `complete` status, log a message indicating the payment was not confirmed in time.

#### 4. Start the Polling Task

*   **Goal**: Trigger the new polling task when a user chooses to pay with USDC.
*   **File**: `app/core_logic.py`
*   **Action**:
    1.  In `process_message`, within the `elif "usdc" in incoming_msg.lower():` block:
    2.  After successfully creating the payment intent and getting the `walletId` (which is the `intent_id`), start the background polling task.
    3.  Use `threading.Thread` to start the `poll_usdc_payment_task`, passing the `user_id` and `intent_id`.
    4.  Example: `task_thread = threading.Thread(target=poll_usdc_payment_task, args=(user_id, payment_info['walletId']))`
    5.  `task_thread.start()`

### Phase 2: Testing

Testing is crucial to ensure the new implementation is robust.

#### 1. Unit Test for `CircleService`

*   **File**: `tests/test_circle_service.py`
*   **Action**:
    *   Write a new test `test_get_payment_intent_status`.
    *   Use `unittest.mock.patch` to mock the `requests.get` call.
    *   Create mock responses that return different statuses (`complete`, `pending`, etc.).
    *   Assert that the function correctly parses the status from the mock responses.

#### 2. Unit Test for the Polling Task

*   **File**: `tests/test_tasks.py`
*   **Action**:
    *   Write a new test `test_poll_usdc_payment_task`.
    *   Mock the `circle_service.get_payment_intent_status` function to control its return value.
    *   Mock the `handle_successful_payment` function to verify it gets called.
    *   **Scenario 1 (Success)**: Have the mock status function return `pending` a few times, then `complete`. Assert that `handle_successful_payment` is called exactly once with the correct `user_id`.
    *   **Scenario 2 (Timeout)**: Have the mock status function always return `pending`. Assert that `handle_successful_payment` is never called and that the task finishes gracefully.

#### 3. Integration Test (Manual)

*   **Goal**: Perform a full, end-to-end test of the USDC payment flow.
*   **Action**:
    1.  Run the application.
    2.  Initiate a conversation with the bot and proceed to the payment step.
    3.  Select "USDC" as the payment method.
    4.  Use the provided wallet address and send 10 testnet USDC from the [Circle Faucet](https://faucet.circle.com/).
    5.  **Observe**:
        *   The application logs should show the polling task starting.
        *   The logs should show the status being checked every 30 seconds.
        *   After the transaction is confirmed on the Sepolia testnet, the logs should show the status as `complete`.
    6.  **Verify**:
        *   Confirm that the `handle_successful_payment` function is triggered.
        *   Confirm that the PDF ticket is generated and sent to you via Telegram/WhatsApp.
        *   Check that the polling task stops after the successful payment. 