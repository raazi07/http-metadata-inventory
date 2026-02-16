from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, Optional
from datetime import datetime

class URLInput(BaseModel):
    url: HttpUrl = Field(..., description="The URL to fetch metadata from")

class MetadataRecord(BaseModel):
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    cookies: Dict[str, str] = Field(default_factory=dict)
    page_source: str = Field(default="")
    status_code: Optional[int] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com",
                "headers": {"Content-Type": "text/html"},
                "cookies": {"session_id": "12345"},
                "page_source": "<html>...</html>",
                "status_code": 200,
                "fetched_at": "2024-05-20T12:00:00Z"
            }
        }
    }
