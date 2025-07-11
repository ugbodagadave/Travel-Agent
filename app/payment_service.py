import os
import stripe

# Initialize the Stripe API client
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(flight_offer: dict, user_id: str) -> str | None:
    """
    Creates a Stripe Checkout session for a given flight offer.

    :param flight_offer: The flight offer object from Amadeus.
    :param user_id: The unique identifier for the user.
    :return: The URL of the checkout session, or None if an error occurs.
    """
    try:
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:5000")
        success_url = f"{base_url}/payment-success"
        cancel_url = f"{base_url}/"

        # Extract necessary details from the flight offer
        price_details = flight_offer.get('price', {})
        total_price = float(price_details.get('total', 0))
        currency = price_details.get('currency', 'USD').lower()
        
        # Convert the price to the smallest currency unit (e.g., cents)
        amount_in_cents = int(total_price * 100)

        # Create a product and price for the checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f"Flight Booking for {user_id}",
                        'description': f"One-way flight to {flight_offer['itineraries'][0]['segments'][-1]['arrival']['iataCode']}"
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id  # Pass the user_id to the webhook
        )
        return session.url
    except Exception as e:
        print(f"Error creating Stripe checkout session: {e}")
        return None 