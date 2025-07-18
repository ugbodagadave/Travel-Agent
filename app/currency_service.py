import requests

class CurrencyService:
    def __init__(self):
        self.base_url = "https://api.frankfurter.app"

    def convert_to_usd(self, amount: float, source_currency: str) -> float | None:
        """
        Converts a given amount from a source currency to USD.
        Returns the converted amount or None if the conversion fails.
        """
        source_currency = source_currency.upper()
        
        if source_currency == "USD":
            return amount

        try:
            response = requests.get(f"{self.base_url}/latest?amount={amount}&from={source_currency}&to=USD")
            response.raise_for_status()
            
            data = response.json()
            return data.get("rates", {}).get("USD")

        except requests.exceptions.RequestException as e:
            print(f"Error converting currency: {e}")
            if e.response:
                print(f"Response Body: {e.response.text}")
            return None
        except (KeyError, TypeError):
            print("Error parsing currency conversion response.")
            return None 