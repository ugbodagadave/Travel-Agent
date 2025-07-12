# Plan to Add Airline Names to Flight Options

This document outlines the step-by-step process to add full airline names to the flight options presented to the user.

## 1. Objective

Enhance the user experience by displaying the full airline name (e.g., "American Airlines") instead of just the IATA code for each flight option. This provides more clarity and a more professional feel to the agent's responses.

## 2. Current Workflow Analysis

- The `search_flights_task` in `app/tasks.py` initiates the flight search by calling `amadeus_service.search_flights`.
- The `AmadeusService` in `app/amadeus_service.py` returns a list of raw flight offer objects from the Amadeus API.
- These raw offers are passed to the `_format_flight_offers` function in `app/utils.py`.
- This utility function formats the flight details into a user-friendly string but currently lacks the airline name.

## 3. Feasibility and API Details

- The Amadeus Flight Offers Search API response contains a `carrierCode` for each flight segment. This is the IATA code for the airline.
- The Amadeus SDK provides an endpoint to resolve these codes: `amadeus.reference_data.airlines.get(airlineCodes='UA')`.
- This confirms the feasibility of the feature. We will receive the code and look up the name.

## 4. Proposed Implementation Plan

### Part 1: Enhance `AmadeusService` to Fetch Airline Names

- **Location**: `app/amadeus_service.py`
- **Action**: Create a new method `get_airline_names(self, airline_codes: list) -> dict`.
- **Details**:
    - This method will accept a list of unique airline IATA codes (e.g., `['AA', 'BA', 'EK']`).
    - It will call the `self.amadeus.reference_data.airlines.get()` endpoint, passing the codes as a comma-separated string.
    - To optimize performance and reduce costs, a new in-memory cache, `self.airline_cache = {}`, will be implemented within the service, mirroring the existing `self.airport_cache`.
    - The method will handle potential API errors gracefully.
    - It will return a dictionary mapping codes to full names (e.g., `{'AA': 'American Airlines', 'BA': 'British Airways'}`).

### Part 2: Integrate Airline Name Retrieval into the Flight Search Task

- **Location**: `app/tasks.py`
- **Action**: Modify the `search_flights_task` function.
- **Details**:
    - After a successful flight search returns `offers`, iterate through them.
    - Collect all unique `carrierCode` values from the `itineraries` -> `segments` of each offer.
    - Call the new `amadeus_service.get_airline_names()` method with the list of unique codes.
    - Augment the `offers` data structure by adding a new key, `airlineName`, to each flight offer's top-level or itinerary level. This will make it easily accessible in the formatting step.

### Part 3: Update the User-Facing Message Format

- **Location**: `app/utils.py`
- **Action**: Modify the `_format_flight_offers` function.
- **Details**:
    - The function will be updated to access the `airlineName` from the augmented flight offer object.
    - The formatted string for each flight option will now prominently feature the airline name.
    - **Example New Format**: `"*1. British Airways: London (LHR) to Paris (CDG) for 250.00 EUR.*"`

## 5. Comprehensive Testing Strategy

### Phase 1: Unit Testing

- **File**: `tests/test_amadeus_service.py`
- **Test Case**: `test_get_airline_names`
- **Assertions**:
    - Mock the `amadeus.reference_data.airlines.get` call.
    - Verify the method correctly calls the Amadeus API with a comma-separated list of codes.
    - Assert that it correctly parses the response and returns the expected dictionary mapping.
    - Test the caching logic: ensure the Amadeus API is called only once when the method is invoked multiple times with the same codes.

### Phase 2: Integration Testing

- **File**: `tests/test_tasks.py`
- **Test Case**: Update `test_search_flights_task_...` tests.
- **Assertions**:
    - When mocking the `AmadeusService`, also mock the return value of the new `get_airline_names` method.
    - Check the arguments passed to the message sending functions (`mock_send_telegram` or `mock_twilio.messages.create`).
    - Assert that the final message body (`body` or `text`) contains the expected airline name (e.g., "American Airlines") and not just the code.

### Phase 3: Manual Verification (Optional but Recommended)

- **File**: `tests/live_amadeus_search.py`
- **Action**: Temporarily modify this script to print the raw JSON of the flight offers returned by a live search.
- **Purpose**: This will allow for manual inspection of the data structure to confirm the exact location of `carrierCode` and validate assumptions before extensive coding.

## 6. Conclusion

The implementation was completed successfully according to the plan. The feature was delivered, tested, and all related documentation has been updated. The temporary end-to-end test script was removed after verification. 