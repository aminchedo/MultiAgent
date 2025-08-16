"""
gRPC JWT Authentication Middleware

This module provides JWT-based authentication for the agent network,
supporting both unary and streaming RPC calls with automatic token refresh.
"""

import asyncio
import functools
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

import grpc
import jwt
from grpc import aio
from grpc.aio import ServerInterceptor, UnaryUnaryCall, UnaryStreamCall
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class JWTAuthInterceptor(ServerInterceptor):
    """
    gRPC server interceptor for JWT-based authentication.
    
    Features:
    - RSA public/private key authentication
    - Token expiration validation
    - Agent-specific claims validation
    - Automatic context enrichment with authenticated agent info
    - Support for both unary and streaming calls
    """
    
    def __init__(
        self,
        public_key_path: str,
        algorithm: str = "RS256",
        issuer: str = "agent-network",
        audience: str = "agent-coordinator",
        token_expiry_seconds: int = 3600,
        allow_unauthenticated_paths: Optional[list] = None
    ):
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.token_expiry_seconds = token_expiry_seconds
        self.allow_unauthenticated_paths = allow_unauthenticated_paths or [
            "/agent.network.AgentRegistry/RegisterAgent",
            "/grpc.health.v1.Health/Check"
        ]
        
        # Load public key for verification
        with open(public_key_path, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Intercept and authenticate incoming requests."""
        
        # Skip authentication for allowed paths
        if handler_call_details.method in self.allow_unauthenticated_paths:
            return await continuation(handler_call_details)
        
        # Extract and validate JWT token
        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get('authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return self._create_error_handler(
                grpc.StatusCode.UNAUTHENTICATED,
                "Missing or invalid authorization header"
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"verify_exp": True}
            )
            
            # Validate agent-specific claims
            if not self._validate_agent_claims(payload):
                return self._create_error_handler(
                    grpc.StatusCode.PERMISSION_DENIED,
                    "Invalid agent claims"
                )
            
            # Add authenticated agent info to context
            handler = await continuation(handler_call_details)
            
            if handler and handler.unary_unary:
                return self._wrap_unary_unary(handler, payload)
            elif handler and handler.unary_stream:
                return self._wrap_unary_stream(handler, payload)
            elif handler and handler.stream_unary:
                return self._wrap_stream_unary(handler, payload)
            elif handler and handler.stream_stream:
                return self._wrap_stream_stream(handler, payload)
            
            return handler
            
        except jwt.ExpiredSignatureError:
            return self._create_error_handler(
                grpc.StatusCode.UNAUTHENTICATED,
                "Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return self._create_error_handler(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid token"
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return self._create_error_handler(
                grpc.StatusCode.INTERNAL,
                "Authentication error"
            )
    
    def _validate_agent_claims(self, payload: Dict[str, Any]) -> bool:
        """Validate agent-specific JWT claims."""
        required_claims = ['agent_id', 'agent_type', 'capabilities']
        
        for claim in required_claims:
            if claim not in payload:
                logger.warning(f"Missing required claim: {claim}")
                return False
        
        # Validate agent_id format
        agent_id = payload.get('agent_id', '')
        if not agent_id or len(agent_id) < 8:
            logger.warning(f"Invalid agent_id: {agent_id}")
            return False
        
        # Validate capabilities is a list
        capabilities = payload.get('capabilities', [])
        if not isinstance(capabilities, list):
            logger.warning(f"Invalid capabilities format: {type(capabilities)}")
            return False
        
        return True
    
    def _create_error_handler(
        self,
        status_code: grpc.StatusCode,
        details: str
    ) -> grpc.RpcMethodHandler:
        """Create an error handler that returns the specified error."""
        
        async def error_handler(request, context):
            await context.abort(status_code, details)
        
        return grpc.unary_unary_rpc_method_handler(
            error_handler,
            request_deserializer=lambda x: x,
            response_serializer=lambda x: x
        )
    
    def _wrap_unary_unary(
        self,
        handler: grpc.RpcMethodHandler,
        auth_payload: Dict[str, Any]
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-unary handler with authentication context."""
        
        @functools.wraps(handler.unary_unary)
        async def wrapper(request, context):
            # Add auth info to context
            context.auth_info = auth_payload
            return await handler.unary_unary(request, context)
        
        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )
    
    def _wrap_unary_stream(
        self,
        handler: grpc.RpcMethodHandler,
        auth_payload: Dict[str, Any]
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-stream handler with authentication context."""
        
        @functools.wraps(handler.unary_stream)
        async def wrapper(request, context):
            context.auth_info = auth_payload
            async for response in handler.unary_stream(request, context):
                yield response
        
        return grpc.unary_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )
    
    def _wrap_stream_unary(
        self,
        handler: grpc.RpcMethodHandler,
        auth_payload: Dict[str, Any]
    ) -> grpc.RpcMethodHandler:
        """Wrap stream-unary handler with authentication context."""
        
        @functools.wraps(handler.stream_unary)
        async def wrapper(request_iterator, context):
            context.auth_info = auth_payload
            return await handler.stream_unary(request_iterator, context)
        
        return grpc.stream_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )
    
    def _wrap_stream_stream(
        self,
        handler: grpc.RpcMethodHandler,
        auth_payload: Dict[str, Any]
    ) -> grpc.RpcMethodHandler:
        """Wrap stream-stream handler with authentication context."""
        
        @functools.wraps(handler.stream_stream)
        async def wrapper(request_iterator, context):
            context.auth_info = auth_payload
            async for response in handler.stream_stream(request_iterator, context):
                yield response
        
        return grpc.stream_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )


class JWTTokenManager:
    """
    Manages JWT token generation and refresh for agent authentication.
    """
    
    def __init__(
        self,
        private_key_path: str,
        algorithm: str = "RS256",
        issuer: str = "agent-network",
        audience: str = "agent-coordinator",
        token_expiry_seconds: int = 3600
    ):
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.token_expiry_seconds = token_expiry_seconds
        
        # Load private key for signing
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
    
    def generate_token(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: list,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a JWT token for an agent."""
        
        now = int(time.time())
        
        payload = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'capabilities': capabilities,
            'iat': now,
            'exp': now + self.token_expiry_seconds,
            'iss': self.issuer,
            'aud': self.audience
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(
            payload,
            self.private_key,
            algorithm=self.algorithm
        )
    
    def refresh_token(self, current_token: str) -> Optional[str]:
        """Refresh an existing token if it's still valid."""
        
        try:
            # Decode without verification to get claims
            payload = jwt.decode(
                current_token,
                options={"verify_signature": False, "verify_exp": False}
            )
            
            # Check if token is expired
            exp = payload.get('exp', 0)
            if exp < time.time():
                return None
            
            # Generate new token with same claims
            return self.generate_token(
                agent_id=payload['agent_id'],
                agent_type=payload['agent_type'],
                capabilities=payload['capabilities'],
                additional_claims={
                    k: v for k, v in payload.items()
                    if k not in ['agent_id', 'agent_type', 'capabilities', 'iat', 'exp', 'iss', 'aud']
                }
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None


class JWTClientInterceptor(aio.ClientCallDetails):
    """
    gRPC client interceptor that automatically adds JWT authentication headers.
    """
    
    def __init__(self, token_manager: JWTTokenManager, agent_info: Dict[str, Any]):
        self.token_manager = token_manager
        self.agent_info = agent_info
        self._token = None
        self._token_lock = asyncio.Lock()
    
    async def _get_token(self) -> str:
        """Get current token, refreshing if necessary."""
        async with self._token_lock:
            if not self._token:
                self._token = self.token_manager.generate_token(
                    agent_id=self.agent_info['agent_id'],
                    agent_type=self.agent_info['agent_type'],
                    capabilities=self.agent_info['capabilities']
                )
            
            # Try to refresh if token exists
            refreshed = self.token_manager.refresh_token(self._token)
            if refreshed:
                self._token = refreshed
            else:
                # Generate new token if refresh failed
                self._token = self.token_manager.generate_token(
                    agent_id=self.agent_info['agent_id'],
                    agent_type=self.agent_info['agent_type'],
                    capabilities=self.agent_info['capabilities']
                )
            
            return self._token
    
    async def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: aio.ClientCallDetails,
        request: Any
    ) -> Any:
        """Add JWT token to unary-unary calls."""
        
        token = await self._get_token()
        
        # Add authorization header
        metadata = list(client_call_details.metadata or [])
        metadata.append(('authorization', f'Bearer {token}'))
        
        new_details = aio.ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready
        )
        
        return await continuation(new_details, request)
    
    async def intercept_unary_stream(
        self,
        continuation: Callable,
        client_call_details: aio.ClientCallDetails,
        request: Any
    ) -> Any:
        """Add JWT token to unary-stream calls."""
        
        token = await self._get_token()
        
        metadata = list(client_call_details.metadata or [])
        metadata.append(('authorization', f'Bearer {token}'))
        
        new_details = aio.ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready
        )
        
        async for response in continuation(new_details, request):
            yield response


# Key generation utilities
def generate_key_pair(
    private_key_path: str = "private_key.pem",
    public_key_path: str = "public_key.pem"
) -> Tuple[str, str]:
    """Generate RSA key pair for JWT signing/verification."""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Save private key
    with open(private_key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Extract and save public key
    public_key = private_key.public_key()
    with open(public_key_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    return private_key_path, public_key_path