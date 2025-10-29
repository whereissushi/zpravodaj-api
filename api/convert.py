"""
Vercel API endpoint for PDF to Flipbook conversion
POST /api/convert
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.pdf_converter import PDFToFlipbook
from lib.s3_uploader import S3Uploader
from lib.db import log_conversion

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
    - title: Title for flipbook
    - account: Account identifier (for organization)
    - upload_to_s3: boolean (default: true)

    Returns:
    - JSON with S3 URLs or ZIP download link
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
        upload_to_s3 = request.form.get('upload_to_s3', 'true').lower() == 'true'

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

        # Upload to S3 or return data
        if upload_to_s3:
            # Get S3 credentials from environment
            s3_bucket = os.getenv('AWS_S3_BUCKET')
            s3_region = os.getenv('AWS_REGION', 'us-east-1')

            if not s3_bucket:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'S3 bucket not configured'})
                }

            # Upload to S3
            uploader = S3Uploader(
                bucket_name=s3_bucket,
                region=s3_region
            )

            # Generate unique folder name (account/title-timestamp)
            import time
            timestamp = int(time.time())
            folder_name = f"{account}/{title.replace(' ', '-').lower()}-{timestamp}"

            s3_urls = uploader.upload_flipbook(result, folder_name)

            # Log to database
            try:
                log_conversion(
                    account=account,
                    title=title,
                    page_count=result['page_count'],
                    s3_url=s3_urls['index_url'],
                    status='success'
                )
            except Exception as db_error:
                print(f"Warning: Failed to log to database: {db_error}")

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'urls': s3_urls,
                    'page_count': result['page_count']
                })
            }
        else:
            # Return as JSON (base64 encoded)
            import base64

            # Encode images as base64
            pages_b64 = [base64.b64encode(img).decode('utf-8') for img in result['pages']]
            thumbs_b64 = [base64.b64encode(img).decode('utf-8') for img in result['thumbs']]

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'html': result['html'],
                    'css': result['css'],
                    'js': result['js'],
                    'pages': pages_b64,
                    'thumbs': thumbs_b64,
                    'page_count': result['page_count']
                })
            }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")

        # Log error to database
        try:
            log_conversion(
                account=account if 'account' in locals() else 'unknown',
                title=title if 'title' in locals() else 'unknown',
                page_count=0,
                s3_url='',
                status='error',
                error_message=str(e)
            )
        except:
            pass

        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }
