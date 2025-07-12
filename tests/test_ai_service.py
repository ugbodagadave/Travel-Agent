
import pytest
from unittest.mock import patch, MagicMock
from app.ai_service import get_ai_response, SYSTEM_PROMPT_GATHER_INFO, SYSTEM_PROMPT_CONFIRMATION

@patch("app.ai_service.client")
def test_get_ai_response_uses_gather_info_prompt_for_new_conversation(mock_openai_client):
    """
    Tests that the correct system prompt is used for the initial state.
    """
    # Mock the API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello! How may I help you?"
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Call the function
    user_message = "hi"
    conversation_history = []
    state = "GATHERING_INFO"
    _, updated_history = get_ai_response(user_message, conversation_history, state)

    # Assert that the system prompt was set correctly
    assert updated_history[0]["role"] == "system"
    assert updated_history[0]["content"] == SYSTEM_PROMPT_GATHER_INFO

@patch("app.ai_service.client")
def test_get_ai_response_uses_confirmation_prompt_for_confirmation_state(mock_openai_client):
    """
    Tests that the system prompt is switched for the AWAITING_CONFIRMATION state.
    """
    # Mock the API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "[CONFIRMED]"
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Call the function
    user_message = "yep"
    # Start with a history that already has the GATHER_INFO prompt
    conversation_history = [{"role": "system", "content": SYSTEM_PROMPT_GATHER_INFO}]
    state = "AWAITING_CONFIRMATION"
    _, updated_history = get_ai_response(user_message, conversation_history, state)

    # Assert that the NEW system prompt was added correctly
    # It should be right before the user's message
    system_prompts = [msg for msg in updated_history if msg['role'] == 'system']
    assert len(system_prompts) > 0
    assert system_prompts[-1]['content'] == SYSTEM_PROMPT_CONFIRMATION

@patch("app.ai_service.client")
def test_get_ai_response_on_topic_request(mock_openai_client):
    """
    Tests that a standard, on-topic travel request gets a valid response
    and that the `max_tokens` parameter is passed.
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Great! What is your destination?"
    mock_openai_client.chat.completions.create.return_value = mock_response

    user_message = "I want to fly to Paris"
    _, history = get_ai_response(user_message, [], "GATHERING_INFO")

    # Assert that the API was called with the correct parameters
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args, call_kwargs = mock_openai_client.chat.completions.create.call_args
    assert call_kwargs['max_tokens'] == 150
    
    # Assert that the response is as expected
    assert history[-1]['content'] == "Great! What is your destination?"

@patch("app.ai_service.client")
def test_get_ai_response_off_topic_request(mock_openai_client):
    """
    Tests that a non-travel-related request is declined with the specific message.
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Sorry, I can't help you with that."
    mock_openai_client.chat.completions.create.return_value = mock_response

    user_message = "What's the capital of Nebraska?"
    response_text, _ = get_ai_response(user_message, [], "GATHERING_INFO")

    # Assert that the API was called (to get the decline response)
    mock_openai_client.chat.completions.create.assert_called_once()
    
    # Assert that the response is the exact decline message
    assert response_text == "Sorry, I can't help you with that." 