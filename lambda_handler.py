"""
AWS Lambda Handler for PDF to Flipbook Converter
Handles PDF uploads and returns flipbook ZIP
"""

import json
import base64
import io
import zipfile
from lib.pdf_converter import PDFToFlipbook


def lambda_handler(event, context):
    """
    Lambda entry point

    Expected event format:
    {
        "body": "<base64-encoded-pdf>",
        "isBase64Encoded": true,
        "queryStringParameters": {
            "title": "Zpravodaj název"
        }
    }
    """

    try:
        # Parse input
        if event.get('isBase64Encoded'):
            pdf_bytes = base64.b64decode(event['body'])
        else:
            # For testing with binary data
            pdf_bytes = event['body']

        # Get title from query params
        params = event.get('queryStringParameters') or {}
        title = params.get('title', 'Zpravodaj')

        print(f"Processing PDF: {title}, size: {len(pdf_bytes)} bytes")

        # Convert PDF to flipbook
        converter = PDFToFlipbook(pdf_bytes, title)
        result = converter.convert()

        print(f"Conversion complete: {result['page_count']} pages")

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

            # Add search data
            zip_file.writestr('search_data.json', result['search_data'])

        # Get ZIP bytes
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        # Return as base64-encoded response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/zip',
                'Content-Disposition': f'attachment; filename="{title}-flipbook.zip"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': base64.b64encode(zip_bytes).decode('utf-8'),
            'isBase64Encoded': True
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }
