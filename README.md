# AI Travel Agent

This project is an AI-powered travel agent that can be used via WhatsApp to book flights.

## Current Progress

So far, we have completed the initial project setup, created a basic web server, and integrated the core AI and messaging services.

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

## Next Steps

The next phase is to implement more advanced conversation logic and slot-filling to extract structured data (like destinations and dates) from user messages. 