"""
S3 Uploader for flipbook assets
"""

import boto3
from botocore.exceptions import ClientError


class S3Uploader:
    def __init__(self, bucket_name, region='us-east-1'):
        """
        Initialize S3 uploader

        Args:
            bucket_name: S3 bucket name
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)

    def upload_flipbook(self, flipbook_data, folder_name):
        """
        Upload complete flipbook to S3

        Args:
            flipbook_data: Dict from PDFToFlipbook.convert()
            folder_name: Base folder path (e.g., "account/zpravodaj-123")

        Returns:
            Dict with URLs to uploaded files
        """
        base_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{folder_name}"

        try:
            # Upload HTML
            self._upload_file(
                f"{folder_name}/index.html",
                flipbook_data['html'].encode('utf-8'),
                'text/html'
            )

            # Upload CSS
            self._upload_file(
                f"{folder_name}/css/style.css",
                flipbook_data['css'].encode('utf-8'),
                'text/css'
            )

            # Upload JS
            self._upload_file(
                f"{folder_name}/js/flipbook.js",
                flipbook_data['js'].encode('utf-8'),
                'application/javascript'
            )

            # Upload page images
            page_urls = []
            for i, page_bytes in enumerate(flipbook_data['pages'], start=1):
                key = f"{folder_name}/files/pages/{i}.jpg"
                self._upload_file(key, page_bytes, 'image/jpeg')
                page_urls.append(f"{base_url}/files/pages/{i}.jpg")

            # Upload thumbnails
            thumb_urls = []
            for i, thumb_bytes in enumerate(flipbook_data['thumbs'], start=1):
                key = f"{folder_name}/files/thumb/{i}.jpg"
                self._upload_file(key, thumb_bytes, 'image/jpeg')
                thumb_urls.append(f"{base_url}/files/thumb/{i}.jpg")

            return {
                'index_url': f"{base_url}/index.html",
                'css_url': f"{base_url}/css/style.css",
                'js_url': f"{base_url}/js/flipbook.js",
                'pages': page_urls,
                'thumbs': thumb_urls,
                'base_url': base_url
            }

        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")

    def _upload_file(self, key, data, content_type):
        """
        Upload single file to S3

        Args:
            key: S3 object key
            data: File content (bytes)
            content_type: MIME type
        """
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            ACL='public-read'  # Make files publicly accessible
        )
