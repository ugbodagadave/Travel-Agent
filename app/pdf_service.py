from fpdf import FPDF

def create_flight_itinerary(flight_offer):
    """
    Generates a simple flight itinerary PDF from a flight offer.
    
    Args:
        flight_offer (dict): A dictionary containing the flight offer details.

    Returns:
        bytes: The raw bytes of the generated PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Set title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Your Flight Itinerary", ln=True, align='C')
    pdf.ln(10)

    # Basic flight details
    pdf.set_font("Arial", '', 12)
    
    if flight_offer:
        price = flight_offer['price']['total']
        currency = flight_offer['price']['currency']
        
        pdf.cell(200, 10, f"Total Price: {price} {currency}", ln=True)
        
        for i, itinerary in enumerate(flight_offer['itineraries']):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, f"Trip {i+1}", ln=True)
            pdf.set_font("Arial", '', 12)
            
            for j, segment in enumerate(itinerary['segments']):
                departure = segment['departure']
                arrival = segment['arrival']
                
                pdf.cell(200, 10, f"  Segment {j+1}:", ln=True)
                pdf.cell(200, 10, f"    From: {departure['iataCode']} at {departure['at']}", ln=True)
                pdf.cell(200, 10, f"    To: {arrival['iataCode']} at {arrival['at']}", ln=True)
                pdf.ln(5)

    else:
        pdf.cell(200, 10, "No flight details available.", ln=True)

    # Return the PDF as a byte string
    return bytes(pdf.output()) 