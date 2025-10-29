"""
Database initialization endpoint
Run once: GET /api/init-db
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.db import init_db


def handler(request):
    """Initialize database schema"""
    try:
        init_db()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': '{"success": true, "message": "Database initialized successfully"}'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "{str(e)}"}}'
        }
