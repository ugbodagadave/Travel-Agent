# Circle USDC Integration Guide

This document explains how we've implemented USDC payments using Circle's Payment Intents API in our Travel Agent application. I'll walk you through the entire architecture, components, and flow so you understand exactly how users can pay for flights using USDC stablecoin.

## Project Structure and Core Components

We've organized the USDC payment integration across several key files:

- **`app/circle_service.py`** - This provides our direct interface to Circle's API
- **`app/payment_service.py`** - This routes payment requests and orchestrates different payment methods
- **`app/tasks.py`** - This contains background tasks for monitoring payment status
- **`app/main.py`** - This handles webhook notifications and orchestrates the final payment steps
- **`app/new_session_manager.py`** - This maintains state and maps payment intents to user sessions

## Architecture Overview

I've designed the USDC payment architecture to be event-driven, combining API calls, background polling, and webhook notifications. Here's how it works:

When a user selects USDC as their payment method, we create a payment intent via Circle's API, which returns a unique deposit address. We then instruct the user to send USDC to this address. The system initiates a background task to poll Circle's API for payment status. Once we confirm payment completion (either via polling or webhook), we trigger the generation and delivery of flight tickets.

## Detailed Implementation Flow

### 1. Payment Method Selection

When a user chooses USDC payment, we trigger this sequence in our core logic:

### 2. Circle Service Integration

The `CircleService` class manages all interactions with Circle's API. Here's what happens:

1. **Create Payment Intent**: We call `create_payment_intent()` method, sending a POST request to Circle's API with the amount in USD and specifying the blockchain payment method (ETH for the Sepolia sandbox)

2. **Retrieve Deposit Address**: We poll Circle's API to get the deposit address associated with the payment intent

3. **Provide Address to User**: Once we obtain the address, we send it to the user along with the exact amount of USDC to send

4. **Map Payment Intent**: We map the `paymentIntentId` to the `user_id` in Redis using the `save_wallet_mapping` function to enable webhook correlation

### 3. Background Payment Monitoring

I've implemented the `poll_usdc_payment_task` function in `app/tasks.py` that runs in a background thread. Here's how it works:

- It periodically calls `get_payment_intent_status` to check the payment status
- The polling continues until the status becomes 'complete' or we reach the timeout (default 1 hour)
- This provides redundancy in case webhooks fail

### 4. Webhook Processing

We handle Circle webhook notifications through the `/circle-webhook` endpoint:

```python
@app.route("/circle-webhook", methods=['POST'])
def circle_webhook():
    data = request.get_json(silent=True)
    notification = data.get('notification')
    if notification and notification.get('type') == 'payments' and notification.get('payment', {}).get('status') == 'complete':
        payment_intent_id = notification.get('payment').get('paymentIntentId')
        user_id = load_user_id_from_wallet(payment_intent_id)
        handle_successful_payment(user_id)
    return 'OK', 200
```

When we receive a `circle-webhook` notification with a 'complete' status, we:
1. Extract the payment intent ID from the webhook
2. Use `load_user_id_from_wallet` to retrieve the corresponding `user_id`
3. Call `handle_successful_payment` to complete the booking process

## Complete Transaction Flow Diagram

## Payment States and Error Handling

We handle several payment states throughout the process:

- **Pending**: Payment intent created, waiting for user to send USDC
- **Processing**: USDC transaction detected on blockchain, waiting for confirmation
- **Complete**: Payment confirmed, tickets generated
- **Failed**: Payment timeout or blockchain transaction failed
- **Cancelled**: User cancelled the payment process

## Key Features and Benefits

### Redundant Payment Confirmation
We implement both webhook notifications and background polling to ensure we never miss a payment confirmation, even if one method fails.

### Secure Session Management
We securely map payment intents to user sessions using Redis, ensuring we can always correlate payments back to the correct booking.

### Real-time Status Updates
Users receive immediate feedback about their payment status through our messaging platforms (WhatsApp/Telegram).

### Blockchain Agnostic
While we currently use Ethereum Sepolia testnet, the architecture supports multiple blockchains supported by Circle.

## Technical Implementation Details

### API Authentication
We authenticate with Circle's API using API keys stored securely in environment variables.

### Error Handling
We implement comprehensive error handling for:
- API failures
- Network timeouts
- Invalid payment amounts
- Blockchain transaction failures

### Timeout Management
Payment intents automatically timeout after 1 hour to prevent indefinite waiting and resource consumption.

### Session Persistence
We store all payment-related data in Redis with appropriate expiration times to maintain system performance.

## Integration with Other Payment Methods

The USDC integration seamlessly works alongside our other payment methods:
- Stripe (credit/debit cards)
- Circle Layer (CLAYER native tokens)

Users can choose their preferred payment method, and we handle the routing automatically through our `payment_service.py` orchestration layer.

## Security Considerations

We've implemented several security measures:

1. **Webhook Validation**: We validate incoming webhooks to ensure they're from Circle
2. **Secure Storage**: API keys and sensitive data are stored securely
3. **Session Isolation**: Each user's payment session is isolated and secure
4. **Timeout Protection**: Automatic cleanup of expired payment intents

## Monitoring and Debugging

We've built comprehensive logging throughout the payment flow:
- Payment intent creation and status changes
- Webhook reception and processing
- Background task execution
- Error conditions and recovery attempts

This logging helps us quickly diagnose and resolve any payment issues.

## Conclusion

The Circle USDC integration provides a robust and secure payment option for users of our AI Travel Agent system. The implementation follows best practices for blockchain payment processing, with comprehensive error handling, secure session management, and reliable transaction monitoring. 

The system successfully integrates with Circle's Payment Intents API to facilitate USDC payments while maintaining compatibility with existing payment methods and application workflows. The addition of redundant confirmation methods (webhooks + polling) ensures reliable payment processing even in edge cases.

This architecture effectively separates concerns, with clear responsibilities for API interaction, session management, and background processing, making it a reliable and maintainable component of our Travel Agent application.