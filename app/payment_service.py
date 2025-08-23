import os
import stripe

# Initialize the Stripe API client
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(flight_offer, user_id):
    """
    Creates a Stripe Checkout session for a given flight offer.
    """
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': flight_offer['price']['currency'],
                        'product_data': {
                            'name': f"Flight to {flight_offer['itineraries'][0]['segments'][0]['arrival']['iataCode']}",
                        },
                        'unit_amount': int(float(flight_offer['price']['total']) * 100),
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=f"{base_url}/payment-success",
            cancel_url=f"{base_url}/payment-cancelled",
            client_reference_id=user_id
        )
        return checkout_session.url
    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        return None 