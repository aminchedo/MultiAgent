"""
Feedback API Routes for Multi-Agent Code Generation System
Collects real user feedback for system improvement and monitoring
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# Feedback data models
class FeedbackRequest(BaseModel):
    """User feedback submission model"""
    project_id: str = Field(..., description="ID of the generated project")
    user_rating: int = Field(..., ge=1, le=5, description="Overall rating (1-5 stars)")
    vibe_alignment_score: int = Field(..., ge=1, le=10, description="How well the output matched the intended vibe (1-10)")
    code_quality_score: int = Field(..., ge=1, le=10, description="Quality of generated code (1-10)")
    usability_score: int = Field(..., ge=1, le=10, description="How usable/practical is the output (1-10)")
    comments: Optional[str] = Field(None, max_length=2000, description="Additional comments")
    generated_files_count: Optional[int] = Field(None, ge=0, description="Number of files in the generated project")
    user_session_id: Optional[str] = Field(None, description="Anonymous user session identifier")
    completion_time_seconds: Optional[float] = Field(None, ge=0, description="Time taken to complete the project")
    
    @validator('comments')
    def validate_comments(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v

class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    feedback_id: str
    status: str
    message: str
    timestamp: datetime

class FeedbackMetrics(BaseModel):
    """Aggregated feedback metrics"""
    total_submissions: int
    average_rating: float
    average_vibe_alignment: float
    average_code_quality: float
    average_usability: float
    ratings_distribution: Dict[int, int]
    recent_feedback_count: int
    satisfaction_rate: float  # Percentage of ratings >= 4

class FeedbackAnalytics(BaseModel):
    """Detailed feedback analytics"""
    metrics: FeedbackMetrics
    trends: Dict[str, Any]
    top_issues: List[str]
    improvement_suggestions: List[str]

# In-memory storage for demonstration (replace with database in production)
feedback_storage: List[Dict[str, Any]] = []

# Create router
router = APIRouter(prefix="/api/feedback", tags=["feedback"])

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback for a generated project"""
    try:
        # Generate unique feedback ID
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Store feedback (in production, save to database)
        feedback_record = {
            "feedback_id": feedback_id,
            "project_id": feedback.project_id,
            "user_rating": feedback.user_rating,
            "vibe_alignment_score": feedback.vibe_alignment_score,
            "code_quality_score": feedback.code_quality_score,
            "usability_score": feedback.usability_score,
            "comments": feedback.comments,
            "generated_files_count": feedback.generated_files_count,
            "user_session_id": feedback.user_session_id,
            "completion_time_seconds": feedback.completion_time_seconds,
            "timestamp": timestamp.isoformat(),
            "ip_address": "anonymized",  # Would get from request in production
        }
        
        feedback_storage.append(feedback_record)
        
        # Log feedback submission
        logger.info(
            f"Feedback submitted",
            extra={
                "feedback_id": feedback_id,
                "project_id": feedback.project_id,
                "user_rating": feedback.user_rating,
                "vibe_alignment": feedback.vibe_alignment_score
            }
        )
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success",
            message="Feedback submitted successfully",
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/metrics", response_model=FeedbackMetrics)
async def get_feedback_metrics():
    """Get aggregated feedback metrics"""
    try:
        if not feedback_storage:
            return FeedbackMetrics(
                total_submissions=0,
                average_rating=0.0,
                average_vibe_alignment=0.0,
                average_code_quality=0.0,
                average_usability=0.0,
                ratings_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                recent_feedback_count=0,
                satisfaction_rate=0.0
            )
        
        # Calculate real metrics from stored feedback
        total_count = len(feedback_storage)
        
        # Calculate averages
        avg_rating = sum(f["user_rating"] for f in feedback_storage) / total_count
        avg_vibe = sum(f["vibe_alignment_score"] for f in feedback_storage) / total_count
        avg_quality = sum(f["code_quality_score"] for f in feedback_storage) / total_count
        avg_usability = sum(f["usability_score"] for f in feedback_storage) / total_count
        
        # Calculate ratings distribution
        ratings_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for feedback in feedback_storage:
            rating = feedback["user_rating"]
            ratings_dist[rating] += 1
        
        # Calculate satisfaction rate (ratings >= 4)
        satisfied_count = sum(1 for f in feedback_storage if f["user_rating"] >= 4)
        satisfaction_rate = (satisfied_count / total_count) * 100 if total_count > 0 else 0
        
        # Recent feedback (last 24 hours)
        from datetime import timedelta
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_count = sum(
            1 for f in feedback_storage 
            if datetime.fromisoformat(f["timestamp"]) > recent_cutoff
        )
        
        return FeedbackMetrics(
            total_submissions=total_count,
            average_rating=round(avg_rating, 2),
            average_vibe_alignment=round(avg_vibe, 2),
            average_code_quality=round(avg_quality, 2),
            average_usability=round(avg_usability, 2),
            ratings_distribution=ratings_dist,
            recent_feedback_count=recent_count,
            satisfaction_rate=round(satisfaction_rate, 2)
        )
        
    except Exception as e:
        logger.error(f"Failed to get feedback metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback metrics")

@router.get("/analytics", response_model=FeedbackAnalytics)
async def get_feedback_analytics():
    """Get detailed feedback analytics and insights"""
    try:
        metrics = await get_feedback_metrics()
        
        if not feedback_storage:
            return FeedbackAnalytics(
                metrics=metrics,
                trends={},
                top_issues=[],
                improvement_suggestions=[]
            )
        
        # Analyze trends (simplified for demonstration)
        trends = {
            "rating_trend": "stable",  # Would calculate actual trend
            "volume_trend": "increasing" if metrics.recent_feedback_count > 0 else "no_data"
        }
        
        # Extract common issues from comments
        top_issues = []
        improvement_suggestions = []
        
        for feedback in feedback_storage:
            if feedback.get("comments"):
                comment = feedback["comments"].lower()
                # Simple keyword analysis (would use NLP in production)
                if any(word in comment for word in ["slow", "performance", "speed"]):
                    top_issues.append("Performance concerns")
                if any(word in comment for word in ["bug", "error", "broken"]):
                    top_issues.append("Code quality issues")
                if any(word in comment for word in ["improve", "better", "enhance"]):
                    improvement_suggestions.append("User suggests enhancements")
        
        # Remove duplicates and limit results
        top_issues = list(set(top_issues))[:5]
        improvement_suggestions = list(set(improvement_suggestions))[:5]
        
        return FeedbackAnalytics(
            metrics=metrics,
            trends=trends,
            top_issues=top_issues,
            improvement_suggestions=improvement_suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to get feedback analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback analytics")

@router.get("/recent")
async def get_recent_feedback(limit: int = Query(10, ge=1, le=100)):
    """Get recent feedback submissions (anonymized)"""
    try:
        # Return recent feedback without sensitive information
        recent_feedback = sorted(
            feedback_storage,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
        # Anonymize the data
        anonymized_feedback = []
        for feedback in recent_feedback:
            anonymized_feedback.append({
                "feedback_id": feedback["feedback_id"],
                "user_rating": feedback["user_rating"],
                "vibe_alignment_score": feedback["vibe_alignment_score"],
                "code_quality_score": feedback["code_quality_score"],
                "usability_score": feedback["usability_score"],
                "timestamp": feedback["timestamp"],
                "has_comments": bool(feedback.get("comments"))
            })
        
        return {
            "recent_feedback": anonymized_feedback,
            "total_count": len(feedback_storage)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent feedback")

@router.get("/health")
async def feedback_health_check():
    """Health check for feedback system"""
    try:
        return {
            "status": "healthy",
            "feedback_system": "operational",
            "total_feedback_collected": len(feedback_storage),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Feedback health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Feedback system health check failed")