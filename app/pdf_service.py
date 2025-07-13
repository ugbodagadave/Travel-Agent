from fpdf import FPDF
from fpdf.enums import XPos, YPos

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
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(200, 10, "Your Flight Itinerary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    # Basic flight details
    pdf.set_font("Helvetica", '', 12)
    
    if flight_offer:
        price = flight_offer['price']['total']
        currency = flight_offer['price']['currency']
        travel_class = "ECONOMY" # Default
        try:
            travel_class = flight_offer.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0].get('cabin', 'ECONOMY').replace('_', ' ').title()
        except (IndexError, KeyError):
            pass # Keep the default

        pdf.cell(200, 10, f"Total Price: {price} {currency}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(200, 10, f"Class: {travel_class}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        for i, itinerary in enumerate(flight_offer['itineraries']):
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(200, 10, f"Trip {i+1}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", '', 12)
            
            for j, segment in enumerate(itinerary['segments']):
                departure = segment['departure']
                arrival = segment['arrival']
                
                pdf.cell(200, 10, f"  Segment {j+1}:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(200, 10, f"    From: {departure['iataCode']} at {departure['at']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(200, 10, f"    To: {arrival['iataCode']} at {arrival['at']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)

    else:
        pdf.cell(200, 10, "No flight details available.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Return the PDF as a byte string
    return bytes(pdf.output()) 