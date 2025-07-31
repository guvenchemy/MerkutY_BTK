from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import transcripts, vocabulary, text_adaptation, auth, text_analysis
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(transcripts.router, prefix="/api", tags=["transcripts"])
app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["vocabulary"])
app.include_router(text_adaptation.router, prefix="/api/adaptation", tags=["text-adaptation"])
app.include_router(text_analysis.router, prefix="/api/analysis", tags=["text-analysis"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nexus API - Your Personal Language Learning Assistant"} 