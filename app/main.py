from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from app.models import URLInput, MetadataRecord
from app.database import db
from app.service import fetch_and_store_metadata
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown logic.
    Retries DB connection/index creation on startup to ensure resilience.
    """
    # Startup logic
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            # Create a unique index on the 'url' field
            await db.metadata.create_index("url", unique=True)
            logger.info("Created unique index on 'url' field.")
            break
        except Exception as e:
            logger.warning(f"Attempt {i+1}/{max_retries}: Could not create index (DB might be starting up): {e}")
            if i < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to initialize database after multiple retries.")
    
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title="HTTP Metadata Inventory",
    description="Service to collect and retrieve metadata for URLs.",
    version="1.0.0",
    lifespan=lifespan,
    redoc_url=None
)

@app.post("/metadata", status_code=status.HTTP_201_CREATED)
async def create_metadata(input_data: URLInput):
    """
    Create a metadata record for a given URL.
    This endpoint fetches the metadata immediately and stores it.
    """
    url = str(input_data.url)
    try:
        # We'll reuse the fetch logic.
        # Note: The requirements say POST creates a record. 
        # We will wait for the result here.
        record = await fetch_and_store_metadata(url)
        if not record:
             raise HTTPException(status_code=500, detail="Failed to fetch metadata")
        
        return {"message": "Metadata created successfully", "url": url}
    except Exception as e:
        logger.error(f"Error in POST /metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metadata")
async def get_metadata(url: str, background_tasks: BackgroundTasks):
    """
    Retrieve metadata for a given URL.
    If metadata exists, returns it.
    If not, triggers background collection and returns 202 Accepted.
    """
    # Check if metadata exists
    existing_record = await db.metadata.find_one({"url": url}, {"_id": 0})
    
    if existing_record:
        return existing_record
    
    # If missing, trigger background task
    background_tasks.add_task(fetch_and_store_metadata, url)
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "Request accepted. Metadata collection in progress.", "url": url}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
