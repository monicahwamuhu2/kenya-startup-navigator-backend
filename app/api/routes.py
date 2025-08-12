from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime

# Import our custom modules
from app.models.schemas import (
    QueryRequest, QueryResponse, StartupProfile, 
    InvestorProfile, EcosystemEntity, AnalyticsData
)
from app.services.groq_service import GroqService
from app.services.startup_service import StartupService
from app.services.matching_service import MatchingService
from app.core.dependencies import get_current_timestamp, validate_query_rate_limit
from app.core.config import settings

# Create the main router
router = APIRouter()

# Initialize services (in production, these would be dependency-injected)
groq_service = GroqService()
startup_service = StartupService()
matching_service = MatchingService()


# QUERY PROCESSING ENDPOINTS - Core AI functionality

@router.post("/query", response_model=QueryResponse, tags=["AI Query"])
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    rate_limit_check: bool = Depends(validate_query_rate_limit)
):
    """
    **Process AI Query**
    
    Submit a question about Kenya's startup ecosystem and receive an AI-powered response.
    
    **Features:**
    - Intelligent context understanding
    - Kenya-specific startup knowledge
    - Investor and accelerator recommendations
    - Actionable next steps
    
    **Example Queries:**
    - "How do I raise seed funding for my fintech startup?"
    - "Which accelerators in Nairobi focus on agritech?"
    - "What are the legal requirements for incorporating in Kenya?"
    """
    try:
        # Validate query length
        if len(request.question) < settings.MIN_QUERY_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Query too short. Minimum {settings.MIN_QUERY_LENGTH} characters required."
            )
        
        if len(request.question) > settings.MAX_QUERY_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Query too long. Maximum {settings.MAX_QUERY_LENGTH} characters allowed."
            )
        
        # Process the query with Groq
        start_time = datetime.now()
        
        # Get AI response
        ai_response = await groq_service.process_startup_query(
            question=request.question,
            startup_profile=request.startup_profile,
            context=request.context
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get relevant ecosystem matches
        ecosystem_matches = []
        if request.startup_profile:
            ecosystem_matches = await matching_service.find_relevant_resources(
                request.startup_profile
            )
        
        # Prepare response
        response = QueryResponse(
            answer=ai_response.content,
            confidence=ai_response.confidence,
            processing_time=processing_time,
            sources=ai_response.sources,
            related_resources=ecosystem_matches,
            suggested_follow_ups=ai_response.suggested_questions,
            timestamp=get_current_timestamp()
        )
        
        # Log analytics in background
        background_tasks.add_task(
            log_query_analytics,
            request.question,
            request.startup_profile,
            processing_time,
            ai_response.confidence
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/query/stream", tags=["AI Query"])
async def stream_query_response(
    request: QueryRequest,
    rate_limit_check: bool = Depends(validate_query_rate_limit)
):
    """
     **Stream AI Response**
    
    Get real-time streaming response for better user experience.
    Response is sent as Server-Sent Events (SSE).
    """
    
    async def generate_response():
        """Generate streaming response chunks"""
        try:
            async for chunk in groq_service.stream_startup_query(
                question=request.question,
                startup_profile=request.startup_profile,
                context=request.context
            ):
                # Format as SSE
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
            
        except Exception as e:
            error_data = {
                'error': True,
                'message': str(e),
                'done': True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# STARTUP PROFILE ENDPOINTS - User management

@router.post("/startups/profile", response_model=Dict[str, Any], tags=["Startup Profiles"])
async def create_startup_profile(profile: StartupProfile):
    """
    👥 **Create Startup Profile**
    
    Create a comprehensive startup profile for personalized recommendations.
    
    **Profile includes:**
    - Company information and stage
    - Industry and target market
    - Team composition
    - Funding history and goals
    """
    try:
        # Validate and process the profile
        processed_profile = await startup_service.create_profile(profile)
        
        # Generate personalized recommendations
        recommendations = await matching_service.generate_recommendations(processed_profile)
        
        return {
            "profile_id": processed_profile.id if hasattr(processed_profile, 'id') else "generated_id",
            "status": "created",
            "recommendations": recommendations,
            "next_steps": startup_service.generate_next_steps(processed_profile),
            "timestamp": get_current_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/startups/profile/{profile_id}", response_model=StartupProfile, tags=["Startup Profiles"])
async def get_startup_profile(profile_id: str):
    """
     **Get Startup Profile**
    
    Retrieve an existing startup profile by ID.
    """
    profile = await startup_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/startups/profile/{profile_id}", tags=["Startup Profiles"])
async def update_startup_profile(profile_id: str, updates: Dict[str, Any]):
    """
     **Update Startup Profile**
    
    Update specific fields in an existing startup profile.
    """
    try:
        updated_profile = await startup_service.update_profile(profile_id, updates)
        return {
            "status": "updated",
            "profile": updated_profile,
            "timestamp": get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ECOSYSTEM DATA ENDPOINTS - Resource discovery

@router.get("/ecosystem/investors", response_model=List[InvestorProfile], tags=["Ecosystem"])
async def get_investors(
    industry: Optional[str] = Query(None, description="Filter by industry focus"),
    stage: Optional[str] = Query(None, description="Filter by investment stage"),
    ticket_size_min: Optional[int] = Query(None, description="Minimum ticket size"),
    ticket_size_max: Optional[int] = Query(None, description="Maximum ticket size"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """
     **Get Investor Database**
    
    Access comprehensive database of Kenya's startup investors.
    
    **Filters available:**
    - Industry focus (fintech, agritech, healthtech, etc.)
    - Investment stage (pre-seed, seed, Series A, etc.)
    - Ticket size range
    - Geographic location
    """
    filters = {
        "industry": industry,
        "stage": stage,
        "ticket_size_min": ticket_size_min,
        "ticket_size_max": ticket_size_max,
        "location": location
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    investors = await startup_service.get_investors(filters)
    return investors


@router.get("/ecosystem/accelerators", response_model=List[EcosystemEntity], tags=["Ecosystem"])
async def get_accelerators(
    industry: Optional[str] = Query(None, description="Filter by industry focus"),
    stage: Optional[str] = Query(None, description="Filter by startup stage"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """
    **Get Accelerator Database**
    
    Discover accelerators and incubators in Kenya's startup ecosystem.
    """
    filters = {k: v for k, v in {
        "industry": industry,
        "stage": stage,
        "location": location
    }.items() if v is not None}
    
    accelerators = await startup_service.get_accelerators(filters)
    return accelerators


@router.get("/ecosystem/coworking", response_model=List[EcosystemEntity], tags=["Ecosystem"])
async def get_coworking_spaces(
    location: Optional[str] = Query(None, description="Filter by location"),
    amenities: Optional[str] = Query(None, description="Filter by amenities")
):
    """
     **Get Co-working Spaces**
    
    Find co-working spaces and innovation hubs across Kenya.
    """
    filters = {k: v for k, v in {
        "location": location,
        "amenities": amenities
    }.items() if v is not None}
    
    spaces = await startup_service.get_coworking_spaces(filters)
    return spaces


@router.get("/ecosystem/events", tags=["Ecosystem"])
async def get_upcoming_events(
    event_type: Optional[str] = Query(None, description="Type of event"),
    industry: Optional[str] = Query(None, description="Industry focus"),
    location: Optional[str] = Query(None, description="Event location")
):
    """
    **Get Upcoming Events**
    
    Discover networking events, conferences, and meetups.
    """
    filters = {k: v for k, v in {
        "event_type": event_type,
        "industry": industry,
        "location": location
    }.items() if v is not None}
    
    events = await startup_service.get_events(filters)
    return events


# MATCHING & RECOMMENDATIONS - Smart algorithms

@router.post("/matching/investors", tags=["Matching"])
async def match_investors(startup_profile: StartupProfile):
    """
    **Match with Investors**
    
    Get personalized investor recommendations based on your startup profile.
    
    **Matching criteria:**
    - Industry alignment
    - Stage preferences
    - Ticket size compatibility
    - Geographic preferences
    - Portfolio synergies
    """
    matches = await matching_service.match_investors(startup_profile)
    return {
        "matches": matches,
        "total_found": len(matches),
        "matching_criteria": matching_service.get_criteria_explanation(),
        "timestamp": get_current_timestamp()
    }


@router.post("/matching/accelerators", tags=["Matching"])
async def match_accelerators(startup_profile: StartupProfile):
    """
    **Match with Accelerators**
    
    Find accelerators that are perfect fit for your startup.
    """
    matches = await matching_service.match_accelerators(startup_profile)
    return {
        "matches": matches,
        "total_found": len(matches),
        "application_deadlines": await matching_service.get_application_deadlines(),
        "timestamp": get_current_timestamp()
    }


# ANALYTICS & INSIGHTS - Usage tracking

@router.get("/analytics/ecosystem", response_model=AnalyticsData, tags=["Analytics"])
async def get_ecosystem_analytics():
    """
    **Ecosystem Analytics**
    
    Get insights about Kenya's startup ecosystem trends and statistics.
    """
    analytics = await startup_service.get_ecosystem_analytics()
    return analytics


@router.get("/analytics/popular-queries", tags=["Analytics"])
async def get_popular_queries(limit: int = Query(10, description="Number of queries to return")):
    """
    **Popular Queries**
    
    See what questions other entrepreneurs are asking.
    """
    popular = await startup_service.get_popular_queries(limit)
    return {
        "popular_queries": popular,
        "total_queries_analyzed": await startup_service.get_total_query_count(),
        "timestamp": get_current_timestamp()
    }


# UTILITY FUNCTIONS - Background tasks and helpers

async def log_query_analytics(
    question: str, 
    startup_profile: Optional[Dict], 
    processing_time: float,
    confidence: float
):
    """
    Background task to log query analytics
    In production, this would write to a database or analytics service
    """
    analytics_data = {
        "question_length": len(question),
        "has_profile": startup_profile is not None,
        "processing_time": processing_time,
        "confidence": confidence,
        "timestamp": get_current_timestamp()
    }
    
    # In production, log to database or analytics service
    print(f"Analytics: {analytics_data}")


# ADMIN ENDPOINTS - For maintenance (optional)

@router.post("/admin/refresh-ecosystem-data", tags=["Admin"])
async def refresh_ecosystem_data(admin_key: str = Query(..., description="Admin authorization key")):
    """
    **Refresh Ecosystem Data**
    
    Manually trigger refresh of ecosystem database (admin only).
    """
    if admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Refresh data in background
    background_refresh = BackgroundTasks()
    background_refresh.add_task(startup_service.refresh_ecosystem_data)
    
    return {
        "status": "refresh_started",
        "message": "Ecosystem data refresh initiated",
        "timestamp": get_current_timestamp()
    }