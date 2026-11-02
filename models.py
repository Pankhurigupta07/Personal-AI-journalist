from pydantic import BaseModel
from typing import List, Optional

class NewsRequest(BaseModel):
    topics: Optional[List[str]] = None
    source_type: str = "news"