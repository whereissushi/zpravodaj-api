"""
Vercel API endpoint for PDF to Flipbook conversion
POST /api/convert
"""

import json
import sys
import os
import io
import zipfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.pdf_converter import PDFToFlipbook

# For local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def handler(request):
    """
    Vercel serverless function handler

    Expected request body (multipart/form-data):
    - pdf: PDF file
    - title: Title for flipbook (optional)
    - account: Account identifier (optional)

    Returns:
    - ZIP file with complete flipbook
    """
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }

    try:
        # Parse multipart form data
        content_type = request.headers.get('content-type', '')

        if 'multipart/form-data' not in content_type:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Content-Type must be multipart/form-data'})
            }

        # Get form data
        pdf_file = request.files.get('pdf')
        title = request.form.get('title', 'Zpravodaj')
        account = request.form.get('account', 'default')

        if not pdf_file:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'PDF file is required'})
            }

        # Read PDF bytes
        pdf_bytes = pdf_file.read()

        # Convert PDF to flipbook
        converter = PDFToFlipbook(pdf_bytes, title)
        result = converter.convert()

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add HTML
            zip_file.writestr('index.html', result['html'])

            # Add CSS
            zip_file.writestr('css/style.css', result['css'])

            # Add JS
            zip_file.writestr('js/flipbook.js', result['js'])

            # Add page images
            for i, page_bytes in enumerate(result['pages'], start=1):
                zip_file.writestr(f'files/pages/{i}.jpg', page_bytes)

            # Add thumbnails
            for i, thumb_bytes in enumerate(result['thumbs'], start=1):
                zip_file.writestr(f'files/thumb/{i}.jpg', thumb_bytes)

        # Get ZIP bytes
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        # Generate filename
        safe_title = title.replace(' ', '-').replace('/', '-').lower()
        filename = f"{safe_title}-flipbook.zip"

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/zip',
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(zip_bytes))
            },
            'body': zip_bytes,
            'isBase64Encoded': False
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")

        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }
