# AI Travel Agent

This project is an AI-powered travel agent that can be used via WhatsApp to book flights.

## Current Progress

So far, we have completed the initial project setup, created a basic web server, integrated the core AI and messaging services, and added session persistence.

### Phase 0: Project Setup
- Initialized a Git repository.
- Created a Python virtual environment (`venv`).
- Set up the project structure with `app` and `tests` directories.
- Installed `pytest` for testing.
- Created a `.gitignore` file.

### Phase 1: Basic Web Server
- Installed Flask.
- Created a basic Flask application in `app/main.py`.
- Implemented a `/webhook` endpoint.
- Wrote and passed a unit test to verify the webhook.

### Phase 2: Twilio Integration
- Installed the `twilio` library.
- Configured the webhook to receive and parse WhatsApp messages.
- Implemented logic to send a TwiML response.
- Wrote and passed a unit test to verify the Twilio integration.

### Phase 3: IO Intelligence Integration
- Installed the `openai` library to use with the IO Intelligence API.
- Created a dedicated `app/ai_service.py` module to handle API calls.
- Integrated the AI service with the webhook to generate dynamic responses.
- Wrote and passed a unit test using a mock to verify the AI service integration.

### Phase 4: Conversation Logic and Slot-Filling
- Implemented a system prompt to guide the AI agent in collecting flight details (origin, destination, dates, etc.).
- Wrote and passed unit tests for multi-turn conversations, ensuring the agent asks clarifying questions and correctly identifies when all slots are filled.

### Phase 5: Session Persistence with Redis
- Installed the `redis` library.
- Set up a free Redis instance on Render.
- Created a `session_manager.py` to handle loading and saving conversation history.
- Integrated the session manager into the main webhook, enabling stateful, multi-turn conversations.
- Wrote and passed a comprehensive end-to-end test to verify the entire conversation flow with session management.

## Next Steps

The next phase is to handle timezones correctly to ensure flight searches are accurate. After that, we will integrate a real flight search API. 