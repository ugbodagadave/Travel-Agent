import os
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
import requests

def setup_cloudinary():
    """
    Configures the Cloudinary client using environment variables.
    Should be called once at application startup.
    """
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
        api_key=os.environ.get("CLOUDINARY_API_KEY"),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        secure=True  # Ensure URLs are HTTPS
    )

def upload_pdf(pdf_bytes, filename):
    """
    Uploads PDF bytes to Cloudinary and returns the public URL.
    Returns None if the upload fails.
    """
    try:
        print(f"Uploading {filename} to Cloudinary...")
        
        # We use 'raw' for non-image files like PDFs and specify a public_id
        upload_result = cloudinary.uploader.upload(
            pdf_bytes,
            resource_type="raw",
            public_id=filename,
            folder="flight_tickets/"  # Optional: to keep files organized
        )
        
        # The secure_url is the HTTPS URL for the uploaded file
        media_url = upload_result.get('secure_url')

        if not media_url:
            print("ERROR: Cloudinary upload failed, secure_url not found in response.")
            return None

        print(f"Successfully uploaded to Cloudinary. URL: {media_url}")
        return media_url

    except CloudinaryError as e:
        print(f"ERROR: A Cloudinary error occurred during upload: {e}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during Cloudinary upload: {e}")
        return None 