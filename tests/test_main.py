import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app

# Mock DB result for update_one
class MockUpdateResult:
    modified_count = 1
    upserted_id = "test_id"

@pytest.mark.asyncio
async def test_create_metadata_success():
    # Mock the database call in service
    # Patch db.metadata.update_one
    with patch("app.service.db.metadata.update_one", new_callable=AsyncMock) as mock_update:
        mock_update.return_value.modified_count = 1
        mock_update.return_value.upserted_id = "test_id"
        
        # Mock httpx.AsyncClient ONLY in app.service
        # We need to construct a mock that works as a context manager
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.cookies = {"session": "abc"}
        mock_response.text = "<html>Test</html>"
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        with patch("app.service.httpx.AsyncClient", return_value=mock_client_instance):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post("/metadata", json={"url": "https://example.com"})
            
            assert response.status_code == 201
            assert response.json()["message"] == "Metadata created successfully"
            mock_update.assert_called_once()

@pytest.mark.asyncio
async def test_get_metadata_existing():
    # Mock the database call in main
    expected_data = {
        "url": "https://example.com",
        "headers": {"Content-Type": "text/html"},
        "cookies": {},
        "page_source": "<html>Test</html>",
        "status_code": 200,
        "fetched_at": "2024-05-20T12:00:00"
    }
    
    with patch("app.main.db.metadata.find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = expected_data
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/metadata", params={"url": "https://example.com"})
        
        assert response.status_code == 200
        assert response.json() == expected_data

@pytest.mark.asyncio
async def test_get_metadata_missing():
    # Mock database to return None
    with patch("app.main.db.metadata.find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        
        # We also need to mock fetch_and_store_metadata so it doesn't actually run or cause issues
        # But wait, fetch_and_store_metadata is imported in main.py
        with patch("app.main.fetch_and_store_metadata") as mock_bg_task:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get("/metadata", params={"url": "https://example.com"})
            
            assert response.status_code == 202
            assert response.json()["message"] == "Request accepted. Metadata collection in progress."
