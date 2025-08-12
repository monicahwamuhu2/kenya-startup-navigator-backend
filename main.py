import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the most basic FastAPI app
app = FastAPI(
    title="Kenya Startup Navigator API",
    description="AI-powered guidance for Kenya's startup ecosystem",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - simple health indicator"""
    return {
        "message": "🚀 Kenya Startup Navigator API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy"}

@app.post("/api/v1/query")
async def process_query(request: dict):
    """Simplified query endpoint for testing"""
    question = request.get("question", "")
    
    return {
        "answer": f"Thank you for asking: '{question}'. This is a test response from Kenya Startup Navigator API. The backend is working correctly!",
        "confidence": 0.95,
        "processing_time": 1.2,
        "sources": ["Kenya Startup Ecosystem Database"],
        "suggested_follow_ups": [
            "How do I get started with my startup?",
            "What funding options are available?",
            "Which accelerators should I consider?"
        ],
        "timestamp": "2024-08-12T20:00:00Z"
    }

# Keep it simple - no complex startup logic
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )