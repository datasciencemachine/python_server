from database_setup import *
import os
import io
import uuid
import requests
from PIL import Image
from psycopg2 import Binary  # For storing binary data in PostgreSQL

def insert_job_request(request_id):
    """
    Insert a new job request into the job_request table with pending status.
    
    Args:
        request_id (str): Unique identifier for the job request
    
    Returns:
        bool: True if insertion successful, False otherwise
    """
    connection = None
    try:
        # Get a database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # SQL query to insert a new job request
        insert_query = """
        INSERT INTO job_request (
            request_id, 
            status, 
            created_at
        ) VALUES (
            %s, 
            %s, 
            NOW()
        )
        """
        
        # Execute the insert query
        cursor.execute(insert_query, (request_id, 'pending'))
        
        # Commit the transaction
        connection.commit()
        
        return True
    
    except Exception as e:
        # Log the error
        print(f"Error inserting job request: {e}")
        
        # Rollback the transaction in case of error
        if connection:
            connection.rollback()
        
        return False
    
    finally:
        # Always release the connection back to the pool
        if connection:
            release_db_connection(connection)

def update_status(request_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE requests SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (status, request_id))
    conn.commit()
    cur.close()
    conn.close()


def upload_image_to_db(request_id, image_id, image_data):
    """
    Upload the compressed image to the database and return a public link.
    
    Args:
        request_id (str): Unique identifier for the request.
        image_id (str): Unique identifier for the image.
        image_data (io.BytesIO): Compressed image data.
    
    Returns:
        str: Public link to the compressed image.
    """
    connection = None
    try:
        # Get a connection from the pool
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert the image into the database
        cursor.execute(
            "INSERT INTO images (id, request_id, image_data) VALUES (%s, %s, %s)",
            (image_id, request_id, Binary(image_data.getvalue()))  # Use Binary for BLOB data
        )
        connection.commit()
        
        # Generate a public link (for demonstration, this is a placeholder)
        public_link = f"http://example.com/images/{image_id}"
        
        return public_link

    except Exception as e:
        print(f"Failed to upload image to database: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            release_db_connection(connection)