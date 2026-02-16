# HTTP Metadata Inventory Service

A FastAPI-based service to collect and retrieve metadata (headers, cookies, page source) for URLs. It uses MongoDB for storage and Docker Compose for orchestration.

## Features

- **POST /metadata**: Fetch and store metadata for a given URL immediately.
- **GET /metadata**: Retrieve stored metadata. If missing, triggers a background collection and returns 202 Accepted.
- **Background Worker**: Handles metadata collection asynchronously to ensure API responsiveness.
- **MongoDB Storage**: Stores metadata with headers, cookies, and page source.
- **Dockerized**: Fully containerized environment.

## Requirements

- Docker & Docker Compose
- Python 3.11+ (for local development)

## Running the Application

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd http-metadata-inventory
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
   The API will be available at `http://localhost:8000`.

## API Documentation

Once running, you can access the interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### 1. Create Metadata (POST)
   - **URL**: `/metadata`
   - **Method**: `POST`
   - **Body**:
     ```json
     {
       "url": "https://example.com"
     }
     ```
   - **Response**: `201 Created`

#### 2. Retrieve Metadata (GET)
   - **URL**: `/metadata?url=https://example.com`
   - **Method**: `GET`
   - **Response**:
     - `200 OK`: Returns metadata (headers, cookies, page_source).
     - `202 Accepted`: Metadata not found, collection triggered in background.

## Testing

To run the tests, you can use `pytest`.

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests**:
   ```bash
   pytest
   ```

## Architecture

- **FastAPI**: Handles HTTP requests and async background tasks.
- **Motor**: Async MongoDB driver for non-blocking database operations.
- **Pydantic**: Data validation and serialization.
- **Docker Compose**: Orchestrates the API and MongoDB containers.

## Configuration

Environment variables are managed in `app/config.py` and `docker-compose.yml`.
- `MONGO_URI`: MongoDB connection string.
- `DB_NAME`: Database name (default: `metadata_inventory`).
