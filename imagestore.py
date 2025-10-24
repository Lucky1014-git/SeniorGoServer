import base64
import os
import tempfile
from unittest import result
import cloudinary
import cloudinary.uploader
from flask import jsonify

# Configure Cloudinary (you'll need to set these environment variables or replace with your actual values)
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dmvm23swd'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', '247638584697619'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'j9qSejepi0lcjT1JEv4-OpvM7jg')
)


def upload_profile_photo(image_base64):
    try:

        if image_base64.startswith("data:image"):
            image_base64 = image_base64.split(",")[1]
        # Convert Base64 to bytes
        image_bytes = base64.b64decode(image_base64)

        # Save to temporary file or upload directly
        with open("temp_image.jpg", "wb") as f:
            f.write(image_bytes)

        # Upload to Cloudinary
        result = cloudinary.uploader.upload("temp_image.jpg")
        # Clean up temporary file
        if os.path.exists("temp_image.jpg"):
            os.remove("temp_image.jpg")
        
        # Return the secure URL
        return result['secure_url']

    except Exception as e:
        print(f"Error in upload_profile_photo: {e}")
        return jsonify({"message": f"Failed to upload profile photo: {str(e)}"}), 500




