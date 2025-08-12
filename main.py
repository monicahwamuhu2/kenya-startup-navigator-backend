from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import os
from typing import List, Optional
import time

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

app = FastAPI(
    title="Kenya Startup Navigator API",
    description="AI-powered guidance for Kenya's startup ecosystem",
    version="1.0.0"
)

# CORS configuration for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kenya-startup-navigator-frontend-ruddy.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    startup_profile: Optional[dict] = None
    context: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    processing_time: float
    sources: List[str]
    suggested_follow_ups: List[str]
    timestamp: str

# System prompt for Kenya startup ecosystem
SYSTEM_PROMPT = """You are KenyaStartup AI, an expert advisor on Kenya's startup ecosystem. You have comprehensive knowledge of Kenya's business landscape and provide practical, actionable advice.

Your expertise includes:
- Major VCs: TLcom Capital, Novastar Ventures, GreenTec Capital, 4DX Ventures
- Accelerators: iHub, MEST Africa, Antler Kenya, Founder Institute
- Government Programs: KIICO, Youth Enterprise Fund, Women Enterprise Fund
- Regulatory: Central Bank of Kenya, Kenya Revenue Authority, Communications Authority
- Co-working: iHub, NaiLab, GrowthHub Africa

Always provide:
1. Specific, actionable advice for Kenya
2. Relevant local contacts and resources
3. Realistic timelines and costs
4. Consider local business culture
5. Include successful Kenyan startup examples

Format responses clearly with practical next steps."""

async def call_groq_api(messages: List[dict]) -> dict:
    """Call Groq API with error handling"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Groq API error: {response.text}"
                )
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="Request timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

def calculate_confidence(content: str, question: str) -> float:
    """Calculate confidence score based on response quality"""
    if not content:
        return 0.0
    
    score = 0.0
    
    # Length factor
    score += min(len(content) / 1000, 1.0) * 0.3
    
    # Kenya-specific content
    kenya_terms = ['kenya', 'kenyan', 'nairobi', 'kra', 'cbk', 'ihub', 'tlcom', 'shilling']
    kenya_count = sum(1 for term in kenya_terms if term.lower() in content.lower())
    score += min(kenya_count / 5, 1.0) * 0.4
    
    # Structure indicators
    structure_count = content.count('##') + content.count('**') + content.count('- ')
    score += min(structure_count / 6, 1.0) * 0.3
    
    return min(score, 1.0)

def extract_sources(content: str) -> List[str]:
    """Extract relevant sources from content"""
    sources = []
    potential_sources = [
        "TLcom Capital", "Novastar Ventures", "GreenTec Capital",
        "iHub", "MEST Africa", "Antler Kenya",
        "Central Bank of Kenya", "Kenya Revenue Authority",
        "Nairobi Angel Network"
    ]
    
    for source in potential_sources:
        if source.lower() in content.lower():
            sources.append(source)
    
    if not sources:
        sources.append("Kenya Startup Ecosystem Database")
    
    return sources[:3]

def generate_follow_ups(question: str) -> List[str]:
    """Generate relevant follow-up questions"""
    question_lower = question.lower()
    
    if 'fund' in question_lower or 'invest' in question_lower:
        return [
            "What documents do I need for investor meetings?",
            "How long does fundraising typically take in Kenya?",
            "What valuation should I expect at my stage?"
        ]
    elif 'legal' in question_lower or 'register' in question_lower:
        return [
            "What are the ongoing compliance requirements?",
            "How much should I budget for legal costs?",
            "Which law firms specialize in startups?"
        ]
    elif 'accelerator' in question_lower or 'incubator' in question_lower:
        return [
            "What's the application process like?",
            "How do I prepare for accelerator interviews?",
            "What equity do accelerators typically take?"
        ]
    else:
        return [
            "How do I get started in Kenya's startup ecosystem?",
            "What funding options are available for early-stage startups?",
            "Which accelerators should I consider in Nairobi?"
        ]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 Kenya Startup Navigator API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/v1/query",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Kenya Startup Navigator API",
        "ai_service": "Groq LLaMA 3",
        "timestamp": time.time()
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process AI query about Kenya's startup ecosystem"""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.question or len(request.question.strip()) < 5:
            raise HTTPException(status_code=400, detail="Question too short")
        
        if len(request.question) > 2000:
            raise HTTPException(status_code=400, detail="Question too long")
        
        # Build context-aware prompt
        user_prompt = f"Question: {request.question}"
        
        if request.startup_profile:
            profile_info = []
            for key, value in request.startup_profile.items():
                if value:
                    profile_info.append(f"{key}: {value}")
            if profile_info:
                user_prompt += f"\n\nStartup Profile:\n" + "\n".join(profile_info)
        
        if request.context:
            user_prompt += f"\n\nAdditional Context: {request.context}"
        
        # Prepare messages for Groq
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call Groq API
        response_data = await call_groq_api(messages)
        
        # Extract content
        content = ""
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
        
        if not content:
            raise HTTPException(status_code=500, detail="Empty response from AI")
        
        # Calculate metrics
        processing_time = time.time() - start_time
        confidence = calculate_confidence(content, request.question)
        sources = extract_sources(content)
        follow_ups = generate_follow_ups(request.question)
        
        # Return response
        return QueryResponse(
            answer=content,
            confidence=confidence,
            processing_time=processing_time,
            sources=sources,
            suggested_follow_ups=follow_ups,
            timestamp=str(int(time.time()))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)