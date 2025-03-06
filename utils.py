import requests
from PIL import Image
import io
import os
from database_query import *
from celery import Celery
from flask import Flask, request, jsonify
import pandas as pd
import io
import uuid

def process_image(image_url, request_id, quality=50):
    """
    Download an image from a public URL, compress it, and upload it to the database.
    
    Args:
        image_url (str): Public URL of the image to download.
        request_id (str): Unique identifier for the request (used as a key in the database).
        quality (int, optional): Compression quality (1-95). Lower value means higher compression. Defaults to 50.
    
    Returns:
        str: Public link to the compressed image.
    """
    try:
        # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Open the image using Pillow
        with Image.open(io.BytesIO(response.content)) as img:
            # Convert to RGB mode if image is in RGBA (removes alpha channel)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Compress the image
            compressed_image = io.BytesIO()
            img.save(compressed_image, format='JPEG', optimize=True, quality=quality)
            compressed_image.seek(0)  # Reset the stream position to the beginning
            
            # Upload the compressed image to the database
            image_id = str(uuid.uuid4())  # Generate a unique ID for the image
            public_link = upload_image_to_db(request_id, image_id, compressed_image)
            
            return public_link

    except Exception as e:
        print(f"Failed to process image: {e}")
        raise
@celery.task(bind=True)
def process_csv(self, request_id, df, webhook_url=None):
    """Celery task to process the CSV data, images, and trigger a webhook."""
    try:
        # Update status to PROCESSING
        update_status(request_id, "PROCESSING")


        for index, row in df.iterrows():
            output_image_urls = [process_image(url.strip()) for url in row['Input Image Urls'].split(',') if url.strip()]


        # Update status to COMPLETED
        update_status(request_id, "COMPLETED")

        # Trigger webhook if URL is provided
        if webhook_url:
            webhook_payload = {
                "request_id": request_id,
                "status": "COMPLETED",
                "message": "CSV and image processing completed successfully."
            }
            try:
                response = requests.post(webhook_url, json=webhook_payload)
                response.raise_for_status()
                print(f"Webhook triggered successfully: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to trigger webhook: {e}")

        print(f"Processed data for request ID: {request_id}")
        return {"request_id": request_id}

    except pd.errors.EmptyDataError:
        update_status(request_id, "FAILED")
        if webhook_url:
            webhook_payload = {
                "request_id": request_id,
                "status": "FAILED",
                "message": "The uploaded CSV file is empty"
            }
            try:
                response = requests.post(webhook_url, json=webhook_payload)
                response.raise_for_status()
                print(f"Webhook triggered successfully: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to trigger webhook: {e}")

        raise ValueError("The uploaded CSV file is empty")
    except Exception as e:
        update_status(request_id, "FAILED")
        if webhook_url:
            webhook_payload = {
                "request_id": request_id,
                "status": "FAILED",
                "message": f"CSV and image processing failed: {str(e)}"
            }
            try:
                response = requests.post(webhook_url, json=webhook_payload)
                response.raise_for_status()
                print(f"Webhook triggered successfully: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to trigger webhook: {e}")

        print(f"Task failed: {e}")
        raise Exception(f"Failed to process CSV and images: {str(e)}")
    
def validate_csv_file(file):
    """Validate that the file is a proper CSV with required columns."""
    if not file or file.filename == '':
        return None, "No selected file"
        
    if not file.filename.endswith('.csv'):
        return None, "File is not a CSV"
    
    try:
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        
        required_columns = ['S. No.', 'Product Name', 'Input Image Urls']
        for column in required_columns:
            if column not in df.columns:
                return None, f"CSV must contain '{column}' column"
                
        return df, None
    
    except pd.errors.EmptyDataError:
        return None, "The uploaded CSV file is empty"
    except Exception as e:
        return None, f"Failed to process CSV file: {str(e)}"

def process_csv_request(df):
    """Process the CSV and initiate background task."""
    request_id = str(uuid.uuid4())
    process_csv.delay(request_id, df)
    return request_id

def get_job_status(request_id):
    """
    Check the status of a job request.
    
    Args:
        request_id (str): The unique identifier for the job request
        
    Returns:
        dict: JSON response with status information
    """
    connection = None
    try:
        # Validate request_id format (assuming it's a UUID)
        try:
            uuid.UUID(request_id)
        except ValueError:
            return jsonify({"error": "Invalid request_id format"}), 400
            
        # Get a database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # SQL query to get job status
        status_query = """
        SELECT 
            status, 
            created_at,
            updated_at,
            completion_percentage,
            error_message
        FROM 
            job_request 
        WHERE 
            request_id = %s
        """
        
        # Execute the query
        cursor.execute(status_query, (request_id,))
        
        # Fetch the result
        result = cursor.fetchone()
        
        # Check if job exists
        if result is None:
            return jsonify({"error": "Job not found"}), 404
            
        # Extract data from result
        status, created_at, updated_at, completion_percentage, error_message = result
        
        # Prepare response
        response = {
            "request_id": request_id,
            "status": status,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "completion_percentage": completion_percentage or 0
        }
        
        # Add error message if it exists
        if error_message:
            response["error_message"] = error_message
            
        return jsonify(response), 200
        
    except Exception as e:
        # Log the error
        print(f"Error retrieving job status: {e}")
        return jsonify({"error": "Failed to retrieve job status", "details": str(e)}), 500
        
    finally:
        # Always release the connection back to the pool
        if connection:
            release_db_connection(connection)
