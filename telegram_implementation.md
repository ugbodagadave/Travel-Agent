# AI Travel Agent: Telegram Integration Plan

This document outlines the step-by-step plan to integrate Telegram as a new communication channel for the AI Travel Agent, allowing users to book flights by chatting with a Telegram bot. We will follow a test-driven development (TDD) approach.

---

## Phase 0: Project Setup & Bot Creation

### Feature/Build
- Prepare the project for the new integration and create the Telegram bot itself.

### Implementation Steps
1.  **Create Your Bot with BotFather:**
    *   Open Telegram, search for the user `@BotFather`, and start a chat.
    *   Send the `/newbot` command.
    *   Follow the prompts to choose a name and username for your bot.
    *   BotFather will provide you with a unique **Bot Token**. Please save this token.
2.  **Credential Prompt:** I will ask you for your **Telegram Bot Token**. We will add it to your `.env` file as `TELEGRAM_BOT_TOKEN` for local development.
3.  **Install `requests` library:** If not already installed, we'll add `requests` to your `requirements.txt` and install it. This will be used to communicate with the Telegram Bot API. `pip install requests`

---

## Phase 1: Basic Telegram Webhook Endpoint

### Feature/Build
- A new `/telegram-webhook` endpoint in the Flask app to receive incoming updates from Telegram.

### Tests
- Create `tests/test_telegram.py` (or add to `test_app.py`).
- Write a test that simulates a POST request from Telegram to `/telegram-webhook` and asserts a `200 OK` response.

### Implementation Steps
1.  **Create `app/main.py`:**
    *   Define a new route `/telegram-webhook` that accepts `POST` requests.
    *   For now, this route will just receive the request, log it, and return a `200 OK` status to acknowledge receipt. Telegram requires a quick response to its webhooks.

### Testing
- Run `pytest` to ensure the new endpoint is active and responsive.

---

## Phase 2: Sending & Receiving Messages via Telegram API

### Feature/Build
- Parse incoming messages from the Telegram webhook.
- Send a simple, static reply back to the user using the Telegram Bot API.

### Tests
- Mock the `requests.post` method used to call the Telegram API.
- Write a test to ensure `/telegram-webhook` correctly parses the `chat.id` and `text` from a simulated Telegram request body.
- Write a test to assert that the endpoint calls the Telegram `sendMessage` API with the correct `chat_id` and a reply message.

### Implementation Steps
1.  **Create `app/telegram_service.py`:**
    *   This new module will encapsulate all communication with the Telegram Bot API.
    *   Create a function `send_message(chat_id, text)`. This function will construct the API URL (`https://api.telegram.org/bot<TOKEN>/sendMessage`) and send a `POST` request with the `chat_id` and `text` in the body.
2.  **Update `/telegram-webhook`:**
    *   In `app/main.py`, modify the webhook to parse the JSON payload from Telegram. The user's message is at `message.text` and their unique identifier is at `message.chat.id`.
    *   Call the new `telegram_service.send_message` function to send a reply (e.g., "Message received!").

### Testing
- Run `pytest` to verify the request parsing and reply logic.

---

## Phase 3: Refactoring and Core Logic Integration

### Feature/Build
- Connect the Telegram channel to the existing AI, conversation, and session management logic.
- Refactor the core message processing logic to be platform-agnostic.

### Tests
- Write a test to ensure the core processing function correctly calls `load_session`, `get_ai_response`, and `save_session`.
- Update session manager tests to handle Telegram-specific user IDs (e.g., `telegram:12345678`).
- Write an integration test for `/telegram-webhook` that mocks the AI and session services and verifies they are called with the correct data from a Telegram message.

### Implementation Steps
1.  **Refactor Core Logic:**
    *   Create a new central function, e.g., `process_message(user_id, incoming_msg)`, in a file like `app/core_logic.py`.
    *   Move the shared logic from the existing Twilio `/webhook` into this function. This includes loading the session, getting the AI response, handling state transitions, and saving the session.
    *   The function will take a `user_id` and the message `text`, and return the message that should be sent back to the user.
2.  **Update Webhooks:**
    *   Modify both `/webhook` (Twilio) and `/telegram-webhook` to be simple wrappers.
    *   **Telegram Webhook:**
        *   Extract `chat.id` and `text`.
        *   Create a unique `user_id` (e.g., `f"telegram:{chat_id}"`).
        *   Call `process_message(user_id, text)`.
        *   Use `telegram_service.send_message` to send the returned response.
    *   **Twilio Webhook:**
        *   Extract `From` and `Body`.
        *   Use the `From` value as the `user_id`.
        *   Call `process_message(user_id, Body)`.
        *   Format the returned response into TwiML.

### Testing
- Run the full `pytest` suite to ensure the refactoring hasn't broken the existing WhatsApp functionality and that the new Telegram flow works as expected.

---

## Phase 4: Adapting Flight Search and Payment Flow

### Feature/Build
- Ensure that multi-line messages (like flight options) and URLs (like Stripe payment links) are handled correctly for Telegram users.

### Tests
- Write a test for the message formatting logic. Given a list of flight options, assert that it produces a correctly formatted Markdown string for Telegram.
- Test the Stripe payment link generation for a Telegram user, ensuring the `user_id` is correctly passed in the metadata.

### Implementation Steps
1.  **Update Message Formatting:**
    *   The Telegram Bot API supports Markdown for message formatting.
    *   Locate the code that formats the flight options list for the user.
    *   Update it to generate a clean, numbered list using Markdown syntax. This will likely be passed to `telegram_service.send_message` which will need a `parse_mode='MarkdownV2'` parameter.
2.  **Update Payment Initiation:**
    *   The `payment_service.create_checkout_session` already uses the `user_id` in the Stripe metadata.
    *   Since our refactored webhook now creates a `telegram:<chat_id>` user ID, this will work without changes. The payment link will be sent to the user, which is fully supported by Telegram.

### Testing
- Run `pytest`.

---

## Phase 5: Handling Asynchronous Payment Confirmation

### Feature/Build
- Make the `/stripe-webhook` platform-aware, so it can send post-payment messages to users on either WhatsApp or Telegram.

### Tests
- Update the existing test for `/stripe-webhook` in `tests/test_app.py`.
- Create two test cases for a `checkout.session.completed` event:
    1.  One with a `user_id` in the metadata that starts with `whatsapp:`. Assert that the Twilio client is called to send the confirmation.
    2.  One with a `user_id` that starts with `telegram:`. Assert that `telegram_service.send_message` is called.

### Implementation Steps
1.  **Update `/stripe-webhook` in `app/main.py`:**
    *   Inside the handler for the `checkout.session.completed` event, retrieve the `user_id` from the event's metadata.
    *   Add conditional logic:
        *   `if user_id.startswith('whatsapp:'):`
            *   Use the existing Twilio client to send the proactive message asking for traveler details.
        *   `elif user_id.startswith('telegram:'):`
            *   Extract the `chat_id` from the `user_id`.
            *   Call `telegram_service.send_message(chat_id, ...)` to ask for traveler details.

### Testing
- Run `pytest` to ensure the Stripe webhook can notify users on both platforms correctly.

---

## Phase 6: Deployment to Render

### Feature/Build
- Deploy the application with the new Telegram integration to the live Render environment.

### Implementation Steps
1.  **Update `render.yaml`:**
    *   Add `TELEGRAM_BOT_TOKEN` to the list of environment variables under `envVars`.
2.  **Push to GitHub:** Commit all your changes and push them to your main branch on GitHub. This will trigger an automatic deployment on Render.
3.  **Add Environment Variable in Render:**
    *   Go to your service's dashboard on Render.
    *   Navigate to the "Environment" tab.
    *   Add a new secret file or environment variable for `TELEGRAM_BOT_TOKEN` and paste the token you got from BotFather.
4.  **Set the Telegram Webhook:**
    *   Once the deployment is live, you must tell Telegram where to send messages.
    *   Take your application's live URL (e.g., `https://your-app.onrender.com`) and your bot token.
    *   I will provide you with a `curl` command to run from your terminal to set the webhook. It will look like this:
        ```bash
        curl -F "url=https://your-app.onrender.com/telegram-webhook" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
        ```
    *   If successful, Telegram will respond with `{"ok":true,"result":true,"description":"Webhook was set"}`.

### Testing
- Perform a final, end-to-end test by opening Telegram and sending a message to your bot. Go through the entire flow of booking a flight to ensure everything works on the live system. 