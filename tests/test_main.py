import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app

# Create a module-scoped event loop for pytest-asyncio
@pytest.fixture(scope="module")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Mock DB result for update_one
class MockUpdateResult:
    modified_count = 1
    upserted_id = "test_id"

@pytest.fixture
def mock_db():
    # Patch DB in all locations where it's imported
    with patch("app.database.db") as mock_db_database, \
         patch("app.main.db") as mock_db_main, \
         patch("app.service.db") as mock_db_service:
        
        # Create a single mock object to control all of them
        shared_mock = MagicMock()
        
        # Configure common async methods
        shared_mock.metadata.create_index = AsyncMock()
        shared_mock.metadata.update_one = AsyncMock()
        shared_mock.metadata.find_one = AsyncMock()
        
        # Assign this shared mock to all patched locations
        mock_db_database.metadata = shared_mock.metadata
        mock_db_main.metadata = shared_mock.metadata
        mock_db_service.metadata = shared_mock.metadata
        
        yield shared_mock

@pytest.mark.asyncio(scope="module")
async def test_create_metadata_success(mock_db):
    # Setup update_one return value
    mock_result = MagicMock()
    mock_result.modified_count = 1
    mock_result.upserted_id = "test_id"
    mock_db.metadata.update_one.return_value = mock_result
    
    # Setup mock client that will be used inside the 'async with' block
    mock_client_instance = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.cookies = {"session": "abc"}
    mock_response.text = "<html>Test</html>"
    mock_client_instance.get.return_value = mock_response

    # This mock represents the object returned by httpx.AsyncClient(...)
    # Its __aenter__ method should return the client instance
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value = mock_client_instance
    mock_client_context.__aexit__.return_value = None

    # Patch httpx.AsyncClient to return our context manager mock
    with patch("app.service.httpx.AsyncClient", return_value=mock_client_context):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/metadata", json={"url": "https://example.com"})
        
        # Print response body if assertion fails
        if response.status_code != 201:
            print(f"Response Body: {response.text}")
        
        assert response.status_code == 201
        assert response.json()["message"] == "Metadata created successfully"
        mock_db.metadata.update_one.assert_called_once()

@pytest.mark.asyncio(scope="module")
async def test_get_metadata_existing(mock_db):
    # Setup find_one return value
    expected_data = {
        "url": "https://example.com",
        "headers": {"Content-Type": "text/html"},
        "cookies": {},
        "page_source": "<html>Test</html>",
        "status_code": 200,
        "fetched_at": "2024-05-20T12:00:00"
    }
    mock_db.metadata.find_one.return_value = expected_data
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/metadata", params={"url": "https://example.com"})
    
    assert response.status_code == 200
    assert response.json() == expected_data

@pytest.mark.asyncio(scope="module")
async def test_get_metadata_missing(mock_db):
    # Setup find_one to return None
    mock_db.metadata.find_one.return_value = None
    
    # We also need to mock fetch_and_store_metadata so it doesn't actually run or cause issues
    # But wait, fetch_and_store_metadata is imported in main.py
    with patch("app.main.fetch_and_store_metadata") as mock_bg_task:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/metadata", params={"url": "https://example.com"})
        
        assert response.status_code == 202
        assert response.json()["message"] == "Request accepted. Metadata collection in progress."
