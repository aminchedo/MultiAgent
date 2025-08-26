"""
Enhanced Security and Error Handling Module
Provides comprehensive security measures, validation, and error handling utilities
"""

import jwt
import hashlib
import secrets
import time
import re
from typing import Dict, Any, Optional, List, Union
from functools import wraps
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

# Error Types and Classes
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"
    AGENT = "agent"
    NETWORK = "network"
    DATABASE = "database"

class SecurityError(Exception):
    """Base security exception"""
    def __init__(self, message: str, category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.message = message
        self.category = category
        self.severity = severity
        self.timestamp = time.time()
        super().__init__(self.message)

class ValidationError(SecurityError):
    """Input validation error"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.field = field
        self.value = value
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM)

class RateLimitError(SecurityError):
    """Rate limiting error"""
    def __init__(self, message: str, limit: int, window: int):
        self.limit = limit
        self.window = window
        super().__init__(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.HIGH)

class AgentError(SecurityError):
    """Agent execution error"""
    def __init__(self, message: str, agent_name: str, operation: str = None):
        self.agent_name = agent_name
        self.operation = operation
        super().__init__(message, ErrorCategory.AGENT, ErrorSeverity.HIGH)

# Security Configuration
class SecurityConfig:
    """Security configuration settings"""
    
    # JWT Configuration
    JWT_SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    JWT_REFRESH_HOURS = 168  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 60
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_BURST = 10
    
    # Input Validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_PROMPT_LENGTH = 5000
    MIN_PROMPT_LENGTH = 10
    ALLOWED_FILE_EXTENSIONS = ['.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.md']
    
    # CORS Configuration
    ALLOWED_ORIGINS = ["*"]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["*"]
    
    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

# Input Validation Utilities
class InputValidator:
    """Comprehensive input validation utilities"""
    
    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """Validate user prompt input"""
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("Prompt must be a non-empty string", "prompt", prompt)
        
        if len(prompt.strip()) < SecurityConfig.MIN_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt must be at least {SecurityConfig.MIN_PROMPT_LENGTH} characters",
                "prompt", prompt
            )
        
        if len(prompt) > SecurityConfig.MAX_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt must not exceed {SecurityConfig.MAX_PROMPT_LENGTH} characters",
                "prompt", prompt
            )
        
        # Check for potentially malicious content
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # Eval functions
            r'exec\s*\(',  # Exec functions
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, prompt, re.IGNORECASE | re.DOTALL):
                raise ValidationError(
                    "Prompt contains potentially malicious content",
                    "prompt", prompt
                )
        
        return True
    
    @staticmethod
    def validate_framework(framework: str) -> bool:
        """Validate framework selection"""
        allowed_frameworks = ["react", "vue", "vanilla", "nextjs", "nuxt", "angular"]
        
        if not framework or framework not in allowed_frameworks:
            raise ValidationError(
                f"Framework must be one of: {allowed_frameworks}",
                "framework", framework
            )
        
        return True
    
    @staticmethod
    def validate_complexity(complexity: str) -> bool:
        """Validate complexity level"""
        allowed_complexity = ["simple", "intermediate", "complex"]
        
        if not complexity or complexity not in allowed_complexity:
            raise ValidationError(
                f"Complexity must be one of: {allowed_complexity}",
                "complexity", complexity
            )
        
        return True
    
    @staticmethod
    def validate_features(features: List[str]) -> bool:
        """Validate feature list"""
        allowed_features = [
            "responsive-design", "dark-mode", "animations", 
            "api-integration", "testing", "deployment"
        ]
        
        if not isinstance(features, list):
            raise ValidationError("Features must be a list", "features", features)
        
        for feature in features:
            if feature not in allowed_features:
                raise ValidationError(
                    f"Unknown feature: {feature}. Allowed: {allowed_features}",
                    "features", feature
                )
        
        return True
    
    @staticmethod
    def validate_file_content(content: str, filename: str) -> bool:
        """Validate file content for security"""
        if not content or not isinstance(content, str):
            raise ValidationError("File content must be a non-empty string", "content", content)
        
        # Check file size
        if len(content.encode('utf-8')) > SecurityConfig.MAX_REQUEST_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {SecurityConfig.MAX_REQUEST_SIZE} bytes",
                "content", len(content)
            )
        
        # Check file extension
        if filename:
            ext = '.' + filename.split('.')[-1] if '.' in filename else ''
            if ext not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
                raise ValidationError(
                    f"File extension not allowed: {ext}",
                    "filename", filename
                )
        
        return True

# Rate Limiting
class RateLimiter:
    """Advanced rate limiting with sliding window"""
    
    def __init__(self):
        self.requests = {}  # client_id -> [(timestamp, count), ...]
        self.blocked_clients = {}  # client_id -> block_until_timestamp
    
    def is_allowed(self, client_id: str, limit: int = None, window: int = None) -> bool:
        """Check if request is allowed for client"""
        limit = limit or SecurityConfig.RATE_LIMIT_REQUESTS
        window = window or SecurityConfig.RATE_LIMIT_WINDOW
        current_time = time.time()
        
        # Check if client is currently blocked
        if client_id in self.blocked_clients:
            if current_time < self.blocked_clients[client_id]:
                return False
            else:
                del self.blocked_clients[client_id]
        
        # Initialize client tracking
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests outside window
        self.requests[client_id] = [
            (ts, count) for ts, count in self.requests[client_id]
            if current_time - ts < window
        ]
        
        # Count current requests in window
        total_requests = sum(count for _, count in self.requests[client_id])
        
        if total_requests >= limit:
            # Block client for additional time
            self.blocked_clients[client_id] = current_time + window
            raise RateLimitError(
                f"Rate limit exceeded. {total_requests}/{limit} requests in {window}s",
                limit, window
            )
        
        # Add current request
        self.requests[client_id].append((current_time, 1))
        return True

# JWT Token Management
class TokenManager:
    """JWT token creation and validation"""
    
    @staticmethod
    def create_token(user_id: str, additional_claims: Dict = None) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=SecurityConfig.JWT_EXPIRATION_HOURS),
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, SecurityConfig.JWT_SECRET_KEY, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create refresh token"""
        payload = {
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=SecurityConfig.JWT_REFRESH_HOURS),
            "type": "refresh"
        }
        
        return jwt.encode(payload, SecurityConfig.JWT_SECRET_KEY, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                SecurityConfig.JWT_SECRET_KEY, 
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired", ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM)
        except jwt.InvalidTokenError as e:
            raise SecurityError(f"Invalid token: {e}", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH)

# Error Handler Decorator
def handle_errors(severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator for comprehensive error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {func.__name__}: {e.message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Validation Error",
                        "message": e.message,
                        "field": e.field,
                        "category": e.category.value
                    }
                )
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded in {func.__name__}: {e.message}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate Limit Exceeded",
                        "message": e.message,
                        "limit": e.limit,
                        "window": e.window
                    }
                )
            except SecurityError as e:
                logger.error(f"Security error in {func.__name__}: {e.message}")
                status_code = status.HTTP_403_FORBIDDEN if e.category == ErrorCategory.AUTHORIZATION else status.HTTP_401_UNAUTHORIZED
                raise HTTPException(
                    status_code=status_code,
                    detail={
                        "error": "Security Error",
                        "message": e.message,
                        "category": e.category.value,
                        "severity": e.severity.value
                    }
                )
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred" if severity != ErrorSeverity.LOW else str(e)
                    }
                )
        return wrapper
    return decorator

# Security Middleware
class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    async def __call__(self, request: Request, call_next):
        """Process request with security checks"""
        start_time = time.time()
        
        try:
            # Get client identifier
            client_id = self.get_client_id(request)
            
            # Rate limiting
            self.rate_limiter.is_allowed(client_id)
            
            # Add security headers
            response = await call_next(request)
            
            for header, value in SecurityConfig.SECURITY_HEADERS.items():
                response.headers[header] = value
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(time.time() - start_time)
            
            return response
            
        except (RateLimitError, SecurityError) as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS if isinstance(e, RateLimitError) else status.HTTP_403_FORBIDDEN,
                detail={"error": e.__class__.__name__, "message": e.message}
            )
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = TokenManager.validate_token(token)
                return payload.get("user_id", "anonymous")
            except SecurityError:
                pass
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"

# Content Security
class ContentSecurity:
    """Content security and sanitization"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\x08', '\x0b', '\x0c', '\x0e', '\x0f']
        
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Limit length
        return text[:SecurityConfig.MAX_PROMPT_LENGTH]
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000).hex() + ':' + salt

# Global instances
rate_limiter = RateLimiter()
token_manager = TokenManager()
input_validator = InputValidator()
security_middleware = SecurityMiddleware()

# Utility functions
def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Implementation would check for valid JWT token
        return await func(*args, **kwargs)
    return wrapper

def validate_request(validation_rules: Dict[str, callable]):
    """Decorator to validate request data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Implementation would validate request based on rules
            return await func(*args, **kwargs)
        return wrapper
    return decorator