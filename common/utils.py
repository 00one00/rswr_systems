"""
Common utility functions used across the application.
"""
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
import os


def convert_heic_to_jpeg(uploaded_file):
    """
    Convert HEIC/HEIF image files to JPEG format for browser compatibility.

    Args:
        uploaded_file: Django UploadedFile object

    Returns:
        InMemoryUploadedFile: Converted JPEG file if input was HEIC/HEIF
        Original file: If input was already a supported format

    This function:
    - Accepts HEIC/HEIF files from iPhones and converts them to JPEG
    - Preserves image quality at 95% for AI training purposes
    - Maintains original filename but changes extension to .jpg
    - Returns original file unchanged if already in JPEG/PNG/WebP format
    """
    if not uploaded_file:
        return None

    # Get file extension
    file_name = uploaded_file.name
    file_ext = os.path.splitext(file_name)[1].lower()

    # Check if file is HEIC/HEIF
    if file_ext not in ['.heic', '.heif']:
        # Not a HEIC file, return original
        return uploaded_file

    try:
        # Open the HEIC image using Pillow (with pillow-heif registered)
        image = Image.open(uploaded_file)

        # Convert to RGB if necessary (HEIC can have different color modes)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Create a BytesIO buffer to hold the JPEG data
        output = BytesIO()

        # Save as JPEG with high quality (95%) for AI training
        image.save(output, format='JPEG', quality=95, optimize=True)
        output.seek(0)

        # Create new filename with .jpg extension
        new_filename = os.path.splitext(file_name)[0] + '.jpg'

        # Create a new InMemoryUploadedFile
        converted_file = InMemoryUploadedFile(
            output,
            'ImageField',
            new_filename,
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )

        return converted_file

    except Exception as e:
        # If conversion fails, log the error and return original file
        # This allows the upload to continue even if conversion fails
        print(f"Warning: Failed to convert HEIC to JPEG: {str(e)}")
        return uploaded_file
