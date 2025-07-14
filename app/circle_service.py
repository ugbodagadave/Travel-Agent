import os
import requests
import uuid

class CircleService:
    def __init__(self):
        self.api_key = os.getenv("CIRCLE_API_KEY")
        self.base_url = "https://api-sandbox.circle.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _generate_idempotency_key(self):
        """Generates a unique idempotency key for each request."""
        return str(uuid.uuid4())

    def create_payment_wallet(self):
        """Creates a new wallet for a single payment."""
        # This is a simplified wallet creation for a specific use case.
        # In a real-world scenario, you might have more robust logic.
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "description": "Flight Payment Wallet"
        }
        try:
            response = requests.post(
                f"{self.base_url}/wallets", headers=self.headers, json=payload
            )
            response.raise_for_status()
            wallet_data = response.json().get("data", {})
            wallet_id = wallet_data.get("walletId")

            if wallet_id:
                # Second call to generate a deposit address for the new wallet
                address_payload = {
                    "idempotencyKey": str(uuid.uuid4()),
                    "currency": "USD",
                    "chain": "ETH-SEPOLIA"
                }
                address_response = requests.post(
                    f"{self.base_url}/wallets/{wallet_id}/addresses", 
                    headers=self.headers,
                    json=address_payload
                )
                address_response.raise_for_status()
                address_data = address_response.json().get("data", {})
                
                if address_data and "address" in address_data:
                    address = address_data.get("address")
                    return {"walletId": wallet_id, "address": address}

            print(f"Error: Wallet ID or Address not found in Circle response. Response: {response.json()}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error creating Circle wallet: {e}")
            if e.response:
                print(f"Response Body: {e.response.text}")
            return None 