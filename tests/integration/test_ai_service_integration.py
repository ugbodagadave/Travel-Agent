import pytest
import os
from dotenv import load_dotenv
from app.ai_service import extract_traveler_details

# Load environment variables from .env file
load_dotenv()

# This is to forcefully load the IO_API_KEY for the test environment
# as it seems to be missing otherwise.
os.environ['IO_API_KEY'] = os.getenv('IO_API_KEY')


@pytest.mark.integration
def test_extract_traveler_details_integration():
    """
    Integration test for the extract_traveler_details function.
    This test calls the io.net API.
    """
    # Arrange
    message = "Hi, I'd like to book a flight for John Doe, born on 1990-01-01."
    expected_details = {
        "fullName": "John Doe",
        "dateOfBirth": "1990-01-01"
    }

    # Act
    extracted_details = extract_traveler_details(message)

    # Assert
    assert extracted_details is not None
    assert extracted_details == expected_details 