from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ENUMS - Standardized choices


class StartupStage(str, Enum):
    """Standardized startup stages for Kenya's ecosystem"""
    IDEA = "idea"
    MVP = "mvp"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    GROWTH = "growth"
    MATURE = "mature"


class Industry(str, Enum):
    """Key industry sectors in Kenya's startup ecosystem"""
    FINTECH = "fintech"
    AGRITECH = "agritech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    ECOMMERCE = "ecommerce"
    LOGISTICS = "logistics"
    CLEANTECH = "cleantech"
    PROPTECH = "proptech"
    BLOCKCHAIN = "blockchain"
    AI_ML = "ai_ml"
    MEDIA = "media"
    RETAIL = "retail"
    OTHER = "other"


class InvestorType(str, Enum):
    """Types of investors in the ecosystem"""
    ANGEL = "angel"
    VC = "vc"
    CORPORATE_VC = "corporate_vc"
    GOVERNMENT = "government"
    DEVELOPMENT_FINANCE = "development_finance"
    CROWDFUNDING = "crowdfunding"
    GRANT = "grant"


class Location(str, Enum):
    """Key locations in Kenya's startup ecosystem"""
    NAIROBI = "nairobi"
    MOMBASA = "mombasa"
    KISUMU = "kisumu"
    ELDORET = "eldoret"
    NAKURU = "nakuru"
    MERU = "meru"
    NYERI = "nyeri"
    OTHER = "other"


# CORE REQUEST/RESPONSE MODELS - API contracts

class QueryRequest(BaseModel):
    """
    Request model for AI query processing
    
    This is what the frontend sends when a user asks a question
    """
    question: str = Field(
        ..., 
        min_length=5, 
        max_length=2000,
        description="The user's question about Kenya's startup ecosystem",
        example="How do I raise seed funding for my fintech startup in Nairobi?"
    )
    
    startup_profile: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional startup profile for personalized responses"
    )
    
    context: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional context or follow-up information",
        example="I'm a first-time founder with a team of 3 developers"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation tracking"
    )

    @validator('question')
    def validate_question(cls, v):
        """Ensure question is meaningful and clean"""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        return v


class AIResponse(BaseModel):
    """Internal model for AI service responses"""
    content: str = Field(..., description="The AI-generated response content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the response")
    sources: List[str] = Field(default=[], description="Sources used for the response")
    suggested_questions: List[str] = Field(default=[], description="Suggested follow-up questions")


class QueryResponse(BaseModel):
    """
    Response model for processed queries
    
    This is what gets sent back to the frontend
    """
    answer: str = Field(..., description="AI-generated answer to the question")
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score for the response (0.0 to 1.0)"
    )
    
    processing_time: float = Field(
        ..., 
        description="Time taken to process the query in seconds"
    )
    
    sources: List[str] = Field(
        default=[],
        description="Sources and references used in the response"
    )
    
    related_resources: List[Dict[str, Any]] = Field(
        default=[],
        description="Relevant ecosystem resources (investors, accelerators, etc.)"
    )
    
    suggested_follow_ups: List[str] = Field(
        default=[],
        description="Suggested follow-up questions",
        example=[
            "What documents do I need to prepare for investors?",
            "How long does the fundraising process typically take?",
            "What valuation should I expect at seed stage?"
        ]
    )
    
    timestamp: str = Field(
        ...,
        description="When the response was generated"
    )


# STARTUP PROFILE MODELS - User data structures

class TeamMember(BaseModel):
    """Individual team member information"""
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., description="Role in the company")
    experience_years: int = Field(..., ge=0, le=50)
    skills: List[str] = Field(default=[], description="Key skills and expertise")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")


class FundingRound(BaseModel):
    """Information about a funding round"""
    round_type: str = Field(..., description="Type of funding round")
    amount: float = Field(..., gt=0, description="Amount raised in USD")
    date: datetime = Field(..., description="Date of the funding round")
    investors: List[str] = Field(default=[], description="List of investors")
    valuation: Optional[float] = Field(None, description="Company valuation at the time")


class StartupProfile(BaseModel):
    """
    Comprehensive startup profile for personalized recommendations
    
    This model captures all relevant information about a startup
    for intelligent matching and advice generation
    """
    # Basic Company Information
    company_name: str = Field(..., min_length=2, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200, description="One-line company description")
    description: str = Field(..., min_length=10, max_length=1000, description="Detailed company description")
    
    # Business Details
    industry: Industry = Field(..., description="Primary industry sector")
    stage: StartupStage = Field(..., description="Current startup stage")
    location: Location = Field(..., description="Primary business location")
    
    # Team Information
    team_size: int = Field(..., ge=1, le=1000, description="Total number of employees")
    founding_team: List[TeamMember] = Field(
        default=[],
        description="Information about founding team members"
    )
    
    # Business Model
    revenue_model: str = Field(..., description="How the company makes money")
    target_market: str = Field(..., description="Primary target market and customers")
    competitive_advantage: str = Field(..., description="What makes the company unique")
    
    # Financial Information
    monthly_revenue: Optional[float] = Field(None, ge=0, description="Current monthly revenue in USD")
    monthly_burn_rate: Optional[float] = Field(None, ge=0, description="Monthly expenses in USD")
    runway_months: Optional[int] = Field(None, ge=0, description="Months of runway remaining")
    
    # Funding History
    funding_history: List[FundingRound] = Field(
        default=[],
        description="Previous funding rounds"
    )
    
    # Current Needs
    seeking_funding: bool = Field(default=False, description="Currently seeking investment")
    funding_amount_target: Optional[float] = Field(None, description="Target funding amount in USD")
    funding_use_case: Optional[str] = Field(None, description="How funding will be used")
    
    # Metrics and Traction
    key_metrics: Dict[str, Any] = Field(
        default={},
        description="Key business metrics and KPIs"
    )
    
    # External Links
    website: Optional[str] = Field(None, description="Company website")
    pitch_deck_url: Optional[str] = Field(None, description="Link to pitch deck")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('website')
    def validate_website(cls, v):
        """Basic website URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            v = f"https://{v}"
        return v


# ECOSYSTEM ENTITY MODELS - External resources


class ContactInfo(BaseModel):
    """Contact information for ecosystem entities"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None


class InvestorProfile(BaseModel):
    """
    Comprehensive investor profile for matching algorithms
    """
    name: str = Field(..., description="Investor or firm name")
    type: InvestorType = Field(..., description="Type of investor")
    
    # Investment Preferences
    focus_industries: List[Industry] = Field(..., description="Industries they invest in")
    focus_stages: List[StartupStage] = Field(..., description="Stages they invest in")
    
    # Investment Details
    ticket_size_min: int = Field(..., ge=0, description="Minimum investment amount in USD")
    ticket_size_max: int = Field(..., ge=0, description="Maximum investment amount in USD")
    
    # Geographic Preferences
    geographic_focus: List[Location] = Field(..., description="Geographic regions of interest")
    
    # Firm Details
    description: str = Field(..., description="Investor description and thesis")
    portfolio_companies: List[str] = Field(default=[], description="Notable portfolio companies")
    partners: List[str] = Field(default=[], description="Key partners or decision makers")
    
    # Contact and Social
    contact_info: ContactInfo = Field(..., description="Contact information")
    
    # Performance Metrics
    total_investments: Optional[int] = Field(None, description="Total number of investments")
    successful_exits: Optional[int] = Field(None, description="Number of successful exits")
    
    # Metadata
    founded_year: Optional[int] = Field(None, ge=1900, le=2030)
    last_active: Optional[datetime] = Field(None, description="Last known activity")


class EcosystemEntity(BaseModel):
    """
    Generic model for ecosystem entities (accelerators, co-working spaces, etc.)
    """
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Type of entity")
    description: str = Field(..., description="Detailed description")
    
    # Location Information
    location: Location = Field(..., description="Primary location")
    address: Optional[str] = Field(None, description="Physical address")
    
    # Focus Areas
    focus_industries: List[Industry] = Field(default=[], description="Industry focus areas")
    focus_stages: List[StartupStage] = Field(default=[], description="Stage focus areas")
    
    # Services and Offerings
    services: List[str] = Field(default=[], description="Services offered")
    amenities: List[str] = Field(default=[], description="Available amenities")
    
    # Program Details (for accelerators)
    program_duration_weeks: Optional[int] = Field(None, description="Program duration in weeks")
    equity_taken: Optional[float] = Field(None, ge=0, le=100, description="Equity percentage taken")
    investment_amount: Optional[int] = Field(None, description="Investment provided in USD")
    
    # Application Information
    application_deadline: Optional[datetime] = Field(None, description="Next application deadline")
    application_url: Optional[str] = Field(None, description="Application link")
    
    # Contact Information
    contact_info: ContactInfo = Field(..., description="Contact information")
    
    # Success Metrics
    portfolio_companies: List[str] = Field(default=[], description="Portfolio or alumni companies")
    success_stories: List[str] = Field(default=[], description="Notable success stories")
    
    # Metadata
    founded_year: Optional[int] = Field(None, ge=1900, le=2030)
    last_updated: datetime = Field(default_factory=datetime.now)


# ANALYTICS AND REPORTING MODELS


class QueryAnalytics(BaseModel):
    """Analytics data for individual queries"""
    question_category: str = Field(..., description="Categorized topic of the question")
    processing_time: float = Field(..., description="Time to process in seconds")
    confidence_score: float = Field(..., description="AI confidence in the response")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating of the response")
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalyticsData(BaseModel):
    """
    Comprehensive analytics and insights about the ecosystem
    """
    # Query Statistics
    total_queries: int = Field(..., description="Total number of queries processed")
    avg_processing_time: float = Field(..., description="Average query processing time")
    avg_confidence_score: float = Field(..., description="Average AI confidence score")
    
    # Popular Topics
    popular_categories: Dict[str, int] = Field(
        ..., 
        description="Most popular query categories and their counts"
    )
    
    # Ecosystem Statistics
    total_investors: int = Field(..., description="Total investors in database")
    total_accelerators: int = Field(..., description="Total accelerators in database")
    total_startups_profiled: int = Field(..., description="Total startup profiles created")
    
    # Trending Data
    trending_industries: List[str] = Field(..., description="Currently trending industries")
    recent_funding_activity: Dict[str, Any] = Field(..., description="Recent funding trends")
    
    # Performance Metrics
    user_satisfaction_score: float = Field(
        ..., 
        ge=0, 
        le=5, 
        description="Average user satisfaction rating"
    )
    
    # Temporal Data
    generated_at: datetime = Field(default_factory=datetime.now)
    data_period: str = Field(..., description="Time period for the analytics")


# MATCHING AND RECOMMENDATION MODELS


class MatchScore(BaseModel):
    """Detailed scoring for startup-investor matches"""
    overall_score: float = Field(..., ge=0, le=1, description="Overall match score")
    industry_alignment: float = Field(..., ge=0, le=1, description="Industry alignment score")
    stage_fit: float = Field(..., ge=0, le=1, description="Stage compatibility score")
    ticket_size_match: float = Field(..., ge=0, le=1, description="Ticket size compatibility")
    geographic_preference: float = Field(..., ge=0, le=1, description="Geographic alignment")
    portfolio_synergy: float = Field(..., ge=0, le=1, description="Portfolio synergy potential")


class InvestorMatch(BaseModel):
    """Investor recommendation with matching details"""
    investor: InvestorProfile = Field(..., description="Investor information")
    match_score: MatchScore = Field(..., description="Detailed match scoring")
    reasoning: str = Field(..., description="Explanation of why this is a good match")
    recommended_approach: str = Field(..., description="Suggested approach for outreach")
    warm_intro_available: bool = Field(default=False, description="Whether warm intro is possible")


class RecommendationSet(BaseModel):
    """Set of recommendations for a startup"""
    startup_profile_id: str = Field(..., description="ID of the startup profile")
    investor_matches: List[InvestorMatch] = Field(..., description="Matched investors")
    accelerator_matches: List[Dict[str, Any]] = Field(..., description="Matched accelerators")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    generated_at: datetime = Field(default_factory=datetime.now)


# ERROR AND STATUS MODELS

class ErrorResponse(BaseModel):
    """Standardized error response format"""
    error: bool = Field(default=True, description="Indicates this is an error response")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="When the error occurred")
    path: Optional[str] = Field(None, description="API endpoint that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standardized success response format"""
    success: bool = Field(default=True, description="Indicates successful operation")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: str = Field(..., description="When the operation completed")


# EXPORT ALL MODELS
__all__ = [
    # Enums
    "StartupStage", "Industry", "InvestorType", "Location",
    
    # Request/Response Models
    "QueryRequest", "QueryResponse", "AIResponse",
    
    # Business Models
    "StartupProfile", "TeamMember", "FundingRound",
    "InvestorProfile", "EcosystemEntity", "ContactInfo",
    
    # Analytics Models
    "QueryAnalytics", "AnalyticsData",
    
    # Matching Models
    "MatchScore", "InvestorMatch", "RecommendationSet",
    
    # Utility Models
    "ErrorResponse", "SuccessResponse"
]