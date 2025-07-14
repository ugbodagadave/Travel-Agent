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
        """
        Creates a new wallet with a unique address for a one-time payment.
        Returns the wallet address and ID, or None if an error occurs.
        """
        idempotency_key = self._generate_idempotency_key()
        
        payload = {
            "idempotencyKey": idempotency_key,
            "description": f"Flight Payment Wallet - {idempotency_key}" # Unique description
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/wallets",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status() # Raise an exception for bad status codes
            
            data = response.json().get('data', {})
            wallet_id = data.get('walletId')
            address = data.get('address') # This is the address to send funds to
            
            if wallet_id and address:
                return {"walletId": wallet_id, "address": address}
            else:
                print(f"Error: Wallet ID or Address not found in Circle response. Response: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error creating Circle wallet: {e}")
            if e.response:
                print(f"Response Body: {e.response.text}")
            return None 