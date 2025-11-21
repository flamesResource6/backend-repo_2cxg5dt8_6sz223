"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Episode(BaseModel):
    number: int = Field(..., ge=1, description="Episode number starting from 1")
    title: str = Field(..., description="Episode title")
    video_url: Optional[str] = Field(None, description="Public/embeddable video URL (e.g., YouTube)")
    language: str = Field("Hindi", description="Audio language, e.g., Hindi, Japanese")

class Anime(BaseModel):
    """
    Anime collection schema
    Collection name: "anime"
    """
    title: str = Field(..., description="Anime title")
    description: Optional[str] = Field(None, description="Short synopsis")
    cover_image: Optional[str] = Field(None, description="Poster/cover image URL")
    trailer_url: Optional[str] = Field(None, description="Embeddable trailer URL (YouTube)" )
    languages: List[str] = Field(default_factory=lambda: ["Hindi"], description="Available languages")
    genres: List[str] = Field(default_factory=list, description="Genre tags")
    year: Optional[int] = Field(None, ge=1950, le=2100, description="Release year")
    episodes: List[Episode] = Field(default_factory=list, description="List of episodes")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
