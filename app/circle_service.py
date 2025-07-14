import os
import requests
import uuid
import time

class CircleService:
    """
    Service for interacting with the Circle API using the Payment Intents flow.
    """
    def __init__(self):
        self.api_key = os.environ.get("CIRCLE_API_KEY")
        self.base_url = "https://api-sandbox.circle.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_payment_intent(self, usd_amount):
        """
        Creates a new payment intent and polls for the deposit address.
        """
        # Step 1: Create the Payment Intent
        intent_payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "amount": {
                "amount": f"{usd_amount:.2f}",
                "currency": "USD"
            },
            "settlementCurrency": "USD",
            "paymentMethods": [
                {"type": "blockchain", "chain": "ETH"} # Use ETH for Sepolia sandbox
            ]
        }
        
        try:
            intent_response = requests.post(
                f"{self.base_url}/paymentIntents", headers=self.headers, json=intent_payload
            )
            intent_response.raise_for_status()
            intent_data = intent_response.json().get("data", {})
            intent_id = intent_data.get("id")

            if not intent_id:
                print("Failed to create payment intent: ID missing from response.")
                return None

            # Step 2: Poll for the address
            for _ in range(10): # Poll for up to 10 seconds
                time.sleep(1) # Wait 1 second between polls
                address_response = requests.get(
                    f"{self.base_url}/paymentIntents/{intent_id}", headers=self.headers
                )
                address_response.raise_for_status()
                address_data = address_response.json().get("data", {})
                
                payment_method = address_data.get("paymentMethods", [{}])[0]
                address = payment_method.get("address")

                if address:
                    print(f"Successfully retrieved address for intent {intent_id}")
                    # The webhook needs the intent_id to find the user
                    return {"walletId": intent_id, "address": address}
            
            print(f"Polling timed out for intent {intent_id}. Address not found.")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error in Circle payment intent flow: {e}")
            if e.response:
                print(f"Response Body: {e.response.text}")
            return None 