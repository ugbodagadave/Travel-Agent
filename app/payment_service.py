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
            success_url='https://example.com/success?session_id={CHECKOUT_SESSION_ID}', # Temporary URL
            cancel_url='https://example.com/cancel', # Temporary URL
            # Store our internal identifiers in the metadata
            metadata={
                'user_id': user_id,
                # Storing the entire flight offer might exceed metadata limits.
                # For now, we'll rely on retrieving it from the user's session state
                # based on the user_id when the webhook is called.
            }
        )
        return session.url
    except Exception as e:
        print(f"Error creating Stripe checkout session: {e}")
        return None 