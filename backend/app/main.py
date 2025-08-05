from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import transcripts, vocabulary, text_adaptation, auth, text_analysis, library, smart_analysis, web_library
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Nexus API",
    description="API for the Nexus language learning platform.",
    version="0.1.0"
)

# CORS Middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(transcripts.router, prefix="/api", tags=["transcripts"])
app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["vocabulary"])
app.include_router(text_adaptation.router, prefix="/api/adaptation", tags=["text-adaptation"])
app.include_router(text_analysis.router, prefix="/api/text-analysis", tags=["text-analysis"])
app.include_router(library.router, prefix="/api", tags=["library"])
app.include_router(smart_analysis.router, prefix="/api/smart", tags=["smart-analysis"])
app.include_router(web_library.router, prefix="/api/web-library", tags=["web-library"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nexus API - Your Personal Language Learning Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 