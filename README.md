---

# Image Processing API

This is a Flask-based API for processing CSV files containing product image URLs. The API compresses the images and stores them in a PostgreSQL database. It also supports background processing using Celery and provides webhook notifications.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Celery Background Tasks](#celery-background-tasks)
8. [Webhook Support](#webhook-support)
9. [Contributing](#contributing)
10. [License](#license)

---

## Features

- **CSV Upload**: Upload a CSV file containing product image URLs.
- **Validation**: Validate the CSV file structure.
- **Image Compression**: Compress images and store them in a PostgreSQL database.
- **Job Status Tracking**: Check the status of a job using a unique request ID.
- **Webhook Support**: Notify external systems about job status changes.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Set up environment variables**:
   Create a `.env` file in the root directory with the following content:
   ```plaintext
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=your_database_port
   ```

2. **Initialize the database connection pool**:
   Run the following command to initialize the PostgreSQL connection pool:
   ```bash
   python database_setup.py
   ```

---

## Running the Application

1. **Start the Flask application**:
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`.

2. **Start the Celery worker** (in a separate terminal):
   ```bash
   celery -A app.celery worker --loglevel=info
   ```
   This will handle background tasks for processing CSV files and images.

---

## API Endpoints

### 1. Upload CSV File

- **URL**: `/upload`
- **Method**: `POST`
- **Description**: Upload a CSV file containing product image URLs.
- **Request Body**:
  - `file`: CSV file with columns `S. No.`, `Product Name`, and `Input Image Urls`.
- **Response**:
  - `request_id`: Unique identifier for the job.

   **Example Request**:
   ```bash
   curl -X POST -F "file=@path/to/your/file.csv" http://localhost:5000/upload
   ```

   **Example Response**:
   ```json
   {
       "request_id": "550e8400-e29b-41d4-a716-446655440000"
   }
   ```

### 2. Check Job Status

- **URL**: `/job/status/<request_id>`
- **Method**: `GET`
- **Description**: Check the status of a job using the request ID.
- **Response**:
  - `request_id`: Unique identifier for the job.
  - `status`: Current status of the job (`PROCESSING`, `COMPLETED`, `FAILED`).
  - `created_at`: Timestamp when the job was created.
  - `updated_at`: Timestamp when the job was last updated.
  - `completion_percentage`: Percentage of completion.
  - `error_message`: Error message if the job failed.

   **Example Request**:
   ```bash
   curl http://localhost:5000/job/status/550e8400-e29b-41d4-a716-446655440000
   ```

   **Example Response**:
   ```json
   {
       "request_id": "550e8400-e29b-41d4-a716-446655440000",
       "status": "COMPLETED",
       "created_at": "2023-10-01T12:00:00Z",
       "updated_at": "2023-10-01T12:05:00Z",
       "completion_percentage": 100,
       "error_message": null
   }
   ```

---

## Database Schema

The database schema includes the following tables:

### `job_request`
- `request_id` (UUID): Unique identifier for the job.
- `status` (String): Current status of the job (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- `created_at` (Timestamp): When the job was created.
- `updated_at` (Timestamp): When the job was last updated.
- `completion_percentage` (Integer): Percentage of completion.
- `error_message` (Text): Error message if the job failed.

### `compressed_images`
- `image_id` (UUID): Unique identifier for the compressed image.
- `request_id` (UUID): Foreign key referencing the job request.
- `image_url` (Text): Public URL of the compressed image.
- `created_at` (Timestamp): When the image was compressed.

---

## Celery Background Tasks

- The `process_csv` Celery task handles the background processing of CSV files and images.
- It updates the job status in the database and triggers a webhook (if provided) upon completion or failure.

---

## Webhook Support

- If a `webhook_url` is provided, the API will send a POST request to the specified URL with the following payload:
  ```json
  {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "COMPLETED",
      "message": "CSV and image processing completed successfully."
  }
  ```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

