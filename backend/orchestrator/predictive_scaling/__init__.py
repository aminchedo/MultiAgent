"""
AI-Powered Predictive Scaling Module

This module implements machine learning-based predictive scaling for the
Agent Orchestrator, providing 15/30/60 minute workload forecasts with
automatic fallback to rule-based scaling.
"""

from .features import FeatureExtractor, ScalingFeatures
from .model import WorkloadPredictor, PredictiveScalingEngine
from .scaler import PredictiveScaler, ScalingDecision, ScalingConstraints

__all__ = [
    'FeatureExtractor',
    'ScalingFeatures', 
    'WorkloadPredictor',
    'PredictiveScalingEngine',
    'PredictiveScaler',
    'ScalingDecision',
    'ScalingConstraints'
]

__version__ = '1.0.0'