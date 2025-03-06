from flask import Flask, request, jsonify
import pandas as pd

from utils import *
# from celery import Celery
# import psycopg2
import requests  # For sending webhook requests

# Initialize Flask app
app = Flask(__name__)




@app.route('/upload', methods=['POST'])
def upload_csv():
    """Endpoint to upload a CSV file with product images."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    
    # Validate the CSV
    df, error = validate_csv_file(file)
    if error:
        return jsonify({"error": error}), 400
    
    # Process the request
    request_id = process_csv_request(df)
    
    # Return response
    return jsonify({"request_id": request_id}), 202


# Route to check job status
@app.route('/job/status/<request_id>', methods=['GET'])
def check_job_status(request_id):
    """
    Endpoint to check the status of a job.
    """
    return get_job_status(request_id)

if __name__ == '__main__':
    app.run(debug=True)
    initialize_db_pool()