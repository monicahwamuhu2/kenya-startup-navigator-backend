from typing import List, Dict, Any, Optional
import math
from datetime import datetime, timedelta

from app.models.schemas import (
    StartupProfile, InvestorProfile, EcosystemEntity, 
    MatchScore, InvestorMatch, RecommendationSet,
    Industry, StartupStage, Location
)


class MatchingService:
    """
    Intelligent matching service for startup ecosystem resources
    
    Uses sophisticated algorithms to match startups with:
    - Investors based on stage, industry, location, and ticket size
    - Accelerators based on program fit and timing
    - Co-working spaces based on location and amenities
    - Mentors and advisors based on expertise
    """
    
    def __init__(self):
        # Weights for different matching criteria
        self.investor_match_weights = {
            'industry_alignment': 0.30,
            'stage_fit': 0.25,
            'ticket_size_match': 0.20,
            'geographic_preference': 0.15,
            'portfolio_synergy': 0.10
        }
        
        self.accelerator_match_weights = {
            'industry_alignment': 0.35,
            'stage_fit': 0.30,
            'program_timing': 0.20,
            'location_preference': 0.15
        }
    
    async def match_investors(self, startup_profile: StartupProfile) -> List[InvestorMatch]:
        """
        Match startup with relevant investors using comprehensive scoring
        
        Args:
            startup_profile: Complete startup profile with all relevant information
            
        Returns:
            List of investor matches with detailed scoring and reasoning
        """
        # Import here to avoid circular imports
        from app.services.startup_service import StartupService
        startup_service = StartupService()
        
        # Get all investors
        all_investors = await startup_service.get_investors()
        
        matches = []
        for investor in all_investors:
            match_score = self._calculate_investor_match_score(startup_profile, investor)
            
            if match_score.overall_score > 0.3:  # Only include reasonable matches
                reasoning = self._generate_investor_match_reasoning(
                    startup_profile, investor, match_score
                )
                
                recommended_approach = self._generate_investor_approach_strategy(
                    startup_profile, investor, match_score
                )
                
                match = InvestorMatch(
                    investor=investor,
                    match_score=match_score,
                    reasoning=reasoning,
                    recommended_approach=recommended_approach,
                    warm_intro_available=self._check_warm_intro_possibility(startup_profile, investor)
                )
                matches.append(match)
        
        # Sort by overall score
        matches.sort(key=lambda x: x.match_score.overall_score, reverse=True)
        
        return matches[:10]  # Return top 10 matches
    
    def _calculate_investor_match_score(
        self, 
        startup: StartupProfile, 
        investor: InvestorProfile
    ) -> MatchScore:
        """Calculate detailed match score between startup and investor"""
        
        # 1. Industry Alignment
        industry_score = 0.0
        if startup.industry in investor.focus_industries:
            industry_score = 1.0
        elif len(investor.focus_industries) == 0:  # Generalist investor
            industry_score = 0.6
        
        # 2. Stage Fit
        stage_score = 0.0
        if startup.stage in investor.focus_stages:
            stage_score = 1.0
        else:
            # Calculate proximity of stages
            stage_order = [
                StartupStage.IDEA, StartupStage.MVP, StartupStage.PRE_SEED,
                StartupStage.SEED, StartupStage.SERIES_A, StartupStage.SERIES_B,
                StartupStage.GROWTH, StartupStage.MATURE
            ]
            
            try:
                startup_idx = stage_order.index(startup.stage)
                min_distance = min([
                    abs(startup_idx - stage_order.index(stage)) 
                    for stage in investor.focus_stages
                ])
                stage_score = max(0, 1.0 - (min_distance * 0.3))
            except ValueError:
                stage_score = 0.2
        
        # 3. Ticket Size Match
        ticket_score = 0.0
        if startup.funding_amount_target:
            target = startup.funding_amount_target
            if investor.ticket_size_min <= target <= investor.ticket_size_max:
                ticket_score = 1.0
            elif target < investor.ticket_size_min:
                # Too small - calculate how far off
                ratio = target / investor.ticket_size_min
                ticket_score = max(0, ratio * 0.7)  # Partial credit
            elif target > investor.ticket_size_max:
                # Too large - calculate how far off
                ratio = investor.ticket_size_max / target
                ticket_score = max(0, ratio * 0.8)  # Partial credit
        else:
            # No target specified, use stage-based estimation
            ticket_score = 0.6
        
        # 4. Geographic Preference
        geo_score = 0.0
        if startup.location in investor.geographic_focus:
            geo_score = 1.0
        elif Location.OTHER in investor.geographic_focus:  # Pan-African investor
            geo_score = 0.8
        else:
            geo_score = 0.3  # Still possible but lower priority
        
        # 5. Portfolio Synergy
        synergy_score = 0.0
        if investor.portfolio_companies:
            # Check for complementary companies in portfolio
            # This is simplified - in production you'd have more sophisticated analysis
            if len(investor.portfolio_companies) > 0:
                synergy_score = 0.6  # Assume some synergy potential
        else:
            synergy_score = 0.4  # New investor, less portfolio synergy
        
        # Calculate weighted overall score
        overall_score = (
            industry_score * self.investor_match_weights['industry_alignment'] +
            stage_score * self.investor_match_weights['stage_fit'] +
            ticket_score * self.investor_match_weights['ticket_size_match'] +
            geo_score * self.investor_match_weights['geographic_preference'] +
            synergy_score * self.investor_match_weights['portfolio_synergy']
        )
        
        return MatchScore(
            overall_score=overall_score,
            industry_alignment=industry_score,
            stage_fit=stage_score,
            ticket_size_match=ticket_score,
            geographic_preference=geo_score,
            portfolio_synergy=synergy_score
        )
    
    def _generate_investor_match_reasoning(
        self,
        startup: StartupProfile,
        investor: InvestorProfile,
        match_score: MatchScore
    ) -> str:
        """Generate human-readable reasoning for the match"""
        
        reasons = []
        
        # Industry alignment
        if match_score.industry_alignment >= 0.8:
            reasons.append(f"Strong industry fit - {investor.name} actively invests in {startup.industry.value}")
        elif match_score.industry_alignment >= 0.5:
            reasons.append(f"Good industry alignment with {investor.name}'s investment thesis")
        
        # Stage fit
        if match_score.stage_fit >= 0.8:
            reasons.append(f"Perfect stage match - focuses on {startup.stage.value} companies")
        elif match_score.stage_fit >= 0.5:
            reasons.append(f"Good stage alignment for {startup.stage.value} startups")
        
        # Ticket size
        if match_score.ticket_size_match >= 0.8:
            if startup.funding_amount_target:
                reasons.append(f"Ticket size ${startup.funding_amount_target:,} fits their investment range")
            else:
                reasons.append("Investment range aligns with typical funding needs for your stage")
        
        # Geographic preference
        if match_score.geographic_preference >= 0.8:
            reasons.append(f"Strong geographic focus on {startup.location.value}")
        
        # Portfolio synergy
        if match_score.portfolio_synergy >= 0.6 and investor.portfolio_companies:
            reasons.append(f"Portfolio synergies with companies like {', '.join(investor.portfolio_companies[:2])}")
        
        if not reasons:
            reasons.append("Potential fit based on overall investment profile")
        
        return ". ".join(reasons) + "."
    
    def _generate_investor_approach_strategy(
        self,
        startup: StartupProfile,
        investor: InvestorProfile,
        match_score: MatchScore
    ) -> str:
        """Generate recommended approach strategy for contacting investor"""
        
        if match_score.overall_score >= 0.8:
            return f"High-priority target. Research recent investments and reach out through warm introduction if possible. Highlight your {startup.industry.value} traction and {startup.location.value} market opportunity."
        
        elif match_score.overall_score >= 0.6:
            return f"Strong potential match. Prepare a compelling pitch deck focusing on market opportunity and business model. Consider attending events where {investor.name} partners speak."
        
        elif match_score.overall_score >= 0.4:
            return f"Worth exploring. Research their portfolio companies to understand investment patterns. Cold outreach with exceptional traction data may work."
        
        else:
            return "Lower priority match. Focus on building traction before approaching. Consider as backup option."
    
    def _check_warm_intro_possibility(
        self,
        startup: StartupProfile,
        investor: InvestorProfile
    ) -> bool:
        """Check if warm introduction might be possible (simplified logic)"""
        # In production, this would check actual network connections
        # For now, we'll use heuristics based on location and ecosystem
        
        if startup.location == Location.NAIROBI:
            # Nairobi has strong startup ecosystem with many connections
            return True
        
        if investor.name in ["Nairobi Angel Network", "iHub"]:
            # Local ecosystem players are more accessible
            return True
        
        return False
    
    async def match_accelerators(self, startup_profile: StartupProfile) -> List[Dict[str, Any]]:
        """
        Match startup with relevant accelerators
        
        Args:
            startup_profile: Complete startup profile
            
        Returns:
            List of accelerator matches with scoring and recommendations
        """
        from app.services.startup_service import StartupService
        startup_service = StartupService()
        
        all_accelerators = await startup_service.get_accelerators()
        
        matches = []
        for accelerator in all_accelerators:
            score = self._calculate_accelerator_match_score(startup_profile, accelerator)
            
            if score > 0.3:  # Only include reasonable matches
                match = {
                    "accelerator": accelerator,
                    "match_score": score,
                    "reasoning": self._generate_accelerator_reasoning(startup_profile, accelerator, score),
                    "application_status": self._get_application_status(accelerator),
                    "recommended_preparation": self._get_accelerator_prep_advice(startup_profile, accelerator)
                }
                matches.append(match)
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    def _calculate_accelerator_match_score(
        self,
        startup: StartupProfile,
        accelerator: EcosystemEntity
    ) -> float:
        """Calculate match score between startup and accelerator"""
        
        score = 0.0
        
    def _calculate_accelerator_match_score(
        self,
        startup: StartupProfile,
        accelerator: EcosystemEntity
    ) -> float:
        """Calculate match score between startup and accelerator"""
        
        score = 0.0
        
        # Industry alignment
        if startup.industry in accelerator.focus_industries:
            score += 0.35
        elif len(accelerator.focus_industries) == 0:  # Generalist accelerator
            score += 0.25
        
        # Stage fit
        if startup.stage in accelerator.focus_stages:
            score += 0.30
        elif StartupStage.IDEA in accelerator.focus_stages and startup.stage in [StartupStage.IDEA, StartupStage.MVP]:
            score += 0.25
        
        # Location preference
        if startup.location == accelerator.location:
            score += 0.15
        elif accelerator.location == Location.NAIROBI:  # Central hub
            score += 0.10
        
        # Program timing (simplified)
        if accelerator.application_deadline:
            days_until_deadline = (accelerator.application_deadline - datetime.now()).days
            if 30 <= days_until_deadline <= 180:  # Good timing window
                score += 0.20
            elif days_until_deadline > 0:  # Still time to apply
                score += 0.10
        else:
            score += 0.15  # Rolling applications
        
        return min(score, 1.0)
    
    def _generate_accelerator_reasoning(
        self,
        startup: StartupProfile,
        accelerator: EcosystemEntity,
        score: float
    ) -> str:
        """Generate reasoning for accelerator match"""
        
        reasons = []
        
        if startup.industry in accelerator.focus_industries:
            reasons.append(f"Strong focus on {startup.industry.value} startups")
        
        if startup.stage in accelerator.focus_stages:
            reasons.append(f"Perfect fit for {startup.stage.value} stage companies")
        
        if startup.location == accelerator.location:
            reasons.append(f"Located in {startup.location.value} for easy access")
        
        if accelerator.investment_amount:
            reasons.append(f"Provides ${accelerator.investment_amount:,} investment")
        
        if accelerator.program_duration_weeks:
            reasons.append(f"{accelerator.program_duration_weeks}-week structured program")
        
        if not reasons:
            reasons.append("General startup support and networking opportunities")
        
        return ". ".join(reasons) + "."
    
    def _get_application_status(self, accelerator: EcosystemEntity) -> str:
        """Get current application status for accelerator"""
        
        if accelerator.application_deadline:
            days_until = (accelerator.application_deadline - datetime.now()).days
            
            if days_until < 0:
                return "Applications closed - next cycle TBD"
            elif days_until <= 30:
                return f"Applications close in {days_until} days - apply soon!"
            elif days_until <= 90:
                return f"Applications open - {days_until} days remaining"
            else:
                return f"Early applications open - {days_until} days until deadline"
        else:
            return "Rolling applications - apply anytime"
    
    def _get_accelerator_prep_advice(
        self,
        startup: StartupProfile,
        accelerator: EcosystemEntity
    ) -> List[str]:
        """Get preparation advice for accelerator application"""
        
        advice = []
        
        if accelerator.name == "MEST Africa":
            advice.extend([
                "Prepare for rigorous technical assessment",
                "Demonstrate strong commitment to 12-month program",
                "Show potential for significant scale"
            ])
        elif accelerator.name == "Antler Kenya":
            advice.extend([
                "Be open to co-founder matching process",
                "Prepare for intensive 10-week program",
                "Focus on global scalability potential"
            ])
        elif accelerator.name == "iHub":
            advice.extend([
                "Demonstrate connection to Kenyan market",
                "Show early traction or strong validation",
                "Prepare for community-focused approach"
            ])
        else:
            advice.extend([
                "Prepare compelling pitch deck",
                "Demonstrate market validation",
                "Show team commitment and execution ability"
            ])
        
        return advice
    
    async def find_relevant_resources(
        self,
        startup_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find relevant ecosystem resources for a startup
        
        Args:
            startup_profile: Startup profile data
            
        Returns:
            List of relevant resources with brief descriptions
        """
        resources = []
        
        # Convert dict to StartupProfile if needed
        if isinstance(startup_profile, dict):
            try:
                profile = StartupProfile(**startup_profile)
            except Exception:
                # If conversion fails, return generic resources
                return self._get_generic_resources()
        else:
            profile = startup_profile
        
        # Get top investor matches
        investor_matches = await self.match_investors(profile)
        for match in investor_matches[:3]:  # Top 3
            resources.append({
                "type": "investor",
                "name": match.investor.name,
                "description": f"VC investing ${match.investor.ticket_size_min:,}-${match.investor.ticket_size_max:,}",
                "match_score": match.match_score.overall_score,
                "contact": match.investor.contact_info.website
            })
        
        # Get top accelerator matches
        accelerator_matches = await self.match_accelerators(profile)
        for match in accelerator_matches[:2]:  # Top 2
            resources.append({
                "type": "accelerator",
                "name": match["accelerator"].name,
                "description": match["accelerator"].description[:100] + "...",
                "match_score": match["match_score"],
                "contact": match["accelerator"].contact_info.website
            })
        
        return resources
    
    def _get_generic_resources(self) -> List[Dict[str, Any]]:
        """Get generic resources when profile parsing fails"""
        return [
            {
                "type": "accelerator",
                "name": "iHub",
                "description": "Kenya's premier technology hub and startup incubator",
                "match_score": 0.8,
                "contact": "https://ihub.co.ke"
            },
            {
                "type": "investor",
                "name": "Nairobi Angel Network", 
                "description": "Premier angel investor network in Kenya",
                "match_score": 0.7,
                "contact": "https://nairobiangels.ke"
            }
        ]
    
    async def generate_recommendations(self, startup_profile: StartupProfile) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations for a startup
        
        Args:
            startup_profile: Complete startup profile
            
        Returns:
            Dictionary with various recommendations and next steps
        """
        
        # Get matches
        investor_matches = await self.match_investors(startup_profile)
        accelerator_matches = await self.match_accelerators(startup_profile)
        
        # Generate stage-specific recommendations
        stage_recommendations = self._get_stage_recommendations(startup_profile)
        
        # Generate industry-specific advice
        industry_advice = self._get_industry_advice(startup_profile)
        
        return {
            "top_investors": [
                {
                    "name": match.investor.name,
                    "score": match.match_score.overall_score,
                    "reasoning": match.reasoning
                }
                for match in investor_matches[:3]
            ],
            "recommended_accelerators": [
                {
                    "name": match["accelerator"].name,
                    "score": match["match_score"],
                    "reasoning": match["reasoning"]
                }
                for match in accelerator_matches[:3]
            ],
            "stage_specific_advice": stage_recommendations,
            "industry_insights": industry_advice,
            "immediate_next_steps": self._get_immediate_next_steps(startup_profile),
            "long_term_strategy": self._get_long_term_strategy(startup_profile)
        }
    
    def _get_stage_recommendations(self, startup: StartupProfile) -> List[str]:
        """Get stage-specific recommendations"""
        
        recommendations = {
            StartupStage.IDEA: [
                "Focus on customer discovery and market validation",
                "Build a simple MVP to test core assumptions",
                "Join startup communities like iHub or NaiLab"
            ],
            StartupStage.MVP: [
                "Get your first paying customers",
                "Iterate based on user feedback", 
                "Consider pre-seed funding from angel investors"
            ],
            StartupStage.PRE_SEED: [
                "Scale customer acquisition and retention",
                "Build operational systems and processes",
                "Prepare for seed funding rounds"
            ],
            StartupStage.SEED: [
                "Focus on product-market fit and growth metrics",
                "Build strategic partnerships",
                "Prepare for Series A fundraising"
            ],
            StartupStage.SERIES_A: [
                "Scale operations across East Africa",
                "Build strong unit economics",
                "Consider expansion strategies"
            ]
        }
        
        return recommendations.get(startup.stage, ["Continue building and scaling your business"])
    
    def _get_industry_advice(self, startup: StartupProfile) -> List[str]:
        """Get industry-specific advice"""
        
        advice = {
            Industry.FINTECH: [
                "Understand CBK regulatory requirements and sandbox opportunities",
                "Build strong partnerships with traditional financial institutions",
                "Focus on mobile-first solutions for Kenya's high mobile penetration"
            ],
            Industry.AGRITECH: [
                "Connect with smallholder farmers through county governments",
                "Consider climate-smart agriculture solutions",
                "Explore partnerships with agricultural cooperatives"
            ],
            Industry.HEALTHTECH: [
                "Navigate healthcare regulations and certification requirements",
                "Partner with existing healthcare providers",
                "Consider telemedicine opportunities in rural areas"
            ],
            Industry.EDTECH: [
                "Work with Ministry of Education on curriculum alignment",
                "Focus on mobile and offline-capable solutions",
                "Consider partnerships with schools and universities"
            ]
        }
        
        return advice.get(startup.industry, ["Research industry best practices and regulations"])
    
    def _get_immediate_next_steps(self, startup: StartupProfile) -> List[str]:
        """Get immediate actionable next steps"""
        
        steps = []
        
        if not startup.website:
            steps.append("Create a professional website showcasing your product")
        
        if startup.seeking_funding and not startup.funding_amount_target:
            steps.append("Define specific funding amount and use of funds")
        
        if startup.team_size < 3 and startup.stage in [StartupStage.IDEA, StartupStage.MVP]:
            steps.append("Consider finding co-founders or key early employees")
        
        if not startup.monthly_revenue and startup.stage != StartupStage.IDEA:
            steps.append("Focus on generating first revenue or improving sales")
        
        steps.append("Register your business through eCitizen platform if not done")
        steps.append("Join relevant startup communities and networking events")
        
        return steps[:5]  # Limit to 5 most important
    
    def _get_long_term_strategy(self, startup: StartupProfile) -> List[str]:
        """Get long-term strategic recommendations"""
        
        return [
            "Build for regional expansion across East Africa",
            "Develop strong intellectual property protection",
            "Create sustainable competitive advantages",
            "Build strategic partnerships with established players",
            "Plan for multiple exit strategies (acquisition, IPO, etc.)"
        ]
    
    def get_criteria_explanation(self) -> Dict[str, str]:
        """Get explanation of matching criteria"""
        
        return {
            "industry_alignment": "How well the investor's focus industries match your startup's sector",
            "stage_fit": "Whether the investor typically invests in companies at your current stage",
            "ticket_size_match": "How well your funding needs align with their typical investment amounts",
            "geographic_preference": "Their focus on Kenya and East African markets",
            "portfolio_synergy": "Potential synergies with their existing portfolio companies"
        }
    
    async def get_application_deadlines(self) -> Dict[str, Any]:
        """Get upcoming application deadlines"""
        
        from app.services.startup_service import StartupService
        startup_service = StartupService()
        
        accelerators = await startup_service.get_accelerators()
        
        deadlines = []
        for acc in accelerators:
            if acc.application_deadline:
                days_until = (acc.application_deadline - datetime.now()).days
                if days_until > 0:
                    deadlines.append({
                        "name": acc.name,
                        "deadline": acc.application_deadline.strftime("%Y-%m-%d"),
                        "days_remaining": days_until,
                        "application_url": acc.application_url
                    })
        
        # Sort by deadline
        deadlines.sort(key=lambda x: x["days_remaining"])
        
        return {
            "upcoming_deadlines": deadlines,
            "total_opportunities": len(deadlines)
        }


# Export the service
__all__ = ["MatchingService"]