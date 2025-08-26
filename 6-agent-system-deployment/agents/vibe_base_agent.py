"""
Vibe Base Agent Class

Simplified base class for vibe agents with SQLite integration and metrics tracking.
This class provides the foundation for all vibe agents in the platform.
"""

import sqlite3
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class VibeBaseAgent(ABC):
    """Base class for all vibe agents with SQLite integration."""
    
    def __init__(self, agent_name: str = None):
        self.agent_name = agent_name or self.__class__.__name__
        self.db_path = "backend/vibe_projects.db"
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create vibe_projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vibe_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vibe_prompt TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    project_files TEXT,
                    error_message TEXT
                )
            """)
            
            # Create agent_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    response_time REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_details TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized successfully at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Don't raise here to allow agent creation in environments without database
    
    def record_metrics(self, success: bool, response_time: float, operation_type: str, error_msg: Optional[str] = None):
        """Record agent metrics to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_metrics (agent_name, operation_type, success, response_time, error_details)
                VALUES (?, ?, ?, ?, ?)
            """, (self.agent_name, operation_type, success, response_time, error_msg))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for this agent."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
                    AVG(response_time) as avg_response_time,
                    MAX(timestamp) as last_operation
                FROM agent_metrics 
                WHERE agent_name = ?
            """, (self.agent_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                total, successful, avg_time, last_op = result
                success_rate = (successful / total * 100) if total > 0 else 0
                
                return {
                    "agent_name": self.agent_name,
                    "total_operations": total or 0,
                    "successful_operations": successful or 0,
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(avg_time or 0, 3),
                    "last_operation": last_op
                }
            
            return {
                "agent_name": self.agent_name,
                "total_operations": 0,
                "successful_operations": 0,
                "success_rate": 0,
                "avg_response_time": 0,
                "last_operation": None
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}
    
    def execute_with_metrics(self, operation_type: str, func, *args, **kwargs):
        """Execute a function with automatic metrics recording."""
        start_time = time.time()
        success = False
        error_msg = None
        result = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Operation {operation_type} failed: {e}")
            raise
            
        finally:
            response_time = time.time() - start_time
            self.record_metrics(success, response_time, operation_type, error_msg)
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        pass