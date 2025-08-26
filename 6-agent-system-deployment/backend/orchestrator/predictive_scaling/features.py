"""
Feature extraction for predictive scaling

This module extracts and engineers features from Prometheus metrics
for use in the LSTM workload prediction model.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
import holidays
import asyncio
from collections import defaultdict

import structlog
from prometheus_api_client import PrometheusConnect
from prometheus_client import Gauge, Counter, Histogram

logger = structlog.get_logger()

# Metrics for feature extraction monitoring
feature_extraction_duration = Histogram(
    'predictive_scaling_feature_extraction_seconds',
    'Time spent extracting features'
)
feature_extraction_errors = Counter(
    'predictive_scaling_feature_extraction_errors_total',
    'Total feature extraction errors'
)
feature_quality_score = Gauge(
    'predictive_scaling_feature_quality',
    'Quality score of extracted features',
    ['feature_type']
)


@dataclass
class ScalingFeatures:
    """Features for predictive scaling model"""
    # Time-based features
    hour_of_day: int
    day_of_week: int
    day_of_month: int
    is_weekend: bool
    is_holiday: bool
    minutes_since_midnight: int
    
    # Historical metrics (rolling windows)
    task_rate_1m: float
    task_rate_5m: float
    task_rate_15m: float
    task_rate_1h: float
    
    # Queue metrics
    queue_depth_by_priority: Dict[str, int]
    avg_queue_time: float
    queue_growth_rate: float
    max_queue_depth: int
    
    # Agent utilization
    agent_utilization_by_type: Dict[str, float]
    active_agents_by_type: Dict[str, int]
    avg_task_duration_by_type: Dict[str, float]
    
    # Task complexity
    complexity_distribution: Dict[str, float]
    dependency_ratio: float
    avg_task_complexity: float
    
    # System metrics
    cpu_usage: float
    memory_usage: float
    network_throughput: float
    
    # External factors
    api_request_rate: float
    user_sessions_active: int
    concurrent_deployments: int
    
    # Derived features
    task_acceleration: float  # Rate of change in task submission
    utilization_pressure: float  # How close to capacity
    cost_efficiency: float  # Tasks per dollar
    queue_pressure: float  # Queue depth relative to processing capacity
    
    def to_numpy(self) -> np.ndarray:
        """Convert features to numpy array for model input"""
        features = []
        
        # Time features (normalized)
        features.extend([
            self.hour_of_day / 24.0,
            self.day_of_week / 7.0,
            self.day_of_month / 31.0,
            float(self.is_weekend),
            float(self.is_holiday),
            self.minutes_since_midnight / 1440.0
        ])
        
        # Task rates (log-normalized)
        features.extend([
            np.log1p(self.task_rate_1m),
            np.log1p(self.task_rate_5m),
            np.log1p(self.task_rate_15m),
            np.log1p(self.task_rate_1h)
        ])
        
        # Queue metrics
        for priority in ['CRITICAL', 'HIGH', 'NORMAL', 'LOW', 'BACKGROUND']:
            features.append(np.log1p(self.queue_depth_by_priority.get(priority, 0)))
        features.extend([
            np.log1p(self.avg_queue_time),
            np.tanh(self.queue_growth_rate),  # Bounded [-1, 1]
            np.log1p(self.max_queue_depth)
        ])
        
        # Agent utilization (5 agent types)
        for agent_type in ['planner', 'code_generator', 'tester', 'reviewer', 'doc_generator']:
            features.append(self.agent_utilization_by_type.get(agent_type, 0))
            features.append(np.log1p(self.active_agents_by_type.get(agent_type, 0)))
            features.append(np.log1p(self.avg_task_duration_by_type.get(agent_type, 0)))
        
        # Complexity distribution
        for complexity in ['simple', 'moderate', 'complex', 'heavy']:
            features.append(self.complexity_distribution.get(complexity, 0))
        features.extend([
            self.dependency_ratio,
            np.log1p(self.avg_task_complexity)
        ])
        
        # System metrics
        features.extend([
            self.cpu_usage,
            self.memory_usage,
            np.log1p(self.network_throughput)
        ])
        
        # External factors
        features.extend([
            np.log1p(self.api_request_rate),
            np.log1p(self.user_sessions_active),
            np.log1p(self.concurrent_deployments)
        ])
        
        # Derived features
        features.extend([
            np.tanh(self.task_acceleration),
            self.utilization_pressure,
            np.log1p(self.cost_efficiency),
            self.queue_pressure
        ])
        
        return np.array(features, dtype=np.float32)


class FeatureExtractor:
    """Extract features from Prometheus metrics"""
    
    def __init__(self, prometheus_url: str):
        self.prom = PrometheusConnect(url=prometheus_url)
        self.feature_window = timedelta(hours=2)
        self.us_holidays = holidays.US()
        
        # Cache for expensive queries
        self.query_cache = {}
        self.cache_ttl = 60  # seconds
        
    @feature_extraction_duration.time()
    async def extract_features(self, timestamp: datetime) -> ScalingFeatures:
        """Extract features for a given timestamp"""
        try:
            # Run queries in parallel for efficiency
            tasks = [
                self._extract_time_features(timestamp),
                self._extract_task_rates(timestamp),
                self._extract_queue_metrics(timestamp),
                self._extract_agent_metrics(timestamp),
                self._extract_complexity_metrics(timestamp),
                self._extract_system_metrics(timestamp),
                self._extract_external_metrics(timestamp)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Combine results
            features = ScalingFeatures(
                # Time features
                **results[0],
                # Task rates
                **results[1],
                # Queue metrics
                **results[2],
                # Agent metrics
                **results[3],
                # Complexity metrics
                **results[4],
                # System metrics
                **results[5],
                # External metrics
                **results[6],
                # Derived features (calculated from above)
                task_acceleration=self._calculate_acceleration(results[1]),
                utilization_pressure=self._calculate_pressure(results[3]),
                cost_efficiency=self._calculate_cost_efficiency(results[1], results[3]),
                queue_pressure=self._calculate_queue_pressure(results[2], results[3])
            )
            
            # Update quality metrics
            self._update_quality_metrics(features)
            
            return features
            
        except Exception as e:
            feature_extraction_errors.inc()
            logger.error("Feature extraction failed", error=str(e), timestamp=timestamp)
            raise
    
    async def _extract_time_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract time-based features"""
        return {
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'day_of_month': timestamp.day,
            'is_weekend': timestamp.weekday() >= 5,
            'is_holiday': timestamp.date() in self.us_holidays,
            'minutes_since_midnight': timestamp.hour * 60 + timestamp.minute
        }
    
    async def _extract_task_rates(self, timestamp: datetime) -> Dict[str, float]:
        """Extract task submission rates"""
        rates = {}
        
        for window, key in [(1, 'task_rate_1m'), (5, 'task_rate_5m'), 
                           (15, 'task_rate_15m'), (60, 'task_rate_1h')]:
            query = f'rate(agent_tasks_submitted_total[{window}m])'
            result = await self._query_prometheus(query, timestamp)
            rates[key] = self._sum_metric_values(result)
        
        return rates
    
    async def _extract_queue_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract queue-related metrics"""
        # Queue depth by priority
        queue_query = 'task_queue_depth'
        queue_result = await self._query_prometheus(queue_query, timestamp)
        queue_by_priority = self._group_by_label(queue_result, 'priority')
        
        # Average queue time
        queue_time_query = 'avg(task_queue_duration_seconds)'
        queue_time_result = await self._query_prometheus(queue_time_query, timestamp)
        avg_queue_time = self._get_single_value(queue_time_result, default=0)
        
        # Queue growth rate
        growth_query = 'deriv(task_queue_depth[5m])'
        growth_result = await self._query_prometheus(growth_query, timestamp)
        queue_growth_rate = self._sum_metric_values(growth_result)
        
        # Max queue depth
        max_depth_query = 'max(task_queue_depth)'
        max_depth_result = await self._query_prometheus(max_depth_query, timestamp)
        max_queue_depth = int(self._get_single_value(max_depth_result, default=0))
        
        return {
            'queue_depth_by_priority': queue_by_priority,
            'avg_queue_time': avg_queue_time,
            'queue_growth_rate': queue_growth_rate,
            'max_queue_depth': max_queue_depth
        }
    
    async def _extract_agent_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract agent-related metrics"""
        # Utilization by type
        util_query = 'agent_utilization_ratio'
        util_result = await self._query_prometheus(util_query, timestamp)
        utilization_by_type = self._group_by_label(util_result, 'agent_type')
        
        # Active agents by type
        count_query = 'agent_pool_size'
        count_result = await self._query_prometheus(count_query, timestamp)
        active_agents_by_type = {k: int(v) for k, v in 
                                self._group_by_label(count_result, 'agent_type').items()}
        
        # Average task duration by type
        duration_query = 'avg by (agent_type) (agent_task_duration_seconds)'
        duration_result = await self._query_prometheus(duration_query, timestamp)
        avg_duration_by_type = self._group_by_label(duration_result, 'agent_type')
        
        return {
            'agent_utilization_by_type': utilization_by_type,
            'active_agents_by_type': active_agents_by_type,
            'avg_task_duration_by_type': avg_duration_by_type
        }
    
    async def _extract_complexity_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract task complexity metrics"""
        # Get task complexity distribution from last hour
        complexity_dist = {
            'simple': 0.5,    # Default distribution
            'moderate': 0.3,
            'complex': 0.15,
            'heavy': 0.05
        }
        
        # Query actual distribution if available
        complexity_query = '''
            sum by (complexity) (
                increase(agent_tasks_submitted_total[1h])
            ) / ignoring(complexity) group_left
            sum(increase(agent_tasks_submitted_total[1h]))
        '''
        
        try:
            result = await self._query_prometheus(complexity_query, timestamp)
            if result:
                complexity_dist = self._group_by_label(result, 'complexity')
        except:
            pass  # Use defaults
        
        # Dependency ratio
        dep_query = '''
            sum(rate(agent_tasks_submitted_total{has_dependencies="true"}[5m])) /
            sum(rate(agent_tasks_submitted_total[5m]))
        '''
        dep_result = await self._query_prometheus(dep_query, timestamp)
        dependency_ratio = self._get_single_value(dep_result, default=0.2)
        
        # Average complexity
        avg_complexity = sum(
            {'simple': 0.5, 'moderate': 1.0, 'complex': 2.0, 'heavy': 5.0}.get(k, 1) * v
            for k, v in complexity_dist.items()
        )
        
        return {
            'complexity_distribution': complexity_dist,
            'dependency_ratio': dependency_ratio,
            'avg_task_complexity': avg_complexity
        }
    
    async def _extract_system_metrics(self, timestamp: datetime) -> Dict[str, float]:
        """Extract system-level metrics"""
        # CPU usage
        cpu_query = 'avg(100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))'
        cpu_result = await self._query_prometheus(cpu_query, timestamp)
        cpu_usage = self._get_single_value(cpu_result, default=0) / 100.0
        
        # Memory usage
        mem_query = '''
            1 - (
                sum(node_memory_MemAvailable_bytes) /
                sum(node_memory_MemTotal_bytes)
            )
        '''
        mem_result = await self._query_prometheus(mem_query, timestamp)
        memory_usage = self._get_single_value(mem_result, default=0)
        
        # Network throughput (MB/s)
        net_query = 'sum(rate(node_network_receive_bytes_total[5m])) + sum(rate(node_network_transmit_bytes_total[5m]))'
        net_result = await self._query_prometheus(net_query, timestamp)
        network_throughput = self._get_single_value(net_result, default=0) / (1024 * 1024)
        
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'network_throughput': network_throughput
        }
    
    async def _extract_external_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract external system metrics"""
        # API request rate
        api_query = 'sum(rate(http_requests_total[5m]))'
        api_result = await self._query_prometheus(api_query, timestamp)
        api_request_rate = self._get_single_value(api_result, default=0)
        
        # Active user sessions
        session_query = 'sum(user_sessions_active)'
        session_result = await self._query_prometheus(session_query, timestamp)
        user_sessions_active = int(self._get_single_value(session_result, default=0))
        
        # Concurrent deployments
        deploy_query = 'count(deployment_in_progress == 1)'
        deploy_result = await self._query_prometheus(deploy_query, timestamp)
        concurrent_deployments = int(self._get_single_value(deploy_result, default=0))
        
        return {
            'api_request_rate': api_request_rate,
            'user_sessions_active': user_sessions_active,
            'concurrent_deployments': concurrent_deployments
        }
    
    async def _query_prometheus(self, query: str, timestamp: datetime) -> List[Dict]:
        """Execute Prometheus query with caching"""
        cache_key = f"{query}:{timestamp.isoformat()}"
        
        # Check cache
        if cache_key in self.query_cache:
            cached_time, result = self.query_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl:
                return result
        
        # Execute query
        result = self.prom.custom_query(query=query, params={'time': timestamp.isoformat()})
        
        # Cache result
        self.query_cache[cache_key] = (datetime.utcnow(), result)
        
        # Clean old cache entries
        if len(self.query_cache) > 1000:
            self._clean_cache()
        
        return result
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, (cached_time, _) in self.query_cache.items():
            if (current_time - cached_time).total_seconds() > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.query_cache[key]
    
    def _group_by_label(self, result: List[Dict], label: str) -> Dict[str, float]:
        """Group Prometheus result by label"""
        grouped = defaultdict(float)
        
        for item in result:
            if 'metric' in item and label in item['metric']:
                label_value = item['metric'][label]
                value = float(item['value'][1]) if 'value' in item else 0
                grouped[label_value] += value
        
        return dict(grouped)
    
    def _get_single_value(self, result: List[Dict], default: float = 0) -> float:
        """Extract single value from Prometheus result"""
        if result and len(result) > 0 and 'value' in result[0]:
            return float(result[0]['value'][1])
        return default
    
    def _sum_metric_values(self, result: List[Dict]) -> float:
        """Sum all values in Prometheus result"""
        total = 0
        for item in result:
            if 'value' in item:
                total += float(item['value'][1])
        return total
    
    def _calculate_acceleration(self, task_rates: Dict[str, float]) -> float:
        """Calculate task submission acceleration"""
        # Simple linear regression on log scale
        rates = [
            task_rates.get('task_rate_1m', 0),
            task_rates.get('task_rate_5m', 0),
            task_rates.get('task_rate_15m', 0),
            task_rates.get('task_rate_1h', 0)
        ]
        
        if all(r == 0 for r in rates):
            return 0
        
        # Calculate rate of change
        x = np.log([1, 5, 15, 60])
        y = np.log1p(rates)
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return float(slope)
        
        return 0
    
    def _calculate_pressure(self, agent_metrics: Dict[str, Any]) -> float:
        """Calculate overall utilization pressure"""
        utilization_values = list(agent_metrics.get('agent_utilization_by_type', {}).values())
        
        if not utilization_values:
            return 0
        
        # Weighted average with penalty for high utilization
        pressure = 0
        for util in utilization_values:
            if util > 0.9:
                pressure += util * 2  # Double weight for critical utilization
            elif util > 0.7:
                pressure += util * 1.5
            else:
                pressure += util
        
        return pressure / len(utilization_values)
    
    def _calculate_cost_efficiency(self, 
                                  task_rates: Dict[str, float],
                                  agent_metrics: Dict[str, Any]) -> float:
        """Calculate tasks processed per dollar"""
        task_rate = task_rates.get('task_rate_5m', 0) * 60  # Tasks per hour
        
        # Calculate total cost
        total_cost = 0
        cost_map = {
            'planner': 10.0,
            'code_generator': 15.0,
            'tester': 12.0,
            'reviewer': 8.0,
            'doc_generator': 5.0
        }
        
        for agent_type, count in agent_metrics.get('active_agents_by_type', {}).items():
            total_cost += count * cost_map.get(agent_type, 10.0)
        
        if total_cost == 0:
            return 0
        
        return task_rate / total_cost
    
    def _calculate_queue_pressure(self,
                                 queue_metrics: Dict[str, Any],
                                 agent_metrics: Dict[str, Any]) -> float:
        """Calculate queue pressure relative to processing capacity"""
        total_queue = sum(queue_metrics.get('queue_depth_by_priority', {}).values())
        
        # Estimate processing capacity
        total_capacity = 0
        for agent_type, count in agent_metrics.get('active_agents_by_type', {}).items():
            avg_duration = agent_metrics.get('avg_task_duration_by_type', {}).get(agent_type, 60)
            if avg_duration > 0:
                capacity_per_agent = 3600 / avg_duration  # Tasks per hour
                total_capacity += count * capacity_per_agent
        
        if total_capacity == 0:
            return 1.0 if total_queue > 0 else 0
        
        # Normalize to [0, 1] with sigmoid
        pressure = total_queue / (total_capacity / 12)  # 5-minute capacity
        return 2 / (1 + np.exp(-pressure)) - 1
    
    def _update_quality_metrics(self, features: ScalingFeatures):
        """Update Prometheus metrics for feature quality monitoring"""
        # Check for data quality issues
        quality_scores = {
            'task_rates': 1.0 if features.task_rate_5m > 0 else 0,
            'agent_metrics': 1.0 if len(features.active_agents_by_type) > 0 else 0,
            'queue_metrics': 1.0 if features.max_queue_depth >= 0 else 0,
            'system_metrics': 1.0 if 0 <= features.cpu_usage <= 1 else 0
        }
        
        for feature_type, score in quality_scores.items():
            feature_quality_score.labels(feature_type=feature_type).set(score)