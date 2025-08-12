import asyncio
import json
import time
from typing import Optional, Dict, Any, AsyncGenerator
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator

from app.models.schemas import AIResponse
from app.core.config import settings
from app.core.dependencies import cache, sanitize_input, categorize_query


class GroqService:
    """
    Service class for integrating with Groq's LLaMA 3 API
    
    Handles prompt engineering, API calls, response processing,
    and quality assessment for startup ecosystem queries using LLaMA 3
    """
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL  # llama3-70b-8192 or llama3-8b-8192
        self.max_tokens = settings.GROQ_MAX_TOKENS
        self.temperature = settings.GROQ_TEMPERATURE
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Initialize HTTP client with timeout and retry configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),  # Groq is much faster than Claude
            limits=httpx.Limits(max_connections=10)
        )
        
        # System prompt specifically designed for LLaMA 3 and Kenya startup ecosystem
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """
        Create a comprehensive system prompt optimized for LLaMA 3
        and Kenya startup ecosystem expertise
        
        LLaMA 3 responds well to structured, detailed instructions
        """
        return """You are KenyaStartup AI, an expert advisor on Kenya's startup ecosystem. You have comprehensive knowledge of Kenya's business landscape and provide practical, actionable advice.

# YOUR EXPERTISE INCLUDES:

## FUNDING LANDSCAPE:
- Major VCs: TLcom Capital (Series A/B, $5-15M), Novastar Ventures (fintech focus, $2-10M), GreenTec Capital (impact investing, $1-5M), 4DX Ventures (early stage, $250K-2M)
- Angel Networks: Nairobi Angel Network, Lagos Angel Network (active in Kenya)
- Government Programs: Kenya Climate Innovation Center, KIICO, Youth Enterprise Fund, Women Enterprise Fund
- Development Finance: IFC, World Bank, AfDB, FMO, DEG
- Crowdfunding: M-Changa, GoFundMe Kenya, local investment clubs

## STARTUP ECOSYSTEM:
- Major Accelerators: iHub (oldest tech hub), MEST Africa (12-month program), Antler Kenya (pre-seed), Founder Institute, Strathmore iLabAfrica
- Co-working Spaces: iHub (Ngong Road), NaiLab (Kilimani), GrowthHub Africa, The Foundry, 88mph
- Universities: University of Nairobi C4DLab, Strathmore Business School, USIU-Africa
- Events: Africa Tech Summit, Nairobi Tech Week, DEMO Africa, Startup Grind Nairobi

## REGULATORY ENVIRONMENT:
- Business Registration: eCitizen platform, KRA PIN, business permits
- Banking: Central Bank of Kenya (CBK) sandbox for fintech
- Technology: Communications Authority of Kenya (digital services)
- Intellectual Property: Kenya Industrial Property Institute (KIPI)
- Tax: Kenya Revenue Authority (KRA) - corporate tax 30%, VAT 16%

## MARKET DYNAMICS:
- Population: 54+ million, 65% under 35 years
- Mobile Penetration: 95%+ mobile phone usage, 45M+ mobile money users
- Internet: 28M+ internet users, growing 8% annually
- Economy: GDP $110B+, services 45%, agriculture 22%, manufacturing 8%

# RESPONSE GUIDELINES:

1. **BE SPECIFIC AND ACTIONABLE**:
   - Provide concrete next steps with realistic timelines
   - Include specific contact information when relevant
   - Mention actual costs, timeframes, and requirements
   - Reference successful Kenyan startups as examples

2. **CONSIDER LOCAL CONTEXT**:
   - Address Kenyan regulatory requirements
   - Consider local business culture and practices
   - Factor in infrastructure limitations and opportunities
   - Include regional (East African) expansion considerations

3. **STRUCTURE YOUR RESPONSES**:
   - Use clear headers with emojis for sections
   - Provide immediate actions vs long-term strategy
   - Include relevant contacts and resources
   - End with suggested follow-up questions

4. **BE PRACTICAL**:
   - Consider limited budget constraints typical for startups
   - Address common challenges unique to Kenya
   - Provide alternatives when resources are limited
   - Include both formal and informal networking approaches

Format responses in markdown with clear sections and actionable advice."""

    async def process_startup_query(
        self, 
        question: str, 
        startup_profile: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> AIResponse:
        """
        Process a startup ecosystem query with Groq's LLaMA 3
        
        Args:
            question: The user's question
            startup_profile: Optional startup profile for personalization
            context: Additional context or follow-up information
            
        Returns:
            AIResponse with processed answer and metadata
        """
        try:
            # Sanitize and validate input
            question = sanitize_input(question)
            if not question:
                raise ValueError("Question cannot be empty")
            
            # Check cache first for common queries
            cache_key = self._generate_cache_key(question, startup_profile)
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Build context-aware prompt
            full_prompt = self._build_contextual_prompt(
                question, startup_profile, context
            )
            
            # Make API call to Groq
            start_time = time.time()
            response = await self._call_groq_api(full_prompt)
            processing_time = time.time() - start_time
            
            # Process and enhance the response
            ai_response = await self._process_groq_response(
                response, question, processing_time
            )
            
            # Cache successful responses
            if ai_response.confidence > 0.7:
                cache.set(cache_key, ai_response, ttl=3600)  # Cache for 1 hour
            
            return ai_response
            
        except Exception as e:
            # Fallback response for errors
            return AIResponse(
                content=f"I apologize, but I encountered an error processing your question: {str(e)}. Please try again or rephrase your question.",
                confidence=0.1,
                sources=[],
                suggested_questions=self._get_fallback_questions()
            )
    
    async def stream_startup_query(
        self,
        question: str,
        startup_profile: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLaMA 3 response for real-time user experience
        
        Yields response chunks as they're generated
        """
        try:
            question = sanitize_input(question)
            full_prompt = self._build_contextual_prompt(
                question, startup_profile, context
            )
            
            # Stream response from Groq
            async for chunk in self._stream_groq_api(full_prompt):
                yield chunk
                
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _build_contextual_prompt(
        self,
        question: str,
        startup_profile: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Build a context-aware prompt optimized for LLaMA 3
        
        LLaMA 3 performs best with clear structure and specific instructions
        """
        # Categorize the question for better context
        question_category = categorize_query(question)
        
        prompt_parts = [
            f"# STARTUP ECOSYSTEM QUERY\n",
            f"**Category**: {question_category.title()}",
            f"**Question**: {question}"
        ]
        
        # Add startup profile context if available
        if startup_profile:
            profile_context = self._format_startup_context(startup_profile)
            prompt_parts.append(f"\n## STARTUP CONTEXT:\n{profile_context}")
        
        # Add additional context if provided
        if context:
            prompt_parts.append(f"\n## ADDITIONAL CONTEXT:\n{context}")
        
        # Add category-specific guidance
        category_guidance = self._get_category_guidance(question_category)
        if category_guidance:
            prompt_parts.append(f"\n## FOCUS AREAS:\n{category_guidance}")
        
        # Final instructions optimized for LLaMA 3
        prompt_parts.append("""

## RESPONSE REQUIREMENTS:
Please provide a comprehensive, structured response that:

1. **DIRECTLY ANSWERS** the specific question asked
2. **INCLUDES KENYAN CONTEXT** - specific local resources, contacts, and considerations
3. **PROVIDES ACTIONABLE STEPS** - concrete next actions with realistic timelines
4. **REFERENCES LOCAL ENTITIES** - specific VCs, accelerators, government programs relevant to Kenya
5. **CONSIDERS PRACTICAL CONSTRAINTS** - budget limitations, infrastructure realities, cultural factors
6. **SUGGESTS FOLLOW-UPS** - related questions the user might want to ask

Format your response in clear markdown with headers and actionable sections. Be specific about Kenya's startup ecosystem and provide practical, implementable advice.""")
        
        return "\n".join(prompt_parts)
    
    def _format_startup_context(self, profile: Dict[str, Any]) -> str:
        """Format startup profile information for LLaMA 3 prompt"""
        context_parts = []
        
        if profile.get('company_name'):
            context_parts.append(f"- **Company**: {profile['company_name']}")
        
        if profile.get('industry'):
            context_parts.append(f"- **Industry**: {profile['industry']}")
        
        if profile.get('stage'):
            context_parts.append(f"- **Stage**: {profile['stage']}")
        
        if profile.get('location'):
            context_parts.append(f"- **Location**: {profile['location']}")
        
        if profile.get('team_size'):
            context_parts.append(f"- **Team Size**: {profile['team_size']}")
        
        if profile.get('monthly_revenue'):
            context_parts.append(f"- **Monthly Revenue**: ${profile['monthly_revenue']:,}")
        
        if profile.get('seeking_funding'):
            funding_info = "- **Seeking Funding**: Yes"
            if profile.get('funding_amount_target'):
                funding_info += f" (Target: ${profile['funding_amount_target']:,})"
            context_parts.append(funding_info)
        
        return "\n".join(context_parts) if context_parts else "No specific startup profile provided"
    
    def _get_category_guidance(self, category: str) -> str:
        """Get category-specific guidance optimized for LLaMA 3"""
        guidance_map = {
            "funding": """
- Identify specific Kenyan investor types and firms relevant to the startup's stage and industry
- Provide realistic funding timelines and amounts based on Kenya market data
- Include government funding programs like KIICO, Youth Enterprise Fund
- Mention pitch deck requirements and Kenyan investor preferences
- Reference successful funding stories from Kenyan startups (e.g., Twiga Foods, Sendy, Apollo Agriculture)""",
            
            "legal": """
- Cover specific Kenyan regulatory requirements and compliance processes
- Include required licenses and permits by industry sector
- Mention KRA tax obligations, VAT registration, and compliance timelines
- Address intellectual property protection through KIPI
- Reference relevant Kenyan laws (Companies Act 2015, Data Protection Act 2019)""",
            
            "market": """
- Provide Kenya-specific market insights and consumer behavior patterns
- Include market size estimates for Kenya's 54M population
- Address competition from both local and international players
- Consider mobile-first approach (95% mobile penetration)
- Reference successful market entry strategies from Kenyan startups""",
            
            "ecosystem": """
- Recommend specific accelerators (iHub, MEST, Antler Kenya) with application details
- Suggest relevant co-working spaces in Nairobi, Mombasa, Kisumu
- Include mentor and advisor networks accessible in Kenya
- Mention industry-specific communities and events
- Provide networking strategies for Kenya's startup community"""
        }
        
        return guidance_map.get(category, "")
    
    async def _call_groq_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make API call to Groq with proper error handling
        
        Groq uses OpenAI-compatible API format
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                elif response.status_code == 401:
                    raise Exception("Invalid Groq API key. Please check your GROQ_API_KEY in .env file")
                else:
                    error_text = response.text
                    raise Exception(f"Groq API error: {response.status_code} - {error_text}")
                    
            except httpx.TimeoutException:
                if attempt == max_retries - 1:
                    raise Exception("Groq API request timed out after multiple attempts")
                await asyncio.sleep(2 ** attempt)
            
            except httpx.HTTPStatusError as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Groq API request failed: {e.response.status_code} - {e.response.text}")
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed to get response from Groq API after retries")
    
    async def _stream_groq_api(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream response from Groq API for real-time user experience
        
        Groq's streaming is extremely fast, providing excellent UX
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,  # Enable streaming
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            async with self.client.stream(
                "POST",
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status_code != 200:
                    yield f"Error: Groq API request failed with status {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line_data = line[6:]  # Remove "data: " prefix
                        
                        if line_data.strip() == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(line_data)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"Error streaming response: {str(e)}"
    
    async def _process_groq_response(
        self, 
        response: Dict[str, Any], 
        original_question: str,
        processing_time: float
    ) -> AIResponse:
        """Process Groq API response and extract metadata"""
        try:
            # Extract content from Groq response
            content = ""
            if "choices" in response and response["choices"]:
                choice = response["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
            
            # Calculate confidence score based on response quality
            confidence = self._calculate_confidence_score(content, original_question)
            
            # Extract or generate sources
            sources = self._extract_sources(content)
            
            # Generate suggested follow-up questions
            suggested_questions = self._generate_follow_up_questions(
                original_question, content
            )
            
            return AIResponse(
                content=content,
                confidence=confidence,
                sources=sources,
                suggested_questions=suggested_questions
            )
            
        except Exception as e:
            # Return error response
            return AIResponse(
                content=f"Error processing response: {str(e)}",
                confidence=0.1,
                sources=[],
                suggested_questions=[]
            )
    
    def _calculate_confidence_score(self, content: str, question: str) -> float:
        """
        Calculate confidence score based on response quality indicators
        Optimized for LLaMA 3 response patterns
        """
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length factor (LLaMA 3 gives good lengthy responses)
        length_score = min(len(content) / 1200, 1.0) * 0.25
        score += length_score
        
        # Kenya-specific content boost
        kenya_terms = [
            'kenya', 'kenyan', 'nairobi', 'mombasa', 'kra', 'cbk', 'ihub',
            'tlcom', 'novastar', 'mest', 'antler', 'shilling', 'east africa',
            'kiico', 'ecitizen', 'kipi'
        ]
        kenya_mentions = sum(1 for term in kenya_terms if term.lower() in content.lower())
        kenya_score = min(kenya_mentions / 6, 1.0) * 0.3
        score += kenya_score
        
        # Structure and formatting score (LLaMA 3 is good at markdown)
        structure_indicators = ["##", "**", "###", "- ", "1.", "2.", "3."]
        structure_count = sum(1 for indicator in structure_indicators if indicator in content)
        structure_score = min(structure_count / 8, 1.0) * 0.2
        score += structure_score
        
        # Actionability score
        action_words = ['next steps', 'action', 'recommend', 'should', 'can', 'contact', 'apply']
        action_mentions = sum(1 for word in action_words if word in content.lower())
        action_score = min(action_mentions / 5, 1.0) * 0.15
        score += action_score
        
        # Specificity score (mentions of specific companies, amounts, timelines)
        if any(char.isdigit() for char in content):  # Contains numbers/amounts
            score += 0.05
        
        if content.count('@') > 0 or 'http' in content.lower():  # Contains contacts/links
            score += 0.05
        
        return min(score, 1.0)
    
    def _extract_sources(self, content: str) -> List[str]:
        """Extract or infer sources mentioned in the response"""
        sources = []
        
        # Common Kenya startup ecosystem sources
        potential_sources = [
            "TLcom Capital", "Novastar Ventures", "GreenTec Capital", "4DX Ventures",
            "iHub", "MEST Africa", "Antler Kenya", "Founder Institute",
            "Central Bank of Kenya", "Kenya Revenue Authority", "Communications Authority",
            "Kenya Climate Innovation Center", "KIICO", "Youth Enterprise Fund",
            "Nairobi Angel Network", "Strathmore iLabAfrica"
        ]
        
        for source in potential_sources:
            if source.lower() in content.lower():
                sources.append(source)
        
        # Add generic ecosystem source if none found
        if not sources:
            sources.append("Kenya Startup Ecosystem Database")
        
        return sources[:5]  # Limit to 5 sources
    
    def _generate_follow_up_questions(
        self, 
        original_question: str, 
        response_content: str
    ) -> List[str]:
        """Generate relevant follow-up questions based on the query and response"""
        category = categorize_query(original_question)
        
        follow_up_map = {
            "funding": [
                "What documents should I prepare for investor meetings?",
                "How long does the fundraising process typically take in Kenya?",
                "What valuation should I expect at my current stage?",
                "Which legal firms in Kenya specialize in startup fundraising?"
            ],
            "legal": [
                "What are the ongoing compliance requirements after incorporation?",
                "How much should I budget for legal and regulatory costs?",
                "Which law firms in Kenya have experience with startups?",
                "What are the tax implications I should consider with KRA?"
            ],
            "market": [
                "How do I conduct effective market research in Kenya?",
                "What are the key customer acquisition channels here?",
                "How should I price my product for the Kenyan market?",
                "What are the major market risks specific to Kenya?"
            ],
            "ecosystem": [
                "How do I get connected to mentors in Kenya's startup ecosystem?",
                "What networking events should I prioritize attending?",
                "Which startup communities are most active in Nairobi?",
                "How do I build strategic partnerships within the ecosystem?"
            ]
        }
        
        base_questions = follow_up_map.get(category, [
            "What should be my highest priority next step?",
            "How do I measure success in this area?",
            "What common mistakes should I avoid in Kenya?",
            "Who else in the ecosystem should I connect with?"
        ])
        
        return base_questions[:3]  # Return top 3 most relevant
    
    def _get_fallback_questions(self) -> List[str]:
        """Get fallback questions when there's an error"""
        return [
            "How do I get started in Kenya's startup ecosystem?",
            "What funding options are available for early-stage startups in Kenya?",
            "Which accelerators should I consider applying to in Nairobi?",
            "How do I connect with other entrepreneurs in Kenya?"
        ]
    
    def _generate_cache_key(
        self, 
        question: str, 
        startup_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for response caching"""
        import hashlib
        
        # Create a hash based on question and key profile elements
        cache_data = {
            "question": question.lower().strip(),
            "industry": startup_profile.get("industry") if startup_profile else None,
            "stage": startup_profile.get("stage") if startup_profile else None,
            "model": self.model  # Include model in cache key
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()


# Convenience function for quick AI queries
async def ask_groq(question: str, startup_profile: Optional[Dict] = None) -> str:
    """
    Quick function to get AI response for a question using Groq
    
    Useful for testing and simple queries
    """
    service = GroqService()
    try:
        response = await service.process_startup_query(question, startup_profile)
        return response.content
    finally:
        await service.client.aclose()


# Export the service class
__all__ = ["GroqService", "ask_groq"]