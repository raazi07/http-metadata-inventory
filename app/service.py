import httpx
from datetime import datetime
from app.models import MetadataRecord
from app.database import db
import logging

logger = logging.getLogger(__name__)

async def fetch_and_store_metadata(url: str):
    """
    Fetch metadata for a URL and store/update it in MongoDB.
    
    Returns:
        The metadata record if successful, None otherwise.
    """
    logger.info(f"Starting fetch for {url}")
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            
            # Extract headers and cookies
            headers = dict(response.headers)
            cookies = dict(response.cookies)
            
            # Create record
            record = MetadataRecord(
                url=url,
                headers=headers,
                cookies=cookies,
                page_source=response.text,
                status_code=response.status_code,
                fetched_at=datetime.utcnow()
            )
            
            # Upsert into database (update if exists, insert if not)
            result = await db.metadata.update_one(
                {"url": url},
                {"$set": record.model_dump()},
                upsert=True
            )
            
            logger.info(f"Successfully stored metadata for {url}. Modified count: {result.modified_count}, Upserted ID: {result.upserted_id}")
            return record.model_dump()
            
    except httpx.RequestError as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        # In a real system, we might want to store a failed record or retry.
        # For now, we log the error and return None.
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {str(e)}")
        return None
