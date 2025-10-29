"""
Neon PostgreSQL database connection and logging
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


def get_db_connection():
    """
    Get Neon PostgreSQL connection

    Returns:
        psycopg2 connection
    """
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")

    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def init_db():
    """
    Initialize database schema (run once on first deployment)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Create conversions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS conversions (
            id SERIAL PRIMARY KEY,
            account VARCHAR(255) NOT NULL,
            title VARCHAR(500) NOT NULL,
            page_count INTEGER NOT NULL,
            s3_url TEXT,
            status VARCHAR(50) NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index on account for faster queries
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversions_account
        ON conversions(account)
    ''')

    # Create index on created_at for sorting
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversions_created_at
        ON conversions(created_at DESC)
    ''')

    conn.commit()
    cur.close()
    conn.close()


def log_conversion(account, title, page_count, s3_url, status='success', error_message=None):
    """
    Log conversion to database

    Args:
        account: Account identifier
        title: Flipbook title
        page_count: Number of pages
        s3_url: S3 URL to index.html
        status: 'success' or 'error'
        error_message: Error message if status is 'error'

    Returns:
        Conversion ID
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO conversions (account, title, page_count, s3_url, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (account, title, page_count, s3_url, status, error_message))

    conversion_id = cur.fetchone()['id']

    conn.commit()
    cur.close()
    conn.close()

    return conversion_id


def get_conversions(account=None, limit=100):
    """
    Get conversion history

    Args:
        account: Filter by account (optional)
        limit: Max number of results

    Returns:
        List of conversion records
    """
    conn = get_db_connection()
    cur = conn.cursor()

    if account:
        cur.execute('''
            SELECT * FROM conversions
            WHERE account = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (account, limit))
    else:
        cur.execute('''
            SELECT * FROM conversions
            ORDER BY created_at DESC
            LIMIT %s
        ''', (limit,))

    conversions = cur.fetchall()

    cur.close()
    conn.close()

    return conversions


def get_conversion_stats(account=None):
    """
    Get conversion statistics

    Args:
        account: Filter by account (optional)

    Returns:
        Dict with stats (total, success, errors, total_pages)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    if account:
        cur.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                SUM(page_count) as total_pages
            FROM conversions
            WHERE account = %s
        ''', (account,))
    else:
        cur.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                SUM(page_count) as total_pages
            FROM conversions
        ''')

    stats = cur.fetchone()

    cur.close()
    conn.close()

    return stats
