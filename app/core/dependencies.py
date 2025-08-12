from fastapi import HTTPException, Request, Depends
from typing import Optional, Dict, Any
import time
from datetime import datetime, timezone
import hashlib
import json
from collections import defaultdict, deque
import asyncio

from app.core.config import settings


# RATE LIMITING - Protect API from abuse


class RateLimiter:
    
    def __init__(self):
        # Store requests per IP address
        self.requests = defaultdict(deque)
        self.blocked_ips = defaultdict(float)  # IP -> block_until_timestamp
    
    def is_allowed(self, identifier: str, limit: int = None, window: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            identifier: Usually IP address or user ID
            limit: Number of requests allowed (default from settings)
            window: Time window in seconds (default 60)
        """
        if limit is None:
            limit = settings.RATE_LIMIT_PER_MINUTE
        
        current_time = time.time()
        
        # Check if IP is currently blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                return False
            else:
                # Block period expired, remove from blocked list
                del self.blocked_ips[identifier]
        
        # Clean old requests outside the window
        user_requests = self.requests[identifier]
        while user_requests and user_requests[0] < current_time - window:
            user_requests.popleft()
        
        # Check if limit exceeded
        if len(user_requests) >= limit:
            # Block IP for 5 minutes on rate limit violation
            self.blocked_ips[identifier] = current_time + 300
            return False
        
        # Add current request
        user_requests.append(current_time)
        return True
    
    def get_remaining_requests(self, identifier: str, limit: int = None) -> int:
        """Get number of remaining requests for identifier"""
        if limit is None:
            limit = settings.RATE_LIMIT_PER_MINUTE
        
        current_requests = len(self.requests[identifier])
        return max(0, limit - current_requests)


# Global rate limiter instance
rate_limiter = RateLimiter()


async def validate_query_rate_limit(request: Request) -> bool:
    """
    FastAPI dependency for rate limiting query endpoints
    
    This protects our expensive AI processing endpoints from abuse
    """
    # Get client IP address
    client_ip = request.client.host
    
    # In production, you might want to use X-Forwarded-For header
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed",
                "retry_after": 60,
                "client_ip": client_ip
            }
        )
    
    return True



# UTILITY FUNCTIONS - Common helpers

def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format with timezone
    
    Consistent timestamp format across the application
    """
    return datetime.now(timezone.utc).isoformat()


def generate_request_id() -> str:
    """
    Generate unique request ID for tracking
    
    Useful for correlating logs and debugging issues
    """
    timestamp = str(time.time())
    return hashlib.md5(timestamp.encode()).hexdigest()[:12]


def sanitize_input(text: str) -> str:
    """
    Basic input sanitization for user queries
    
    Removes potentially harmful content while preserving meaning
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Remove potential script tags (basic XSS protection)
    text = text.replace("<script", "&lt;script")
    text = text.replace("</script>", "&lt;/script&gt;")
    
    # Remove other potentially harmful patterns
    harmful_patterns = ["javascript:", "data:", "vbscript:"]
    for pattern in harmful_patterns:
        text = text.replace(pattern, "")
    
    return text.strip()


def extract_keywords(text: str, min_length: int = 3) -> list:
    """
    Extract keywords from text for categorization and search
    
    Simple keyword extraction for analytics and matching
    """
    # Convert to lowercase and split
    words = text.lower().split()
    
    # Filter out common stop words and short words
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'i', 'my', 'me', 'we', 'our', 'you',
        'your', 'how', 'what', 'when', 'where', 'why', 'do', 'does', 'can'
    }
    
    keywords = [
        word.strip('.,!?;:"()[]{}') 
        for word in words 
        if len(word) >= min_length and word.lower() not in stop_words
    ]
    
    return list(set(keywords))  # Remove duplicates


def categorize_query(question: str) -> str:
    """
    Categorize user queries for analytics and routing
    
    Helps understand what users are asking about most
    """
    question_lower = question.lower()
    
    # Define category keywords
    categories = {
        "funding": ["fund", "invest", "money", "capital", "raise", "seed", "series", "angel", "vc"],
        "legal": ["legal", "law", "compliance", "regulation", "incorporate", "license", "permit"],
        "market": ["market", "customer", "competitor", "size", "opportunity", "validation"],
        "team": ["team", "hire", "talent", "co-founder", "employee", "staff"],
        "product": ["product", "development", "mvp", "feature", "user", "design"],
        "business_model": ["revenue", "pricing", "monetization", "business model", "strategy"],
        "networking": ["network", "mentor", "advisor", "connect", "introduction"],
        "ecosystem": ["accelerator", "incubator", "co-working", "hub", "community"],
        "scaling": ["scale", "growth", "expand", "international", "regional"],
        "technology": ["tech", "development", "platform", "api", "software"]
    }
    
    # Count keyword matches for each category
    category_scores = defaultdict(int)
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in question_lower:
                category_scores[category] += 1
    
    # Return category with highest score, or 'general' if no strong match
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    else:
        return "general"


# CACHING HELPERS - Simple in-memory caching


class SimpleCache:
    """
    Simple in-memory cache for expensive operations
    
    In production, use Redis or Memcached for distributed caching
    """
    
    def __init__(self, default_ttl: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.default_ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.timestamps.clear()


# Global cache instance
cache = SimpleCache(default_ttl=settings.AI_RESPONSE_CACHE_TTL)


# EXPORT ALL DEPENDENCIES
__all__ = [
    # Rate Limiting
    "RateLimiter", "rate_limiter", "validate_query_rate_limit",
    
    # Utilities
    "get_current_timestamp", "generate_request_id", "sanitize_input",
    "extract_keywords", "categorize_query",
    
    # Caching
    "SimpleCache", "cache"
]