import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Anime, Episode

app = FastAPI(title="Anime TV API", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Anime TV Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Helpers
class AnimeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    trailer_url: Optional[str] = None
    languages: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    year: Optional[int] = None

class EpisodeCreate(BaseModel):
    number: int
    title: str
    video_url: Optional[str] = None
    language: str = "Hindi"

@app.get("/api/anime", response_model=List[dict])
def list_anime(q: Optional[str] = None, language: Optional[str] = None, genre: Optional[str] = None):
    filter_dict = {}
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    if language:
        filter_dict["languages"] = language
    if genre:
        filter_dict["genres"] = genre
    items = get_documents("anime", filter_dict)
    for it in items:
        it["_id"] = str(it.get("_id"))
    return items

@app.post("/api/anime", status_code=201)
def create_anime(payload: AnimeCreate):
    data = payload.model_dump()
    data.setdefault("languages", ["Hindi"]) 
    data.setdefault("genres", [])
    data.setdefault("episodes", [])
    new_id = create_document("anime", data)
    return {"id": new_id}

@app.get("/api/anime/{anime_id}")
def get_anime(anime_id: str):
    try:
        doc = db["anime"].find_one({"_id": ObjectId(anime_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Anime not found")
        doc["_id"] = str(doc["_id"]) 
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

@app.post("/api/anime/{anime_id}/episodes", status_code=201)
def add_episode(anime_id: str, payload: EpisodeCreate):
    try:
        update = {
            "$push": {
                "episodes": payload.model_dump()
            },
            "$set": {"updated_at": None}
        }
        result = db["anime"].update_one({"_id": ObjectId(anime_id)}, update)
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Anime not found")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

@app.get("/api/anime/{anime_id}/episodes")
def list_episodes(anime_id: str):
    try:
        doc = db["anime"].find_one({"_id": ObjectId(anime_id)}, {"episodes": 1})
        if not doc:
            raise HTTPException(status_code=404, detail="Anime not found")
        return doc.get("episodes", [])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

@app.post("/api/seed")
def seed_data():
    """Seed the database with a few Hindi anime entries for demo."""
    count = db["anime"].count_documents({}) if db is not None else 0
    if count > 0:
        return {"inserted": 0, "message": "Collection already has data"}

    sample = [
        {
            "title": "Naruto (Hindi Dub)",
            "description": "A young ninja seeks recognition and dreams of becoming the Hokage.",
            "cover_image": "https://i.imgur.com/8Km9tLL.jpeg",
            "trailer_url": "https://www.youtube.com/embed/-G9BqkgZXRA",
            "languages": ["Hindi", "Japanese"],
            "genres": ["Action", "Adventure"],
            "year": 2002,
            "episodes": [
                {"number": 1, "title": "Enter: Naruto Uzumaki!", "video_url": "https://www.youtube.com/embed/klqEo3v7u5M", "language": "Hindi"},
                {"number": 2, "title": "My Name is Konohamaru!", "video_url": "https://www.youtube.com/embed/0mGZ2lN1tS8", "language": "Hindi"}
            ]
        },
        {
            "title": "Demon Slayer (Hindi)",
            "description": "Tanjiro Kamado becomes a demon slayer after his family is slaughtered.",
            "cover_image": "https://i.imgur.com/2yaf2wb.jpeg",
            "trailer_url": "https://www.youtube.com/embed/VQGCKyvzIM4",
            "languages": ["Hindi", "Japanese"],
            "genres": ["Action", "Dark Fantasy"],
            "year": 2019,
            "episodes": [
                {"number": 1, "title": "Cruelty", "video_url": "https://www.youtube.com/embed/vLFu4Hjz-FM", "language": "Hindi"}
            ]
        }
    ]
    inserted = db["anime"].insert_many(sample)
    return {"inserted": len(inserted.inserted_ids)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
