"""
Backpressure and Flow Control Middleware

This module implements backpressure strategies for agent-to-agent communication,
including request coalescing, circuit breakers, and adaptive rate limiting.
"""

import asyncio
import time
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import hashlib
import json

import grpc
from grpc import aio

logger = logging.getLogger(__name__)


class BackpressureStrategy(Enum):
    """Available backpressure strategies."""
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAKER = "circuit_breaker"
    ADAPTIVE_CONCURRENCY = "adaptive_concurrency"
    REQUEST_COALESCING = "request_coalescing"
    COMBINED = "combined"


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking."""
    failure_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Record a successful request."""
        self.failure_count = 0
        self.last_success_time = time.time()
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()


@dataclass
class RateLimiterState:
    """Token bucket rate limiter state."""
    tokens: float
    last_refill_time: float
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens."""
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def refill(self, rate: float, capacity: float):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill_time
        tokens_to_add = elapsed * rate
        self.tokens = min(capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now


@dataclass
class AdaptiveConcurrencyState:
    """Adaptive concurrency limiter state using gradient descent."""
    limit: float = 100.0
    in_flight: int = 0
    rtt_noload: float = 0.001  # Baseline RTT in seconds
    smoothing: float = 0.2
    gradient: float = 2.0
    min_limit: float = 1.0
    max_limit: float = 1000.0
    
    def update_limit(self, rtt: float, did_drop: bool):
        """Update concurrency limit based on Little's Law and gradient descent."""
        # Update gradient based on whether we dropped the request
        if did_drop:
            self.gradient = max(0.5, self.gradient * 0.9)
        else:
            self.gradient = min(4.0, self.gradient * 1.01)
        
        # Calculate new limit using Little's Law
        # L = λ * W (concurrency = throughput * latency)
        if rtt > 0:
            new_limit = self.gradient * (self.limit * self.rtt_noload / rtt)
            
            # Smooth the limit changes
            self.limit = (self.smoothing * new_limit + 
                         (1 - self.smoothing) * self.limit)
            
            # Apply bounds
            self.limit = max(self.min_limit, min(self.max_limit, self.limit))
        
        # Update baseline RTT estimate
        if not did_drop and rtt < self.rtt_noload * 2:
            self.rtt_noload = (self.smoothing * rtt + 
                              (1 - self.smoothing) * self.rtt_noload)


@dataclass
class CoalescedRequest:
    """Represents a coalesced request with multiple waiters."""
    key: str
    request: Any
    futures: List[asyncio.Future] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def add_waiter(self) -> asyncio.Future:
        """Add a new waiter for this request."""
        future = asyncio.Future()
        self.futures.append(future)
        return future
    
    def complete(self, result: Any, error: Optional[Exception] = None):
        """Complete all waiting futures."""
        for future in self.futures:
            if not future.done():
                if error:
                    future.set_exception(error)
                else:
                    future.set_result(result)


class BackpressureInterceptor(aio.ServerInterceptor):
    """
    Server-side interceptor implementing backpressure strategies.
    
    Features:
    - Rate limiting with token bucket
    - Circuit breaker pattern
    - Adaptive concurrency control
    - Request coalescing for identical requests
    - Metrics collection
    """
    
    def __init__(
        self,
        strategy: BackpressureStrategy = BackpressureStrategy.COMBINED,
        rate_limit: float = 100.0,  # requests per second
        rate_limit_capacity: float = 200.0,  # burst capacity
        circuit_breaker_threshold: int = 5,  # failures before opening
        circuit_breaker_timeout: float = 30.0,  # seconds before retry
        coalesce_window: float = 0.1,  # seconds to wait for coalescing
        max_coalesce_size: int = 100  # max requests to coalesce
    ):
        self.strategy = strategy
        self.rate_limit = rate_limit
        self.rate_limit_capacity = rate_limit_capacity
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.coalesce_window = coalesce_window
        self.max_coalesce_size = max_coalesce_size
        
        # Per-agent state
        self.rate_limiters: Dict[str, RateLimiterState] = defaultdict(
            lambda: RateLimiterState(rate_limit_capacity, time.time())
        )
        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(
            CircuitBreakerState
        )
        self.adaptive_limiters: Dict[str, AdaptiveConcurrencyState] = defaultdict(
            AdaptiveConcurrencyState
        )
        
        # Request coalescing
        self.coalesced_requests: Dict[str, CoalescedRequest] = {}
        self.coalesce_lock = asyncio.Lock()
        
        # Metrics
        self.metrics = {
            'requests_dropped': 0,
            'requests_coalesced': 0,
            'circuit_breaker_opens': 0,
            'rate_limit_hits': 0
        }
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Intercept and apply backpressure strategies."""
        
        handler = await continuation(handler_call_details)
        if not handler:
            return handler
        
        # Extract agent ID from context
        agent_id = self._extract_agent_id(handler_call_details)
        
        # Wrap handler based on type
        if handler.unary_unary:
            return self._wrap_unary_unary(handler, agent_id, handler_call_details)
        elif handler.unary_stream:
            return self._wrap_unary_stream(handler, agent_id, handler_call_details)
        
        return handler
    
    def _extract_agent_id(self, handler_call_details: grpc.HandlerCallDetails) -> str:
        """Extract agent ID from metadata."""
        metadata = dict(handler_call_details.invocation_metadata or [])
        return metadata.get('agent-id', 'unknown')
    
    def _wrap_unary_unary(
        self,
        handler: grpc.RpcMethodHandler,
        agent_id: str,
        call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-unary handler with backpressure logic."""
        
        @functools.wraps(handler.unary_unary)
        async def wrapper(request, context):
            start_time = time.time()
            
            try:
                # Apply backpressure strategies
                allowed, reason = await self._check_backpressure(
                    agent_id, request, call_details.method
                )
                
                if not allowed:
                    self.metrics['requests_dropped'] += 1
                    await context.abort(
                        grpc.StatusCode.RESOURCE_EXHAUSTED,
                        f"Request dropped: {reason}"
                    )
                
                # Check for request coalescing
                if self.strategy in [BackpressureStrategy.REQUEST_COALESCING, 
                                   BackpressureStrategy.COMBINED]:
                    result = await self._try_coalesce(
                        agent_id, request, call_details.method, handler, context
                    )
                    if result is not None:
                        return result
                
                # Execute request
                response = await handler.unary_unary(request, context)
                
                # Record success
                elapsed = time.time() - start_time
                await self._record_success(agent_id, elapsed)
                
                return response
                
            except Exception as e:
                # Record failure
                await self._record_failure(agent_id)
                raise
        
        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )
    
    def _wrap_unary_stream(
        self,
        handler: grpc.RpcMethodHandler,
        agent_id: str,
        call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-stream handler with backpressure logic."""
        
        @functools.wraps(handler.unary_stream)
        async def wrapper(request, context):
            # Apply initial backpressure check
            allowed, reason = await self._check_backpressure(
                agent_id, request, call_details.method
            )
            
            if not allowed:
                self.metrics['requests_dropped'] += 1
                await context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    f"Request dropped: {reason}"
                )
            
            # Stream with rate limiting
            async for response in handler.unary_stream(request, context):
                # Apply per-message rate limiting for streams
                if self.strategy in [BackpressureStrategy.RATE_LIMIT, 
                                   BackpressureStrategy.COMBINED]:
                    limiter = self.rate_limiters[agent_id]
                    limiter.refill(self.rate_limit / 10, self.rate_limit_capacity / 10)
                    
                    if not limiter.consume(0.1):  # Fractional tokens for stream messages
                        await asyncio.sleep(0.01)  # Brief backoff
                
                yield response
        
        return grpc.unary_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )
    
    async def _check_backpressure(
        self,
        agent_id: str,
        request: Any,
        method: str
    ) -> Tuple[bool, str]:
        """Check if request should be allowed based on backpressure strategies."""
        
        strategies_to_check = []
        
        if self.strategy == BackpressureStrategy.COMBINED:
            strategies_to_check = [
                BackpressureStrategy.CIRCUIT_BREAKER,
                BackpressureStrategy.RATE_LIMIT,
                BackpressureStrategy.ADAPTIVE_CONCURRENCY
            ]
        else:
            strategies_to_check = [self.strategy]
        
        for strategy in strategies_to_check:
            if strategy == BackpressureStrategy.CIRCUIT_BREAKER:
                allowed, reason = self._check_circuit_breaker(agent_id)
                if not allowed:
                    return False, reason
            
            elif strategy == BackpressureStrategy.RATE_LIMIT:
                allowed, reason = self._check_rate_limit(agent_id)
                if not allowed:
                    return False, reason
            
            elif strategy == BackpressureStrategy.ADAPTIVE_CONCURRENCY:
                allowed, reason = await self._check_adaptive_concurrency(agent_id)
                if not allowed:
                    return False, reason
        
        return True, "OK"
    
    def _check_circuit_breaker(self, agent_id: str) -> Tuple[bool, str]:
        """Check circuit breaker state."""
        breaker = self.circuit_breakers[agent_id]
        
        if breaker.state == "OPEN":
            # Check if we should transition to half-open
            if time.time() - breaker.last_failure_time > self.circuit_breaker_timeout:
                breaker.state = "HALF_OPEN"
            else:
                return False, "Circuit breaker is OPEN"
        
        return True, "OK"
    
    def _check_rate_limit(self, agent_id: str) -> Tuple[bool, str]:
        """Check rate limit using token bucket."""
        limiter = self.rate_limiters[agent_id]
        limiter.refill(self.rate_limit, self.rate_limit_capacity)
        
        if not limiter.consume():
            self.metrics['rate_limit_hits'] += 1
            return False, "Rate limit exceeded"
        
        return True, "OK"
    
    async def _check_adaptive_concurrency(self, agent_id: str) -> Tuple[bool, str]:
        """Check adaptive concurrency limit."""
        limiter = self.adaptive_limiters[agent_id]
        
        if limiter.in_flight >= int(limiter.limit):
            return False, f"Concurrency limit reached ({int(limiter.limit)})"
        
        limiter.in_flight += 1
        return True, "OK"
    
    async def _try_coalesce(
        self,
        agent_id: str,
        request: Any,
        method: str,
        handler: grpc.RpcMethodHandler,
        context: grpc.ServicerContext
    ) -> Optional[Any]:
        """Try to coalesce identical requests."""
        
        # Generate request key
        request_key = self._generate_request_key(agent_id, method, request)
        
        async with self.coalesce_lock:
            # Check if request is already in flight
            if request_key in self.coalesced_requests:
                coalesced = self.coalesced_requests[request_key]
                
                # Check if coalescing window is still open
                if (time.time() - coalesced.created_at < self.coalesce_window and
                    len(coalesced.futures) < self.max_coalesce_size):
                    
                    # Add to waiters
                    future = coalesced.add_waiter()
                    self.metrics['requests_coalesced'] += 1
                    
                    # Wait for result outside lock
                    return await future
            
            # Create new coalesced request
            coalesced = CoalescedRequest(request_key, request)
            self.coalesced_requests[request_key] = coalesced
        
        # Execute request (first requester)
        try:
            response = await handler.unary_unary(request, context)
            coalesced.complete(response)
            return response
        except Exception as e:
            coalesced.complete(None, e)
            raise
        finally:
            # Cleanup
            async with self.coalesce_lock:
                del self.coalesced_requests[request_key]
    
    def _generate_request_key(
        self,
        agent_id: str,
        method: str,
        request: Any
    ) -> str:
        """Generate a unique key for request coalescing."""
        # Serialize request to bytes (this assumes protobuf messages)
        try:
            request_bytes = request.SerializeToString()
        except:
            # Fallback for non-protobuf requests
            request_bytes = str(request).encode()
        
        # Create hash of agent + method + request
        hasher = hashlib.sha256()
        hasher.update(agent_id.encode())
        hasher.update(method.encode())
        hasher.update(request_bytes)
        
        return hasher.hexdigest()
    
    async def _record_success(self, agent_id: str, elapsed: float):
        """Record successful request."""
        # Update circuit breaker
        breaker = self.circuit_breakers[agent_id]
        breaker.record_success()
        
        # Update adaptive concurrency
        if agent_id in self.adaptive_limiters:
            limiter = self.adaptive_limiters[agent_id]
            limiter.in_flight -= 1
            limiter.update_limit(elapsed, False)
    
    async def _record_failure(self, agent_id: str):
        """Record failed request."""
        # Update circuit breaker
        breaker = self.circuit_breakers[agent_id]
        breaker.record_failure()
        
        if breaker.failure_count >= self.circuit_breaker_threshold:
            breaker.state = "OPEN"
            self.metrics['circuit_breaker_opens'] += 1
            logger.warning(f"Circuit breaker opened for agent {agent_id}")
        
        # Update adaptive concurrency
        if agent_id in self.adaptive_limiters:
            limiter = self.adaptive_limiters[agent_id]
            limiter.in_flight -= 1
            limiter.update_limit(0, True)  # Indicate dropped request


class ClientBackpressureInterceptor:
    """
    Client-side interceptor for handling backpressure responses.
    
    Features:
    - Automatic retry with exponential backoff
    - Request hedging for latency-sensitive calls
    - Load shedding based on local queue depth
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 0.1,
        max_backoff: float = 10.0,
        backoff_multiplier: float = 2.0,
        enable_hedging: bool = True,
        hedge_delay: float = 0.05,  # 50ms
        max_queue_depth: int = 1000
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        self.enable_hedging = enable_hedging
        self.hedge_delay = hedge_delay
        self.max_queue_depth = max_queue_depth
        
        # Local queue tracking
        self.pending_requests = 0
        self.request_lock = asyncio.Lock()
    
    async def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: aio.ClientCallDetails,
        request: Any
    ) -> Any:
        """Intercept unary calls with retry and hedging logic."""
        
        # Check local queue depth
        async with self.request_lock:
            if self.pending_requests >= self.max_queue_depth:
                raise grpc.RpcError(
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    "Local queue depth exceeded"
                )
            self.pending_requests += 1
        
        try:
            # Try with hedging if enabled
            if self.enable_hedging:
                return await self._call_with_hedging(
                    continuation, client_call_details, request
                )
            else:
                return await self._call_with_retry(
                    continuation, client_call_details, request
                )
        finally:
            async with self.request_lock:
                self.pending_requests -= 1
    
    async def _call_with_retry(
        self,
        continuation: Callable,
        client_call_details: aio.ClientCallDetails,
        request: Any
    ) -> Any:
        """Execute call with exponential backoff retry."""
        
        last_error = None
        backoff = self.initial_backoff
        
        for attempt in range(self.max_retries + 1):
            try:
                return await continuation(client_call_details, request)
                
            except grpc.RpcError as e:
                last_error = e
                
                # Don't retry on non-retryable errors
                if e.code() not in [
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED
                ]:
                    raise
                
                # Last attempt, don't sleep
                if attempt == self.max_retries:
                    break
                
                # Exponential backoff with jitter
                jitter = backoff * 0.1 * (2 * asyncio.create_task(
                    asyncio.sleep(0)).random() - 1)
                sleep_time = min(backoff + jitter, self.max_backoff)
                
                logger.debug(
                    f"Retry attempt {attempt + 1}/{self.max_retries} "
                    f"after {sleep_time:.3f}s backoff"
                )
                
                await asyncio.sleep(sleep_time)
                backoff *= self.backoff_multiplier
        
        raise last_error
    
    async def _call_with_hedging(
        self,
        continuation: Callable,
        client_call_details: aio.ClientCallDetails,
        request: Any
    ) -> Any:
        """Execute call with request hedging."""
        
        # Create tasks for primary and hedge requests
        tasks = []
        
        async def make_call(delay: float = 0):
            if delay > 0:
                await asyncio.sleep(delay)
            return await self._call_with_retry(
                continuation, client_call_details, request
            )
        
        # Primary request
        tasks.append(asyncio.create_task(make_call()))
        
        # Hedge request after delay
        tasks.append(asyncio.create_task(make_call(self.hedge_delay)))
        
        # Wait for first successful response
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Return first result
        for task in done:
            try:
                return await task
            except Exception:
                pass
        
        # All failed, raise last error
        for task in tasks:
            try:
                await task
            except Exception as e:
                raise e


# Optimal settings for different scenarios
class BackpressureProfiles:
    """Pre-configured backpressure profiles for common scenarios."""
    
    @staticmethod
    def high_frequency_updates() -> Dict[str, Any]:
        """Profile for high-frequency update scenarios."""
        return {
            'strategy': BackpressureStrategy.COMBINED,
            'rate_limit': 1000.0,  # 1000 RPS
            'rate_limit_capacity': 2000.0,  # Allow bursts
            'circuit_breaker_threshold': 10,
            'circuit_breaker_timeout': 10.0,
            'coalesce_window': 0.05,  # 50ms window
            'max_coalesce_size': 200
        }
    
    @staticmethod
    def latency_sensitive() -> Dict[str, Any]:
        """Profile for latency-sensitive operations."""
        return {
            'strategy': BackpressureStrategy.ADAPTIVE_CONCURRENCY,
            'rate_limit': 500.0,
            'rate_limit_capacity': 500.0,  # No bursts
            'circuit_breaker_threshold': 3,
            'circuit_breaker_timeout': 5.0,
            'coalesce_window': 0.01,  # 10ms window
            'max_coalesce_size': 50
        }
    
    @staticmethod
    def batch_processing() -> Dict[str, Any]:
        """Profile for batch processing scenarios."""
        return {
            'strategy': BackpressureStrategy.REQUEST_COALESCING,
            'rate_limit': 100.0,
            'rate_limit_capacity': 500.0,
            'circuit_breaker_threshold': 5,
            'circuit_breaker_timeout': 30.0,
            'coalesce_window': 0.5,  # 500ms window
            'max_coalesce_size': 1000
        }


# Answer to critical questions:
# 1. Request coalescing: Yes, implemented with configurable window (50ms recommended for high-frequency)
# 2. Optimal heartbeat interval: 2-5 seconds recommended, with 2s for < 50 agents, 5s for 50+