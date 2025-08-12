from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from app.models.schemas import (
    StartupProfile, InvestorProfile, EcosystemEntity, 
    AnalyticsData, Industry, StartupStage, Location, InvestorType
)


class StartupService:
    """
    Service for managing startup profiles and ecosystem data
    
    In production, this would interface with a real database.
    For the MVP, we'll use in-memory data with realistic Kenya ecosystem info.
    """
    
    def __init__(self):
        # Initialize with Kenya startup ecosystem data
        self.investors = self._load_kenya_investors()
        self.accelerators = self._load_kenya_accelerators()
        self.coworking_spaces = self._load_kenya_coworking()
        self.startup_profiles = {}  # Will store created profiles
        self.query_analytics = []   # Will store query analytics
    
    def _load_kenya_investors(self) -> List[InvestorProfile]:
        """Load realistic Kenya investor data"""
        from app.models.schemas import ContactInfo
        
        return [
            InvestorProfile(
                name="TLcom Capital",
                type=InvestorType.VC,
                focus_industries=[Industry.FINTECH, Industry.HEALTHTECH, Industry.LOGISTICS],
                focus_stages=[StartupStage.SEED, StartupStage.SERIES_A, StartupStage.SERIES_B],
                ticket_size_min=500000,
                ticket_size_max=15000000,
                geographic_focus=[Location.NAIROBI, Location.OTHER],
                description="Leading Africa-focused VC with $300M+ under management. Focus on scalable tech companies.",
                portfolio_companies=["Twiga Foods", "Sendy", "uLesson", "Gro Intelligence"],
                partners=["Maurizio Caio", "Andreata Muforo", "Omobola Johnson"],
                contact_info=ContactInfo(
                    email="info@tlcomcapital.com",
                    website="https://tlcomcapital.com",
                    linkedin="tlcom-capital"
                ),
                total_investments=45,
                successful_exits=8,
                founded_year=2016
            ),
            
            InvestorProfile(
                name="Novastar Ventures",
                type=InvestorType.VC,
                focus_industries=[Industry.FINTECH, Industry.AGRITECH, Industry.HEALTHTECH],
                focus_stages=[StartupStage.SEED, StartupStage.SERIES_A],
                ticket_size_min=250000,
                ticket_size_max=5000000,
                geographic_focus=[Location.NAIROBI, Location.OTHER],
                description="Early-stage VC focused on tech-enabled financial inclusion in Africa.",
                portfolio_companies=["Tala", "Apollo Agriculture", "Shortlist", "Kopo Kopo"],
                partners=["Steve Beck", "Carla Jooste"],
                contact_info=ContactInfo(
                    email="info@novastar.vc",
                    website="https://novastar.vc",
                    linkedin="novastar-ventures"
                ),
                total_investments=35,
                successful_exits=5,
                founded_year=2018
            ),
            
            InvestorProfile(
                name="GreenTec Capital",
                type=InvestorType.VC,
                focus_industries=[Industry.CLEANTECH, Industry.AGRITECH, Industry.FINTECH],
                focus_stages=[StartupStage.PRE_SEED, StartupStage.SEED],
                ticket_size_min=50000,
                ticket_size_max=2000000,
                geographic_focus=[Location.NAIROBI, Location.OTHER],
                description="Impact-driven VC investing in sustainable technology solutions for Africa.",
                portfolio_companies=["M-KOPA", "PayGo Energy", "Solar Freeze"],
                partners=["Matthias Hopf", "Eric Schöneich"],
                contact_info=ContactInfo(
                    email="info@greentec-capital.com",
                    website="https://greentec-capital.com",
                    linkedin="greentec-capital"
                ),
                total_investments=28,
                successful_exits=6,
                founded_year=2014
            ),
            
            InvestorProfile(
                name="Nairobi Angel Network",
                type=InvestorType.ANGEL,
                focus_industries=[Industry.FINTECH, Industry.EDTECH, Industry.ECOMMERCE],
                focus_stages=[StartupStage.IDEA, StartupStage.MVP, StartupStage.PRE_SEED],
                ticket_size_min=10000,
                ticket_size_max=250000,
                geographic_focus=[Location.NAIROBI],
                description="Premier angel investor network in Kenya, connecting local entrepreneurs with investors.",
                portfolio_companies=["Sendy", "Lynk", "Kune Food"],
                partners=["Local Angel Investors"],
                contact_info=ContactInfo(
                    email="info@nairobiangels.ke",
                    website="https://nairobiangels.ke",
                    linkedin="nairobi-angel-network"
                ),
                total_investments=60,
                successful_exits=12,
                founded_year=2015
            )
        ]
    
    def _load_kenya_accelerators(self) -> List[EcosystemEntity]:
        """Load realistic Kenya accelerator data"""
        from app.models.schemas import ContactInfo
        
        return [
            EcosystemEntity(
                name="iHub",
                type="Tech Hub",
                description="Kenya's premier technology hub and startup incubator, supporting tech entrepreneurs since 2010.",
                location=Location.NAIROBI,
                address="Ngong Road, Nairobi",
                focus_industries=[Industry.FINTECH, Industry.HEALTHTECH, Industry.EDTECH],
                focus_stages=[StartupStage.IDEA, StartupStage.MVP, StartupStage.PRE_SEED],
                services=["Incubation", "Co-working", "Mentorship", "Funding Connections"],
                amenities=["High-speed Internet", "Meeting Rooms", "Event Space", "Cafe"],
                program_duration_weeks=12,
                equity_taken=0.0,
                investment_amount=25000,
                contact_info=ContactInfo(
                    email="info@ihub.co.ke",
                    website="https://ihub.co.ke",
                    linkedin="ihub-nairobi"
                ),
                portfolio_companies=["Ushahidi", "BRCK", "Eneza Education"],
                founded_year=2010
            ),
            
            EcosystemEntity(
                name="MEST Africa",
                type="Accelerator",
                description="12-month accelerator program training software entrepreneurs and providing seed funding.",
                location=Location.NAIROBI,
                address="Westlands, Nairobi",
                focus_industries=[Industry.FINTECH, Industry.EDTECH, Industry.HEALTHTECH],
                focus_stages=[StartupStage.IDEA, StartupStage.MVP],
                services=["Training Program", "Seed Funding", "Mentorship", "Demo Day"],
                amenities=["Full-time Program", "Stipend", "Workspace", "Networking"],
                program_duration_weeks=52,
                equity_taken=20.0,
                investment_amount=50000,
                application_deadline=datetime(2024, 12, 31),
                application_url="https://meltwater.org/mest/apply/",
                contact_info=ContactInfo(
                    email="info@meltwater.org",
                    website="https://meltwater.org/mest/",
                    linkedin="mest-africa"
                ),
                portfolio_companies=["Nandi", "Chura", "Asoriba"],
                founded_year=2008
            ),
            
            EcosystemEntity(
                name="Antler Kenya",
                type="Accelerator",
                description="Global early-stage VC building startups from day zero with exceptional founders.",
                location=Location.NAIROBI,
                address="Westlands, Nairobi",
                focus_industries=[Industry.FINTECH, Industry.LOGISTICS, Industry.HEALTHTECH],
                focus_stages=[StartupStage.IDEA, StartupStage.MVP],
                services=["Co-founder Matching", "Idea Development", "Seed Investment", "Global Network"],
                amenities=["Residency Program", "Expert Mentors", "Global Alumni Network"],
                program_duration_weeks=10,
                equity_taken=9.0,
                investment_amount=100000,
                contact_info=ContactInfo(
                    email="kenya@antler.co",
                    website="https://antler.co/kenya",
                    linkedin="antler_co"
                ),
                portfolio_companies=["Ilara Health", "Kwara", "OkHi"],
                founded_year=2021
            )
        ]
    
    def _load_kenya_coworking(self) -> List[EcosystemEntity]:
        """Load realistic Kenya co-working space data"""
        from app.models.schemas import ContactInfo
        
        return [
            EcosystemEntity(
                name="NaiLab",
                type="Co-working Space",
                description="Premium co-working space and startup community in Kilimani, Nairobi.",
                location=Location.NAIROBI,
                address="Kilimani, Nairobi",
                focus_industries=[Industry.FINTECH, Industry.EDTECH, Industry.ECOMMERCE],
                services=["Co-working", "Private Offices", "Meeting Rooms", "Events"],
                amenities=["High-speed WiFi", "Printing", "Kitchen", "Parking", "Security"],
                contact_info=ContactInfo(
                    email="info@nailab.co.ke",
                    website="https://nailab.co.ke",
                    linkedin="nailab"
                ),
                founded_year=2011
            ),
            
            EcosystemEntity(
                name="GrowthHub Africa",
                type="Co-working Space",
                description="Modern co-working space with focus on scaling African startups.",
                location=Location.NAIROBI,
                address="Westlands, Nairobi",
                focus_industries=[Industry.FINTECH, Industry.LOGISTICS, Industry.HEALTHTECH],
                services=["Hot Desks", "Dedicated Desks", "Private Offices", "Virtual Offices"],
                amenities=["24/7 Access", "High-speed Internet", "Conference Rooms", "Cafe"],
                contact_info=ContactInfo(
                    email="hello@growthhub.africa",
                    website="https://growthhub.africa",
                    linkedin="growthhub-africa"
                ),
                founded_year=2018
            )
        ]
    
    # Service Methods
    async def create_profile(self, profile: StartupProfile) -> StartupProfile:
        """Create a new startup profile"""
        # In production, save to database
        profile_id = f"startup_{len(self.startup_profiles) + 1}"
        profile.created_at = datetime.now()
        profile.updated_at = datetime.now()
        
        # Add ID to profile (in production this would be handled by DB)
        profile_dict = profile.dict()
        profile_dict['id'] = profile_id
        
        self.startup_profiles[profile_id] = profile_dict
        return profile
    
    async def get_profile(self, profile_id: str) -> Optional[StartupProfile]:
        """Get startup profile by ID"""
        profile_data = self.startup_profiles.get(profile_id)
        if profile_data:
            return StartupProfile(**profile_data)
        return None
    
    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> StartupProfile:
        """Update startup profile"""
        if profile_id not in self.startup_profiles:
            raise ValueError("Profile not found")
        
        profile_data = self.startup_profiles[profile_id]
        profile_data.update(updates)
        profile_data['updated_at'] = datetime.now()
        
        return StartupProfile(**profile_data)
    
    async def get_investors(self, filters: Dict[str, Any] = None) -> List[InvestorProfile]:
        """Get investors with optional filters"""
        investors = self.investors
        
        if filters:
            # Apply filters
            if filters.get('industry'):
                investors = [
                    inv for inv in investors 
                    if filters['industry'] in [ind.value for ind in inv.focus_industries]
                ]
            
            if filters.get('stage'):
                investors = [
                    inv for inv in investors 
                    if filters['stage'] in [stage.value for stage in inv.focus_stages]
                ]
            
            if filters.get('ticket_size_min'):
                investors = [
                    inv for inv in investors 
                    if inv.ticket_size_max >= filters['ticket_size_min']
                ]
            
            if filters.get('ticket_size_max'):
                investors = [
                    inv for inv in investors 
                    if inv.ticket_size_min <= filters['ticket_size_max']
                ]
        
        return investors
    
    async def get_accelerators(self, filters: Dict[str, Any] = None) -> List[EcosystemEntity]:
        """Get accelerators with optional filters"""
        accelerators = self.accelerators
        
        if filters:
            if filters.get('industry'):
                accelerators = [
                    acc for acc in accelerators 
                    if filters['industry'] in [ind.value for ind in acc.focus_industries]
                ]
            
            if filters.get('location'):
                accelerators = [
                    acc for acc in accelerators 
                    if acc.location.value == filters['location']
                ]
        
        return accelerators
    
    async def get_coworking_spaces(self, filters: Dict[str, Any] = None) -> List[EcosystemEntity]:
        """Get co-working spaces with optional filters"""
        spaces = self.coworking_spaces
        
        if filters:
            if filters.get('location'):
                spaces = [
                    space for space in spaces 
                    if space.location.value == filters['location']
                ]
        
        return spaces
    
    async def get_events(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get upcoming events (mock data for now)"""
        # Mock events data
        events = [
            {
                "name": "Nairobi Tech Week",
                "date": "2024-10-15",
                "location": "Nairobi",
                "type": "Conference",
                "description": "Annual technology conference bringing together East Africa's tech community",
                "website": "https://nairotechweek.com"
            },
            {
                "name": "Startup Grind Nairobi",
                "date": "2024-09-20",
                "location": "Nairobi",
                "type": "Networking",
                "description": "Monthly startup networking event with local entrepreneurs",
                "website": "https://startupgrind.com/nairobi"
            }
        ]
        
        return events
    
    def generate_next_steps(self, profile: StartupProfile) -> List[str]:
        """Generate next steps based on startup profile"""
        steps = []
        
        if profile.stage == StartupStage.IDEA:
            steps.extend([
                "Validate your idea with potential customers",
                "Build a minimum viable product (MVP)",
                "Join a local accelerator like iHub or MEST"
            ])
        elif profile.stage == StartupStage.MVP:
            steps.extend([
                "Get your first paying customers",
                "Apply to pre-seed investors like Nairobi Angel Network",
                "Register your business with eCitizen platform"
            ])
        elif profile.stage == StartupStage.SEED:
            steps.extend([
                "Scale your customer acquisition",
                "Approach VCs like TLcom Capital or Novastar",
                "Build strategic partnerships"
            ])
        
        return steps
    
    async def get_ecosystem_analytics(self) -> AnalyticsData:
        """Get ecosystem analytics and insights"""
        return AnalyticsData(
            total_queries=len(self.query_analytics),
            avg_processing_time=2.3,
            avg_confidence_score=0.85,
            popular_categories={
                "funding": 45,
                "legal": 23,
                "market": 18,
                "ecosystem": 14
            },
            total_investors=len(self.investors),
            total_accelerators=len(self.accelerators),
            total_startups_profiled=len(self.startup_profiles),
            trending_industries=["fintech", "agritech", "healthtech"],
            recent_funding_activity={
                "total_rounds": 12,
                "total_amount": 25000000,
                "avg_round_size": 2083333
            },
            user_satisfaction_score=4.2,
            generated_at=datetime.now(),
            data_period="Last 30 days"
        )
    
    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular queries"""
        # Mock popular queries
        return [
            {"query": "How to raise seed funding in Kenya", "count": 24},
            {"query": "Best accelerators in Nairobi", "count": 18},
            {"query": "Kenya business registration process", "count": 15},
            {"query": "Fintech regulations in Kenya", "count": 12},
            {"query": "How to find co-founders", "count": 10}
        ]
    
    async def get_total_query_count(self) -> int:
        """Get total number of queries processed"""
        return len(self.query_analytics)
    
    async def refresh_ecosystem_data(self):
        """Refresh ecosystem data (background task)"""
        # In production, this would fetch fresh data from external sources
        await asyncio.sleep(1)  # Simulate data refresh
        print("Ecosystem data refreshed successfully")


# Export the service
__all__ = ["StartupService"]