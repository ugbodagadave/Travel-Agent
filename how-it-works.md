# How the AI Travel Agent Works: A Deep Dive

This document provides a detailed, step-by-step explanation of how the entire system works. The application is built on a **single-service architecture** that uses background threading to ensure it is responsive, scalable, and resilient.

### High-Level Architecture

The application is a single, robust **Flask web service**. It's designed to handle all user interactions, from receiving initial messages to sending final confirmations.

To prevent long-running operations (like searching for flights) from blocking the application, these tasks are executed in a **separate background thread**. This ensures the main web service is always available to respond instantly to new user messages.

**Redis** is used as a fast, in-memory database to store each user's conversation state, allowing for seamless, multi-turn dialogues.

This single-service, multi-threaded architecture simplifies deployment and maintenance while preserving a highly responsive user experience.

---

### The Step-by-Step User Journey

Let's walk through the exact sequence of events as a user interacts with the agent.

#### Step 1: The Initial Handshake

1.  **User Sends Message:** A user sends "Hi" to the Telegram Bot.
2.  **Platform Webhook:** Telegram makes an HTTP `POST` request to the public URL of the **Web Service**.
3.  **Application Entry Point (`app/main.py`):** The Flask server receives the request. The `/telegram-webhook` function extracts the user's ID and message and passes them to the central `process_message` function in `app/core_logic.py`.

#### Step 2: Core Logic and State Management

This all happens inside the `process_message` function in `app/core_logic.py`.

1.  **Session Loading (`app/new_session_manager.py`):** The function immediately calls `load_session(user_id)` to fetch the user's conversation state from **Redis**. If the user is new, it creates a new session with the state `GATHERING_INFO`.

2.  **AI Processing (`app/ai_service.py`):** Based on the current state, `get_ai_response` is called. It sends the conversation history to the **IO Intelligence API**, which asks clarifying questions until it has all the details (origin, destination, date, etc.). When complete, the AI returns the special tag `[INFO_COMPLETE]`.

3.  **State Transition & Session Saving:** The web service sees the `[INFO_COMPLETE]` tag, transitions the user's state to `AWAITING_CONFIRMATION`, and saves the updated session back to **Redis**. The confirmation summary is sent back to the user as an immediate HTTP response.

#### Step 3: The Asynchronous Handoff (The Background Thread)

This is the most critical part of the architecture.

1.  **User Confirms:** The user replies "Yes". The web service receives this message.
2.  **Task Dispatching (`app/core_logic.py`):**
    *   The `process_message` function loads the session and sees the state is `AWAITING_CONFIRMATION`.
    *   It immediately sends the user the message "Okay, I'm searching for the best flights..."
    *   Crucially, it **does not** search for flights in the main request thread. Instead, it starts a new background thread using Python's built-in `threading` module to run the `search_flights_task` function.
    *   The web service's job is now complete for this request, and it returns an immediate `200 OK` response to Telegram.

#### Step 4: Background Flight Search

1.  **Independent Execution (`app/tasks.py`):**
    *   Meanwhile, the `search_flights_task` function runs independently in its own thread.
2.  **Execution:** The task's code executes:
    *   It calls the Amadeus API to get IATA codes.
    *   It calls the Amadeus API again to perform the live flight search. This can take several seconds without affecting the main application.
3.  **Proactive Response:**
    *   Once the search is complete, the background thread formats the flight offers into a user-friendly list.
    *   It then connects directly to the Telegram API and sends the results as a **new, proactive message** to the user.
4.  **Final State Update:** The thread updates the user's state in Redis to `FLIGHT_SELECTION` and saves the flight offers to their session.

#### Step 5: Payment and Final Booking

The rest of the flow follows a similar pattern. The web service handles the direct user interactions (like choosing a flight), and after payment is confirmed via a Stripe webhook, it triggers the final booking logic. Any long-running notifications could also be handled in background threads.

### Technology Stack Summary

*   **Web Service:** **Flask**, **Gunicorn**.
*   **Background Tasks:** Python's built-in **`threading`** module.
*   **Messaging Platforms:** **Twilio** for WhatsApp, **Telegram Bot API** for Telegram.
*   **Natural Language Understanding:** **IO Intelligence API**.
*   **Flight Data & Booking:** **Amadeus**.
*   **Payments:** **Stripe**.
*   **Session Storage:** **Redis** is the backbone of the system, used for storing conversation state.
*   **Testing:** **Pytest**.
*   **Hosting:** **Render**. 